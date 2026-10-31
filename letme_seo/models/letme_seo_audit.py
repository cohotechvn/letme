import re
from collections import defaultdict

from lxml import etree

from odoo import api, fields, models

from odoo.addons.website.tools import text_from_html

TITLE_MAX = 60
TITLE_MIN = 15
DESCRIPTION_MIN = 70
DESCRIPTION_MAX = 160

# Fields some models use as their default meta description (see their _default_website_meta).
DEFAULT_DESCRIPTION_FIELDS = ('description_sale', 'subtitle')
# HTML content fields scanned for images and used to write a description.
CONTENT_FIELDS = ('website_description', 'content', 'description', 'teaser')
# Models that look like SEO pages but are not pages of their own.
EXCLUDED_MODELS = {'ir.ui.view', 'website.event.menu'}

ISSUES = [
    ('website_no_domain', 'Website domain not set'),
    ('website_no_search_console', 'Search engine not verified'),
    ('website_no_analytics', 'No analytics'),
    ('website_no_social_image', 'No default social image'),
    ('website_no_address', 'Business address incomplete'),
    ('title_too_long', 'Title too long'),
    ('title_too_short', 'Title too short'),
    ('title_duplicate', 'Duplicate title'),
    ('description_missing', 'Missing meta description'),
    ('description_too_short', 'Meta description too short'),
    ('description_too_long', 'Meta description too long'),
    ('description_duplicate', 'Duplicate meta description'),
    ('h1_missing', 'No H1 heading'),
    ('h1_multiple', 'Several H1 headings'),
    ('image_missing_alt', 'Images without alt text'),
    ('not_indexed', 'Hidden from search engines'),
]
SEVERITIES = [('high', 'High'), ('medium', 'Medium'), ('low', 'Low')]
ISSUE_SEVERITY = {
    'website_no_domain': 'high',
    'website_no_search_console': 'medium',
    'website_no_analytics': 'low',
    'website_no_social_image': 'low',
    'website_no_address': 'medium',
    'title_too_long': 'medium',
    'title_too_short': 'low',
    'title_duplicate': 'medium',
    'description_missing': 'high',
    'description_too_short': 'medium',
    'description_too_long': 'low',
    'description_duplicate': 'medium',
    'h1_missing': 'medium',
    'h1_multiple': 'low',
    'image_missing_alt': 'low',
    'not_indexed': 'low',
}
AUTOFIX_ISSUES = {'description_missing', 'description_too_long', 'title_too_long'}


def _clean_text(text):
    return re.sub(r'\s+', ' ', text or '').strip()


def truncate_words(text, limit):
    """Cut ``text`` to at most ``limit`` characters, on a word boundary."""
    text = _clean_text(text)
    if len(text) <= limit:
        return text
    cut = text[:limit + 1].rsplit(' ', 1)[0].rstrip(' ,;:-–|')
    return cut or text[:limit]


def count_html_issues(html):
    """Return (number of <h1>, number of <img> without an alt attribute) in ``html``."""
    if not html:
        return 0, 0
    try:
        root = etree.fromstring(f'<div>{html}</div>', etree.XMLParser(recover=True))
    except etree.XMLSyntaxError:
        return 0, 0
    if root is None:
        return 0, 0
    h1_count = len(root.xpath('//h1'))
    alt_attrs = ('alt', 't-att-alt', 't-attf-alt')
    missing_alt = sum(1 for img in root.xpath('//img') if not any(attr in img.attrib for attr in alt_attrs))
    return h1_count, missing_alt


