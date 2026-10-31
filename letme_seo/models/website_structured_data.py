from odoo import models


class WebsiteStructuredDataMixin(models.AbstractModel):
    _inherit = 'website.structured_data.mixin'

    def _get_jsonld_dict(self, is_detail_page=False):
        schemas = super()._get_jsonld_dict(is_detail_page=is_detail_page)
        website = self.env.website or self.env['website'].browse(self.env.context.get('host_id'))
        if website:
            # Right after the Organization so the graph reads publisher first.
            schemas.insert(1, website._letme_prepare_website_jsonld_vals())
        return schemas
