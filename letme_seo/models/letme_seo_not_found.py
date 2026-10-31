import fnmatch
import logging
from datetime import timedelta

from odoo import api, fields, models
from odoo.tools import SQL

_logger = logging.getLogger(__name__)

# Paths that are never worth a redirect: technical routes and vulnerability scanners.
DEFAULT_IGNORE_PATTERNS = """/web/*
/web
/static/*
/*/static/*
/website/static/*
/longpolling/*
/websocket*
/odoo/*
/@/*
*.php
*.asp
*.aspx
*.env
*.git*
*.sql
*.bak
*/wp-*
/wp-*
/cgi-bin/*
/.well-known/*
"""
MAX_PATH_LENGTH = 1024
RETENTION_DAYS = 90


class LetmeSeoNotFound(models.Model):
    """One row per URL that answered 404 on a website, with its hit count.

    Rows are written by ``ir.http`` in their own cursor so the visitor's
    request is never slowed down or broken by the log.
    """
    _name = 'letme.seo.not.found'
    _description = "404 Not Found URL"
    _order = 'state, hits desc, last_seen desc'
    _rec_name = 'path'

    website_id = fields.Many2one('website', required=True, ondelete='cascade', index=True)
    path = fields.Char(required=True, index=True, readonly=True)
    hits = fields.Integer(default=1, readonly=True)
    first_seen = fields.Datetime(default=fields.Datetime.now, readonly=True)
    last_seen = fields.Datetime(default=fields.Datetime.now, readonly=True, index=True)
    last_referrer = fields.Char(readonly=True, help="Page that linked to this URL the last time it was hit.")
    last_user_agent = fields.Char(readonly=True)
    ignored = fields.Boolean(help="Hide this URL from the list without creating a redirect.")
    redirect_id = fields.Many2one(
        'website.rewrite', compute='_compute_redirect_id',
        string="Redirect",
    )
    state = fields.Selection(
        [('open', 'To Fix'), ('redirected', 'Redirected'), ('ignored', 'Ignored')],
        compute='_compute_state', store=True, index=True,
    )
    has_redirect = fields.Boolean(readonly=True, help="Set when a redirect from this URL exists.")

    _website_path_uniq = models.Constraint(
        'UNIQUE(website_id, path)',
        "This URL is already logged for this website.",
    )

    def _get_rewrites(self):
        """Active 301/302/308 redirects matching the logged paths, by (website, path)."""
        paths = set(self.mapped('path'))
        if not paths:
            return {}
        rewrites = self.env['website.rewrite'].sudo().search([
            ('url_from', 'in', _path_variants(paths)),
            ('redirect_type', 'in', ('301', '302', '308')),
        ])
        result = {}
        for record in self:
            for rewrite in rewrites:
                if rewrite.url_from.rstrip('/') == record.path.rstrip('/') and (
                    not rewrite.website_id or rewrite.website_id == record.website_id
                ):
                    result[record.id] = rewrite
                    break
        return result

    def _compute_redirect_id(self):
        rewrites = self._get_rewrites()
        for record in self:
            record.redirect_id = rewrites.get(record.id, False)

    @api.depends('ignored', 'has_redirect')
    def _compute_state(self):
        for record in self:
            if record.has_redirect:
                record.state = 'redirected'
            elif record.ignored:
                record.state = 'ignored'
            else:
                record.state = 'open'

    def _sync_has_redirect(self):
        """Refresh ``has_redirect`` (and so ``state``) from the redirects."""
        rewrites = self._get_rewrites()
        for record in self:
            has_redirect = record.id in rewrites
            if record.has_redirect != has_redirect:
                record.has_redirect = has_redirect

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    @api.model
    def _get_ignore_patterns(self):
        text = self.env['ir.config_parameter'].sudo().get_str(
            'letme_seo.not_found_ignore_patterns', DEFAULT_IGNORE_PATTERNS,
        )
        return [line.strip() for line in text.splitlines() if line.strip()]

    @api.model
    def _is_ignored_path(self, path):
        lowered = path.lower()
        return any(fnmatch.fnmatchcase(lowered, pattern.lower()) for pattern in self._get_ignore_patterns())

    @api.model
    def _log_hit(self, website_id, path, referrer=None, user_agent=None):
        """Insert or increment the row of ``path``. Safe under concurrent hits."""
        if not website_id or not path or len(path) > MAX_PATH_LENGTH or self._is_ignored_path(path):
            return False
        now = fields.Datetime.now()
        self.env.cr.execute(SQL(
            """
            INSERT INTO letme_seo_not_found
                (website_id, path, hits, first_seen, last_seen, last_referrer, last_user_agent,
                 ignored, has_redirect, state, create_uid, create_date, write_uid, write_date)
            VALUES (%(website)s, %(path)s, 1, %(now)s, %(now)s, %(referrer)s, %(agent)s,
                    FALSE, FALSE, 'open', %(uid)s, %(now)s, %(uid)s, %(now)s)
            ON CONFLICT (website_id, path) DO UPDATE SET
                hits = letme_seo_not_found.hits + 1,
                last_seen = EXCLUDED.last_seen,
                last_referrer = COALESCE(EXCLUDED.last_referrer, letme_seo_not_found.last_referrer),
                last_user_agent = EXCLUDED.last_user_agent,
                write_date = EXCLUDED.write_date
            """,
            website=website_id,
            path=path,
            now=now,
            referrer=(referrer or None) and referrer[:MAX_PATH_LENGTH],
            agent=(user_agent or None) and user_agent[:255],
            uid=self.env.uid,
        ))
        return True

    @api.autovacuum
    def _gc_old_not_found(self):
        """Forget URLs nobody asked for in the last 90 days."""
        limit_date = fields.Datetime.now() - timedelta(days=RETENTION_DAYS)
        self.search([('last_seen', '<', limit_date)]).unlink()

    @api.model
    def _cron_sync_redirects(self):
        self.search([('state', '!=', 'ignored')])._sync_has_redirect()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_create_redirect(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._("Create Redirect"),
            'res_model': 'website.rewrite',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': self.env._("404: %(path)s", path=self.path),
                'default_url_from': self.path,
                'default_website_id': self.website_id.id,
                'default_redirect_type': '301',
            },
        }

    def action_open_redirect(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'website.rewrite',
            'view_mode': 'form',
            'res_id': self.redirect_id.id,
        }

    def action_ignore(self):
        self.ignored = True

    def action_reopen(self):
        self.ignored = False

    def action_refresh_redirects(self):
        self._sync_has_redirect()


def _path_variants(paths):
    """``/a`` and ``/a/`` are the same page for a redirect."""
    paths = {p for p in paths if p}
    return list(paths | {p.rstrip('/') or '/' for p in paths} | {p.rstrip('/') + '/' for p in paths})


class WebsiteRewrite(models.Model):
    _inherit = 'website.rewrite'

    @api.model_create_multi
    def create(self, vals_list):
        rewrites = super().create(vals_list)
        self.env['letme.seo.not.found'].sudo().search([
            ('path', 'in', _path_variants(rewrites.mapped('url_from'))),
        ])._sync_has_redirect()
        return rewrites

    def write(self, vals):
        old_paths = self.mapped('url_from')
        result = super().write(vals)
        if {'url_from', 'redirect_type', 'active', 'website_id'} & set(vals):
            self.env['letme.seo.not.found'].sudo().search([
                ('path', 'in', _path_variants(old_paths + self.mapped('url_from'))),
            ])._sync_has_redirect()
        return result

    def unlink(self):
        paths = _path_variants(self.mapped('url_from'))
        result = super().unlink()
        self.env['letme.seo.not.found'].sudo().search([('path', 'in', paths)])._sync_has_redirect()
        return result
