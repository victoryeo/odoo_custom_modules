{
    'name': 'Stock Custom Inventory',
    'version': '1.0',
    'category': 'Inventory/Inventory',
    'summary': 'Custom inventory features for Odoo',
    'description': """
    Custom inventory management:
    - Product storage requirements
    - Quality control for stock moves
    - Enhanced picking workflows
    - Custom reporting
    """,
    'author': 'Victor',
    'website': 'https://yourwebsite.com',
    'depends': ['stock', 'sale_stock', 'purchase_stock'],
    'data': [
        #'views/product_views_temp.xml',
        'views/product_views.xml',
        #'views/stock_move_views.xml',
        #'views/stock_picking_views.xml',
        #'security/ir.model.access.csv',
        #'data/demo_data.xml',
    ],
    #'demo': ['data/demo_data.xml'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}