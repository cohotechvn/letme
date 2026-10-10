import calendar
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError

MONTHS = [(str(month), str(month)) for month in range(1, 13)]


class LetmeLockMonthWizard(models.TransientModel):
    """Lock accounting entries up to the end of a chosen month.

    Odoo Community has the lock date fields on the company but no screen to
    set them. This wizard sets them for one month at a time.
    """
    _name = 'letme.lock.month.wizard'
    _description = "Monthly Lock Dates"

    def _default_month_date(self):
        return fields.Date.context_today(self) - relativedelta(months=1)

    company_id = fields.Many2one(
        'res.company', required=True, readonly=True,
        default=lambda self: self.env.company,
    )
    month = fields.Selection(
        MONTHS, required=True,
        default=lambda self: str(self._default_month_date().month),
    )
    year = fields.Integer(
        required=True,
        default=lambda self: self._default_month_date().year,
    )
    lock_date = fields.Date(compute='_compute_lock_date')
    lock_sale = fields.Boolean(string="Lock Sales", default=True)
    lock_purchase = fields.Boolean(string="Lock Purchases", default=True)
    lock_tax = fields.Boolean(string="Lock Tax Return", default=True)
    lock_all = fields.Boolean(
        string="Lock All Entries",
        help="Nobody can post entries up to this date, except with a lock exception.",
    )
    current_sale_lock_date = fields.Date(related='company_id.sale_lock_date')
    current_purchase_lock_date = fields.Date(related='company_id.purchase_lock_date')
    current_tax_lock_date = fields.Date(related='company_id.tax_lock_date')
    current_fiscalyear_lock_date = fields.Date(related='company_id.fiscalyear_lock_date')
    allow_unlock = fields.Boolean(
        string="Move Lock Dates Back",
        help="Needed when the chosen month is before a date that is already locked.",
    )

    @api.depends('month', 'year')
    def _compute_lock_date(self):
        for wizard in self:
            if wizard.month and 1900 <= wizard.year <= 9999:
                month = int(wizard.month)
                wizard.lock_date = date(wizard.year, month, calendar.monthrange(wizard.year, month)[1])
            else:
                wizard.lock_date = False

    def action_apply(self):
        self.ensure_one()
        if not self.lock_date:
            raise UserError(self.env._("Choose a valid month and year."))
        field_flags = {
            'sale_lock_date': self.lock_sale,
            'purchase_lock_date': self.lock_purchase,
            'tax_lock_date': self.lock_tax,
            'fiscalyear_lock_date': self.lock_all,
        }
        values = {name: self.lock_date for name, selected in field_flags.items() if selected}
        if not values:
            raise UserError(self.env._("Select at least one lock."))
        moved_back = [
            name for name in values
            if self.company_id[name] and self.company_id[name] > self.lock_date
        ]
        if moved_back and not self.allow_unlock:
            raise UserError(self.env._(
                "Some lock dates are already after %(date)s. Tick \"Move Lock Dates Back\" "
                "if you really want to reopen that period.",
                date=self.lock_date,
            ))
        self.company_id.write(values)
        self.company_id.message_post(body=self.env._(
            "Lock dates set to %(date)s by %(user)s: %(locks)s",
            date=self.lock_date,
            user=self.env.user.name,
            locks=", ".join(self.company_id._fields[name].string for name in values),
        ))
        return {'type': 'ir.actions.act_window_close'}
