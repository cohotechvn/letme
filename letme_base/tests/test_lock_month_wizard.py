from datetime import date

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestLockMonthWizard(TransactionCase):

    def _wizard(self, **vals):
        return self.env['letme.lock.month.wizard'].create(vals)

    def test_lock_month_end(self):
        self._wizard(month='2', year=2028).action_apply()
        company = self.env.company
        self.assertEqual(company.sale_lock_date, date(2028, 2, 29))
        self.assertEqual(company.purchase_lock_date, date(2028, 2, 29))
        self.assertEqual(company.tax_lock_date, date(2028, 2, 29))
        self.assertFalse(company.fiscalyear_lock_date)

    def test_move_back_needs_confirmation(self):
        self._wizard(month='3', year=2028).action_apply()
        with self.assertRaises(UserError):
            self._wizard(month='1', year=2028).action_apply()
        self._wizard(month='1', year=2028, allow_unlock=True).action_apply()
        self.assertEqual(self.env.company.sale_lock_date, date(2028, 1, 31))