class LetmeSeoAuditLine(models.Model):
    """One SEO problem found on one website record. The table is rebuilt on each audit."""
    _name = 'letme.seo.audit.line'
    _description = "SEO Audit Issue"
    _order = 'severity_order, issue, website_id, res_model, record_name'
    _rec_name = 'record_name'

    website_id = fields.Many2one('website', required=True, ondelete='cascade', index=True)
    res_model = fields.Char(string="Model", index=True)
    res_model_name = fields.Char(string="Document Type")
    res_id = fields.Many2oneReference(string="Record ID", model_field='res_model')
    record_name = fields.Char(string="Page")
    url = fields.Char(string="URL")
    issue = fields.Selection(ISSUES, required=True, index=True)
    severity = fields.Selection(SEVERITIES, required=True, index=True)
    severity_order = fields.Integer(compute='_compute_severity_order', store=True)
    message = fields.Char()
    value = fields.Text(string="Current Value")
    length = fields.Integer(aggregator=None)
    can_autofix = fields.Boolean(compute='_compute_can_autofix')

    @api.depends('severity')
    def _compute_severity_order(self):
        order = {'high': 1, 'medium': 2, 'low': 3}
        for line in self:
            line.severity_order = order.get(line.severity, 9)

    @api.depends('issue', 'res_model')
    def _compute_can_autofix(self):
        for line in self:
            line.can_autofix = bool(line.res_model) and line.issue in AUTOFIX_ISSUES

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    @api.model
    def _get_audited_models(self):
        """Published website documents that carry SEO fields and have their own URL."""
        names = []
        for name, model in self.env.registry.items():
            if (
                name in EXCLUDED_MODELS
                or model._abstract
                or model._transient
                or not model._auto
                or 'website_meta_title' not in model._fields
                or 'website_url' not in model._fields
            ):
                continue
            names.append(name)
        # Variants and users share the page of their delegated parent (template, partner).
        return sorted(
            name for name in names
            if not set(self.env.registry[name]._inherits) & set(names)
        )

    @api.model
    def _get_audit_domain(self, model, website):
        domain = []
        if 'website_id' in model._fields:
            domain += ['|', ('website_id', '=', False), ('website_id', '=', website.id)]
        published = model._fields.get('is_published')
        if published and (published.store or published.search):
            domain.append(('is_published', '=', True))
        return domain

    @api.model
    def _audit_website_settings(self, website):
        problems = []
        if not website.domain:
            problems.append(('website_no_domain', self.env._(
                "Set the website domain (https://...) so canonical URLs, hreflang and the sitemap always use it.",
            ), False))
        if not (website.google_search_console or website.letme_google_verification or website.letme_bing_verification):
            problems.append(('website_no_search_console', self.env._(
                "Verify the site in Google Search Console or Bing Webmaster Tools to follow indexing.",
            ), False))
        if not (website.google_analytics_key or website.plausible_shared_key):
            problems.append(('website_no_analytics', self.env._(
                "No Google Analytics or Plausible tracking is set.",
            ), False))
        if not website.social_default_image:
            problems.append(('website_no_social_image', self.env._(
                "No default social share image: links shared on Facebook or Zalo show the logo instead.",
            ), False))
        partner = website.company_id.partner_id.sudo()
        if website.letme_business_type != 'Organization' and not (partner.street and partner.city and website.company_id.phone):
            problems.append(('website_no_address', self.env._(
                "A local business needs a street, a city and a phone number on the company.",
            ), False))
        return [{
            'website_id': website.id,
            'record_name': website.name,
            'url': '/',
            'issue': issue,
            'severity': ISSUE_SEVERITY[issue],
            'message': message,
            'value': value,
        } for issue, message, value in problems]

    @api.model
    def _get_default_description(self, record):
        for field_name in DEFAULT_DESCRIPTION_FIELDS:
            if field_name in record._fields and record[field_name]:
                return _clean_text(record[field_name])
        return ''

    @api.model
    def _get_record_html(self, record):
        if record._name == 'website.page':
            return record.view_id.arch_db or ''
        parts = []
        for field_name in CONTENT_FIELDS:
            field = record._fields.get(field_name)
            if field and field.type == 'html' and record[field_name]:
                parts.append(str(record[field_name]))
        return ''.join(parts)

    @api.model
    def _audit_record(self, record, website):
        """Return the problems of one record as (issue, message, value, length) tuples,
        plus its effective title and description for duplicate checks."""
        problems = []
        name = _clean_text(record.name if 'name' in record._fields else record.display_name)
        title = _clean_text(record.website_meta_title) or f"{name} | {website.name}"
        description = _clean_text(record.website_meta_description) or self._get_default_description(record)

        if len(title) > TITLE_MAX:
            problems.append(('title_too_long', self.env._(
                "Search engines cut titles after about %(max)s characters.", max=TITLE_MAX,
            ), title, len(title)))
        elif len(title) < TITLE_MIN:
            problems.append(('title_too_short', self.env._(
                "A title under %(min)s characters says little about the page.", min=TITLE_MIN,
            ), title, len(title)))

        if not description:
            problems.append(('description_missing', self.env._(
                "Without a description, search engines pick a random sentence of the page.",
            ), False, 0))
        elif len(description) < DESCRIPTION_MIN:
            problems.append(('description_too_short', self.env._(
                "Aim for %(min)s to %(max)s characters.", min=DESCRIPTION_MIN, max=DESCRIPTION_MAX,
            ), description, len(description)))
        elif len(description) > DESCRIPTION_MAX:
            problems.append(('description_too_long', self.env._(
                "Search engines cut descriptions after about %(max)s characters.", max=DESCRIPTION_MAX,
            ), description, len(description)))

        h1_count, missing_alt = count_html_issues(self._get_record_html(record))
        if record._name == 'website.page':
            if h1_count == 0:
                problems.append(('h1_missing', self.env._(
                    "Give the page one main heading (Heading 1).",
                ), False, 0))
            elif h1_count > 1:
                problems.append(('h1_multiple', self.env._(
                    "Keep a single Heading 1 per page and use Heading 2 for sections.",
                ), False, h1_count))
            if 'website_indexed' in record._fields and not record.website_indexed:
                problems.append(('not_indexed', self.env._(
                    "The page is published but asks search engines not to index it.",
                ), False, 0))
        if missing_alt:
            problems.append(('image_missing_alt', self.env._(
                "%(count)s image(s) have no alt text describing them.", count=missing_alt,
            ), False, missing_alt))
        return problems, title, description

    @api.model
    def _audit_website(self, website):
        vals_list = self._audit_website_settings(website)
        seen_titles = defaultdict(list)
        seen_descriptions = defaultdict(list)
        ir_model = self.env['ir.model']
        lang = website.default_lang_id.code
        for model_name in self._get_audited_models():
            Model = self.env[model_name].sudo().with_context(lang=lang, website_id=website.id)
            records = Model.search(self._get_audit_domain(Model, website))
            if 'is_published' in Model._fields:
                # Some models compute is_published without a search method.
                records = records.filtered('is_published')
            if model_name == 'website.page':
                # A generic page copied for this website is not served any more.
                records = records._get_most_specific_pages()
            model_label = ir_model._get(model_name).name
            for record in records:
                base = {
                    'website_id': website.id,
                    'res_model': model_name,
                    'res_model_name': model_label,
                    'res_id': record.id,
                    'record_name': record.display_name,
                    'url': record.website_url,
                }
                problems, title, description = self._audit_record(record, website)
                for issue, message, value, length in problems:
                    vals_list.append({
                        **base,
                        'issue': issue,
                        'severity': ISSUE_SEVERITY[issue],
                        'message': message,
                        'value': value,
                        'length': length,
                    })
                seen_titles[title.lower()].append((base, title))
                if description:
                    seen_descriptions[description.lower()].append((base, description))
        for issue, seen in (('title_duplicate', seen_titles), ('description_duplicate', seen_descriptions)):
            for entries in seen.values():
                if len(entries) < 2:
                    continue
                for base, text in entries:
                    others = ", ".join(other['record_name'] for other, _text in entries if other is not base)
                    vals_list.append({
                        **base,
                        'issue': issue,
                        'severity': ISSUE_SEVERITY[issue],
                        'message': self.env._("Same text as: %(others)s", others=truncate_words(others, 200)),
                        'value': text,
                        'length': len(text),
                    })
        return vals_list

    @api.model
    def _run_audit(self, websites=None):
        websites = websites or self.env['website'].sudo().search([])
        self.sudo().search([('website_id', 'in', websites.ids)]).unlink()
        vals_list = []
        for website in websites:
            vals_list += self._audit_website(website)
        return self.sudo().create(vals_list)

    @api.model
    def _cron_run_audit(self):
        self._run_audit()

    @api.model
    def action_run_audit(self):
        self._run_audit()
        action = self.env['ir.actions.act_window']._for_xml_id('letme_seo.action_letme_seo_audit_line')
        action['target'] = 'main'
        return action

    # ------------------------------------------------------------------
    # Actions on lines
    # ------------------------------------------------------------------

    def _get_record(self):
        self.ensure_one()
        if not self.res_model or self.res_model not in self.env:
            return None
        return self.env[self.res_model].browse(self.res_id).exists()

    def action_open_record(self):
        self.ensure_one()
        record = self._get_record()
        if not record:
            return self.env['website'].browse(self.website_id.id).get_formview_action()
        return record.get_formview_action()

    def action_open_website(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.url or '/',
            'target': 'new',
        }

    @api.model
    def _get_description_source(self, record):
        """Text to build a description from: the default description field, else the
        paragraphs of the content (headings and menus make poor descriptions)."""
        text = self._get_default_description(record)
        if text:
            return text
        html = self._get_record_html(record)
        if not html:
            return ''
        root = etree.fromstring(f'<div>{html}</div>', etree.XMLParser(recover=True))
        if root is None:
            return ''
        paragraphs = [_clean_text(''.join(p.itertext())) for p in root.xpath('//p')]
        text = ' '.join(p for p in paragraphs if p)
        return text or _clean_text(text_from_html(html, collapse_whitespace=True))

    def action_autofix(self):
        """Write a meta title/description from the record's own content where it is missing or too long."""
        fixed = self.env['letme.seo.audit.line']
        for line in self.filtered('can_autofix'):
            record = line._get_record()
            if not record:
                continue
            record = record.with_context(lang=line.website_id.default_lang_id.code)
            if line.issue == 'title_too_long':
                name = record.name if 'name' in record._fields else record.display_name
                record.website_meta_title = truncate_words(name, TITLE_MAX)
                fixed |= line
            else:
                current = _clean_text(record.website_meta_description)
                source = current if line.issue == 'description_too_long' and current else self._get_description_source(record)
                if source:
                    record.website_meta_description = truncate_words(source, DESCRIPTION_MAX - 5)
                    fixed |= line
        if fixed:
            # The duplicate checks depend on every record, so audit the websites again.
            self._run_audit(fixed.website_id)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success' if fixed else 'warning',
                'message': self.env._("%(count)s issue(s) fixed.", count=len(fixed)) if fixed
                else self.env._("Nothing could be filled automatically: the records have no text to use."),
                'next': {'type': 'ir.actions.client', 'tag': 'soft_reload'},
            },
        }
