from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    letme_google_verification = fields.Char(related='website_id.letme_google_verification', readonly=False)
    letme_bing_verification = fields.Char(related='website_id.letme_bing_verification', readonly=False)
    letme_yandex_verification = fields.Char(related='website_id.letme_yandex_verification', readonly=False)
    letme_facebook_verification = fields.Char(related='website_id.letme_facebook_verification', readonly=False)
    letme_zalo_verification = fields.Char(related='website_id.letme_zalo_verification', readonly=False)
    letme_max_image_preview = fields.Boolean(related='website_id.letme_max_image_preview', readonly=False)
    letme_business_type = fields.Selection(related='website_id.letme_business_type', readonly=False)
    letme_opening_hours = fields.Char(related='website_id.letme_opening_hours', readonly=False)
    letme_price_range = fields.Char(related='website_id.letme_price_range', readonly=False)

    def action_letme_seo_audit(self):
        return self.env['letme.seo.audit.line'].action_run_audit()
