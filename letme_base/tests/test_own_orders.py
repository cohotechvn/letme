from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestOwnOrders(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.seller = new_test_user(cls.env, 'letme_seller', groups='letme_base.group_role_sales')
        cls.other = new_test_user(cls.env, 'letme_other', groups='sales_team.group_sale_salesman_all_leads')
        cls.warehouse = new_test_user(cls.env, 'letme_wh', groups='letme_base.group_role_warehouse')
        partner = cls.env['res.partner'].create({'name': 'Khách test'})
        product = cls.env['product.product'].create({'name': 'Ốp lưng', 'type': 'consu', 'list_price': 100000})
        order_vals = {'partner_id': partner.id, 'order_line': [(0, 0, {'product_id': product.id})]}
        cls.own_order = cls.env['sale.order'].create(dict(order_vals, user_id=cls.seller.id))
        cls.other_order = cls.env['sale.order'].create(dict(order_vals, user_id=cls.other.id))

    def test_seller_sees_only_own_orders(self):
        orders = self.env['sale.order'].with_user(self.seller).search([
            ('id', 'in', (self.own_order | self.other_order).ids),
        ])
        self.assertEqual(orders, self.own_order)

    def test_seller_cannot_edit_other_order(self):
        self.own_order.with_user(self.seller).write({'note': 'ok'})
        with self.assertRaises(AccessError):
            self.other_order.with_user(self.seller).write({'note': 'not allowed'})

    def test_warehouse_still_sees_all(self):
        orders = self.env['sale.order'].with_user(self.warehouse).search([
            ('id', 'in', (self.own_order | self.other_order).ids),
        ])
        self.assertEqual(orders, self.own_order | self.other_order)

    def test_seller_can_open_delivery_of_other_order(self):
        self.other_order.action_confirm()
        picking = self.other_order.picking_ids.with_user(self.seller)
        self.assertTrue(picking)
        picking.web_read({'name': {}, 'state': {}, 'origin': {}, 'sale_id': {'fields': {'display_name': {}}}})
