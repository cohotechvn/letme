from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged

from odoo.addons.letme_base.models.res_partner import normalize_vn_phone


@tagged('post_install', '-at_install')
class TestDuplicatePhone(TransactionCase):

    def test_normalize(self):
        self.assertEqual(normalize_vn_phone('+84 912 345 678'), '0912345678')
        self.assertEqual(normalize_vn_phone('84912345678'), '0912345678')
        self.assertEqual(normalize_vn_phone('0912.345.678'), '0912345678')
        self.assertFalse(normalize_vn_phone(''))
        self.assertFalse(normalize_vn_phone('---'))

    def test_duplicate_blocked_in_any_format(self):
        Partner = self.env['res.partner']
        Partner.create({'name': 'Khách A', 'phone': '0912 345 678'})
        with self.assertRaises(ValidationError):
            Partner.create({'name': 'Khách B', 'phone': '+84912345678'})

    def test_same_company_contacts_allowed(self):
        Partner = self.env['res.partner']
        company = Partner.create({'name': 'Công ty X', 'is_company': True, 'phone': '02838123456'})
        contact = Partner.create({'name': 'Anh Y', 'parent_id': company.id, 'phone': '028 3812 3456'})
        self.assertEqual(contact.letme_phone_normalized, '02838123456')

    def test_archived_partner_ignored(self):
        Partner = self.env['res.partner']
        Partner.create({'name': 'Khách cũ', 'phone': '0987654321', 'active': False})
        Partner.create({'name': 'Khách mới', 'phone': '0987654321'})
