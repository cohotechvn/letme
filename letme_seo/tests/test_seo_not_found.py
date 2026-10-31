from unittest.mock import patch

from odoo.tests import HttpCase, TransactionCase, tagged

from odoo.addons.letme_seo.models.letme_seo_not_found import LetmeSeoNotFound


@tagged('post_install', '-at_install')
class TestSeoNotFoundLog(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env.ref('base.default_website')
        cls.NotFound = cls.env['letme.seo.not.found']

    def _log(self, path):
        return self.NotFound.search([('path', '=', path), ('website_id', '=', self.website.id)])

    def test_hits_counted(self):
        path = '/letme-seo-missing-page'
        self.NotFound._log_hit(self.website.id, path)
        self.NotFound._log_hit(self.website.id, path, referrer='https://example.com/old-link', user_agent='Googlebot')
        log = self._log(path)
        self.assertEqual(log.hits, 2)
        self.assertEqual(log.state, 'open')
        self.assertEqual(log.last_referrer, 'https://example.com/old-link')
        self.assertEqual(log.last_user_agent, 'Googlebot')

    def test_ignored_paths(self):
        for path in ('/wp-login.php', '/web/content/1', '/.env', '/website/static/x.js'):
            self.assertFalse(self.NotFound._log_hit(self.website.id, path), path)
        self.assertFalse(self.NotFound._log_hit(self.website.id, '/x' * 600), "Path too long")
        self.env['ir.config_parameter'].set_str('letme_seo.not_found_ignore_patterns', '/tmp-*')
        self.assertFalse(self.NotFound._log_hit(self.website.id, '/tmp-sale'))
        self.assertTrue(self.NotFound._log_hit(self.website.id, '/wp-login.php'))

    def test_redirect_closes_the_url(self):
        path = '/letme-seo-old-product'
        self.NotFound._log_hit(self.website.id, path)
        log = self._log(path)
        action = log.action_create_redirect()
        self.assertEqual(action['context']['default_url_from'], path)
        rewrite = self.env['website.rewrite'].create({
            'name': 'Moved',
            'url_from': path + '/',
            'url_to': '/contactus',
            'redirect_type': '301',
            'website_id': self.website.id,
        })
        self.assertEqual(log.state, 'redirected')
        self.assertEqual(log.redirect_id, rewrite)
        rewrite.active = False
        self.assertEqual(log.state, 'open')
        rewrite.active = True
        self.assertEqual(log.state, 'redirected')
        rewrite.unlink()
        self.assertEqual(log.state, 'open')

    def test_ignore_and_reopen(self):
        self.NotFound._log_hit(self.website.id, '/letme-seo-old-promo')
        log = self._log('/letme-seo-old-promo')
        log.action_ignore()
        self.assertEqual(log.state, 'ignored')
        log.action_reopen()
        self.assertEqual(log.state, 'open')


@tagged('post_install', '-at_install')
class TestSeoNotFoundRequest(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # 404 pages are served on a read-only cursor and the log opens its own
        # read/write cursor. Test cursors cannot nest that way, real ones can.
        cls.set_registry_readonly_mode(False)

    def test_404_page_logs_the_path(self):
        with patch.object(LetmeSeoNotFound, '_log_hit', autospec=True, return_value=True) as log_hit:
            response = self.url_open('/letme-seo-missing', headers={'Referer': 'https://example.com/a'})
            self.assertEqual(response.status_code, 404)
            self.url_open('/contactus')
        self.assertEqual(log_hit.call_count, 1)
        _self, website_id, path = log_hit.call_args.args
        self.assertEqual(path, '/letme-seo-missing')
        self.assertEqual(log_hit.call_args.kwargs['referrer'], 'https://example.com/a')
        self.assertTrue(website_id)
