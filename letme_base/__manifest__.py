{
    'name': 'COHOTECH Base',
    'version': '20.0.1.0.0',
    'category': 'Hidden',
    'summary': 'COHOTECH roles, own-order restriction, duplicate phone check, monthly lock dates',
    'author': 'COHOTECH',
    'website': 'https://cohotech.vn',
    'license': 'LGPL-3',
    'depends': [
        'sale_stock',
        'point_of_sale',
        'purchase',
        'repair',
        'hr_attendance',
        'hr_holidays',
    ],
    'data': [
        'security/letme_base_groups.xml',
        'security/ir.access.csv',
        'wizard/letme_lock_month_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
}
