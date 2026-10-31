from odoo import fields, models

BUSINESS_TYPES = [
    ('Organization', 'Organization'),
    ('LocalBusiness', 'Local Business'),
    ('Store', 'Store'),
    ('ElectronicsStore', 'Electronics Store'),
    ('ComputerStore', 'Computer Store'),
    ('MobilePhoneStore', 'Mobile Phone Store'),
    ('HomeAndConstructionBusiness', 'Home and Construction Business'),
    ('AutomotiveBusiness', 'Automotive Business'),
    ('ProfessionalService', 'Professional Service'),
    ('Restaurant', 'Restaurant'),
]

# Schema types that are a LocalBusiness and may carry opening hours and a price range.
LOCAL_BUSINESS_TYPES = {code for code, _label in BUSINESS_TYPES} - {'Organization'}

SOCIAL_FIELDS = [
    'social_facebook',
    'social_youtube',
    'social_instagram',
    'social_tiktok',
    'social_linkedin',
    'social_twitter',
    'social_github',
    'social_discord',
]


class Website(models.Model):
    _inherit = 'website'

    # Search engine verification tags. Odoo only handles Google through an HTML file.
    letme_google_verification = fields.Char(
        string="Google Verification Code",
        help="Content of the google-site-verification meta tag given by Google Search Console.",
    )
    letme_bing_verification = fields.Char(
        string="Bing Verification Code",
        help="Content of the msvalidate.01 meta tag given by Bing Webmaster Tools.",
    )
    letme_yandex_verification = fields.Char(string="Yandex Verification Code")
    letme_facebook_verification = fields.Char(
        string="Facebook Domain Verification Code",
        help="Content of the facebook-domain-verification meta tag (Meta Business Suite).",
    )
    letme_zalo_verification = fields.Char(
        string="Zalo Verification Code",
        help="Content of the zalo-platform-site-verification meta tag.",
    )
    letme_max_image_preview = fields.Boolean(
        string="Large Image Previews",
        default=True,
        help="Let Google show large image previews (robots max-image-preview:large) on indexable pages.",
    )

    # Business details for the Organization / LocalBusiness structured data.
    letme_business_type = fields.Selection(
        BUSINESS_TYPES,
        string="Business Type",
        default='Organization',
        required=True,
        help="Schema.org type of the business shown to search engines on every page.",
    )
    letme_opening_hours = fields.Char(
        string="Opening Hours",
        help="Schema.org format, separated by commas. Example: Mo-Sa 08:00-20:00, Su 08:00-12:00",
    )
    letme_price_range = fields.Char(
        string="Price Range",
        help="Free text such as $$ or 100.000-5.000.000 VND.",
    )

    def _letme_get_verification_tags(self):
        """Return (meta name, content) pairs to add to the <head>."""
        self.ensure_one()
        tags = [
            ('google-site-verification', self.letme_google_verification),
            ('msvalidate.01', self.letme_bing_verification),
            ('yandex-verification', self.letme_yandex_verification),
            ('facebook-domain-verification', self.letme_facebook_verification),
            ('zalo-platform-site-verification', self.letme_zalo_verification),
        ]
        return [(name, content.strip()) for name, content in tags if content and content.strip()]

    def _letme_get_same_as(self):
        company = self.company_id.sudo()
        return [company[name].strip() for name in SOCIAL_FIELDS if company[name] and company[name].strip()]

    def _prepare_jsonld_vals(self):
        vals = super()._prepare_jsonld_vals()
        self.ensure_one()
        company = self.company_id.sudo()
        partner = company.partner_id
        vals['@type'] = self.letme_business_type or 'Organization'
        if company.phone:
            vals['telephone'] = company.phone
        if company.email:
            vals['email'] = company.email
        if address := self._build_postaladdress_jsonld_vals(partner):
            vals['address'] = address
        if company.vat:
            vals['vatID'] = company.vat
        if same_as := self._letme_get_same_as():
            vals['sameAs'] = same_as
        if vals['@type'] in LOCAL_BUSINESS_TYPES:
            # Google requires an image for LocalBusiness rich results.
            vals['image'] = vals['logo']
            if self.letme_opening_hours:
                vals['openingHours'] = [
                    hours.strip() for hours in self.letme_opening_hours.split(',') if hours.strip()
                ]
            if self.letme_price_range:
                vals['priceRange'] = self.letme_price_range
        return vals

    def _letme_prepare_website_jsonld_vals(self):
        """Schema.org WebSite entity: gives search engines the site name."""
        self.ensure_one()
        base_url = self.get_base_url()
        vals = {
            '@type': 'WebSite',
            '@id': f'{base_url}/#website',
            'name': self.name,
            'url': base_url,
            'publisher': {'@id': f'{base_url}/#organization'},
        }
        if self.default_lang_id:
            vals['inLanguage'] = self.default_lang_id.code.replace('_', '-')
        return vals
