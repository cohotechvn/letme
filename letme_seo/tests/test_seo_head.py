import json

from lxml import html

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestSeoHead(HttpCase):

    def test_head_tags_and_structured_data(self):
        website = self.env.ref('base.default_website')
        company = website.company_id
        company.write({
            'phone': '0912 345 678',
            'email': 'shop@example.com',
            'street': '1 Lê Lợi',
            'city': 'Huế',
            'social_facebook': 'https://www.facebook.com/cohotech',
            'social_youtube': False,
            'social_twitter': False,
            'social_linkedin': False,
            'social_instagram': False,
            'social_github': False,
            'social_tiktok': False,
            'social_discord': False,
        })
        website.write({
            'letme_business_type': 'ElectronicsStore',
            'letme_opening_hours': 'Mo-Sa 08:00-20:00, Su 08:00-12:00',
            'letme_google_verification': 'google-code',
            'letme_zalo_verification': 'zalo-code',
        })
        response = self.url_open('/')
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        self.assertEqual(tree.xpath("//meta[@name='google-site-verification']/@content"), ['google-code'])
        self.assertEqual(tree.xpath("//meta[@name='zalo-platform-site-verification']/@content"), ['zalo-code'])
        self.assertIn('max-image-preview:large', tree.xpath("//meta[@name='robots']/@content"))

        payload = json.loads(tree.xpath("//script[@type='application/ld+json']/text()")[0])
        by_type = {schema['@type']: schema for schema in payload['@graph']}
        business = by_type['ElectronicsStore']
        self.assertEqual(business['telephone'], '0912 345 678')
        self.assertEqual(business['address']['addressLocality'], 'Huế')
        self.assertEqual(business['sameAs'], ['https://www.facebook.com/cohotech'])
        self.assertEqual(business['openingHours'], ['Mo-Sa 08:00-20:00', 'Su 08:00-12:00'])
        self.assertEqual(by_type['WebSite']['publisher'], {'@id': business['@id']})

    def test_no_tags_by_default(self):
        website = self.env.ref('base.default_website')
        website.letme_max_image_preview = False
        tree = html.fromstring(self.url_open('/').content)
        self.assertFalse(tree.xpath("//meta[@name='msvalidate.01']"))
        self.assertNotIn('max-image-preview:large', tree.xpath("//meta[@name='robots']/@content"))
