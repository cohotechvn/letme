import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError


def normalize_vn_phone(phone):
    """Return the phone number as local digits (0xxxxxxxxx), or False.

    "+84 912 345 678", "84912345678" and "0912.345.678" all give "0912345678".
    """
    if not phone:
        return False
    digits = re.sub(r'\D', '', phone)
    if digits.startswith('84') and len(digits) >= 11:
        digits = '0' + digits[2:]
    return digits or False


class ResPartner(models.Model):
    _inherit = 'res.partner'

    letme_phone_normalized = fields.Char(
        string="Normalized Phone",
        compute='_compute_letme_phone_normalized',
        store=True,
        index=True,
    )

    @api.depends('phone')
    def _compute_letme_phone_normalized(self):
        for partner in self:
            partner.letme_phone_normalized = normalize_vn_phone(partner.phone)

    @api.constrains('phone', 'parent_id', 'active')
    def _check_letme_duplicate_phone(self):
        for partner in self:
            if not partner.active or not partner.letme_phone_normalized:
                continue
            # Contacts of the same company may share the company phone.
            duplicate = self.sudo().search([
                ('id', '!=', partner.id),
                ('letme_phone_normalized', '=', partner.letme_phone_normalized),
                ('commercial_partner_id', '!=', partner.commercial_partner_id.id),
            ], limit=1)
            if duplicate:
                raise ValidationError(self.env._(
                    "The phone number %(phone)s is already used by %(partner)s. "
                    "Open that contact instead of creating a new one.",
                    phone=partner.phone,
                    partner=duplicate.display_name,
                ))
