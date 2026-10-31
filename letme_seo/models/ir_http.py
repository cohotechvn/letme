import logging

from odoo import api, models
from odoo.http import request

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @api.model
    def _get_error_html(self, code, values):
        if code in (404, 'page_404'):
            self._letme_log_not_found()
        return super()._get_error_html(code, values)

    @api.model
    def _letme_log_not_found(self):
        """Record the 404 in its own transaction; never break the error page."""
        if not request or not getattr(request, 'is_frontend', False):
            return
        website = request.env.website
        if not website:
            return
        httprequest = request.httprequest
        if httprequest.method not in ('GET', 'HEAD'):
            return
        try:
            with self.env.registry.cursor() as cr:
                env = self.env(cr=cr, su=True)
                env['letme.seo.not.found']._log_hit(
                    website.id,
                    httprequest.path,
                    referrer=httprequest.referrer,
                    user_agent=httprequest.user_agent.string,
                )
        except Exception:
            _logger.warning("Could not log 404 for %s", httprequest.path, exc_info=True)
