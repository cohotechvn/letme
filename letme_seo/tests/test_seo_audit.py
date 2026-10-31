from odoo.tests import TransactionCase, tagged

from odoo.addons.letme_seo.models.letme_seo_audit import (
    count_html_issues,
    truncate_words,
)

PAGE_ARCH = """<t t-name="letme_seo.%s"><t t-call="website.layout"><div id="wrap">
<h1>Main title</h1><h1>Second title</h1>
<p>Chúng tôi sửa chữa điện thoại, máy tính và thiết bị điện tử tại nhà với giá minh bạch và bảo hành dài hạn cho mọi khách hàng.</p>
<img src="/web/image/a.png"/><img src="/web/image/b.png" alt="Cửa hàng"/>
</div></t></t>"""


@tagged('post_install', '-at_install')
class TestSeoAudit(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].create({'name': 'Letme SEO Test'})
        cls.Line = cls.env['letme.seo.audit.line']

    def _create_page(self, key, **vals):
        return self.env['website.page'].create({
            'name': vals.pop('name', key),
            'url': '/%s' % key,
            'type': 'qweb',
            'key': 'letme_seo.%s' % key,
            'arch': PAGE_ARCH % key,
            'website_id': self.website.id,
            'is_published': True,
            **vals,
        })

    def _lines(self, record):
        return self.Line.search([('res_model', '=', record._name), ('res_id', '=', record.id)])

    def test_helpers(self):
        self.assertEqual(truncate_words('một hai ba bốn', 9), 'một hai')
        self.assertEqual(truncate_words('ngắn', 50), 'ngắn')
        self.assertEqual(count_html_issues('<h1>a</h1><img src="x"/><img alt="" src="y"/>'), (1, 1))
        self.assertEqual(count_html_issues(''), (0, 0))

    def test_page_issues(self):
        page = self._create_page(
            'letme-seo-page',
            name='Dịch vụ sửa chữa điện thoại, máy tính, máy in và thiết bị điện tử tận nơi',
        )
        self.Line._run_audit(self.website)
        issues = set(self._lines(page).mapped('issue'))
        self.assertIn('title_too_long', issues)
        self.assertIn('description_missing', issues)
        self.assertIn('h1_multiple', issues)
        self.assertIn('image_missing_alt', issues)
        self.assertNotIn('h1_missing', issues)
        # Website level checks run too.
        website_issues = self.Line.search([('website_id', '=', self.website.id), ('res_model', '=', False)])
        self.assertIn('website_no_domain', website_issues.mapped('issue'))

    def test_duplicates(self):
        page_a = self._create_page('letme-seo-a', website_meta_description='Mô tả giống nhau ' * 6)
        page_b = self._create_page('letme-seo-b', website_meta_description='Mô tả giống nhau ' * 6)
        self.Line._run_audit(self.website)
        self.assertIn('description_duplicate', self._lines(page_a).mapped('issue'))
        self.assertIn('description_duplicate', self._lines(page_b).mapped('issue'))

    def test_unpublished_not_audited(self):
        page = self._create_page('letme-seo-draft', is_published=False)
        self.Line._run_audit(self.website)
        self.assertFalse(self._lines(page))

    def test_autofix(self):
        page = self._create_page(
            'letme-seo-fix',
            name='Dịch vụ sửa chữa điện thoại, máy tính, máy in và thiết bị điện tử tận nơi',
        )
        self.Line._run_audit(self.website)
        self._lines(page).filtered('can_autofix').action_autofix()
        self.assertTrue(page.website_meta_description.startswith('Chúng tôi sửa chữa điện thoại'))
        self.assertLessEqual(len(page.website_meta_description), 160)
        self.assertLessEqual(len(page.website_meta_title), 60)
        issues = set(self._lines(page).mapped('issue'))
        self.assertFalse(issues & {'description_missing', 'title_too_long'})
