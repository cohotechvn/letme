{
    'name': 'COHOTECH SEO',
    'version': '20.0.1.0.0',
    'category': 'Website/Website',
    'summary': 'SEO audit, 404 log with one-click redirects, business schema, verification tags',
    'author': 'COHOTECH',
    'website': 'https://cohotech.vn',
    'license': 'LGPL-3',
    'depends': [
        'website',
    ],
    'data': [
        'security/ir.access.csv',
        'data/ir_cron_data.xml',
        'views/letme_seo_audit_views.xml',
        'views/letme_seo_not_found_views.xml',
        'views/res_config_settings_views.xml',
        'views/website_templates.xml',
    ],
    'installable': True,
    'application': False,
}
