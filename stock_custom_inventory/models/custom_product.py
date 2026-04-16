from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    storage_temperature = fields.Selection(
        [
            ('ambient', 'Ambient (15-25°C)'),
            ('cool', 'Cool (2-8°C)'),
            ('frozen', 'Frozen (-18°C or below)'),
            ('controlled', 'Controlled Room Temperature'),
        ],
        string='Storage Temperature',
        default='ambient',
        tracking=True,
    )
    
    shelf_life_days = fields.Integer(
        string='Shelf Life (Days)',
        default=0,
        tracking=True,
    )
    
    minimum_stock_level = fields.Float(
        string='Minimum Stock Level',
        default=10.0,
    )
    
    maximum_stock_level = fields.Float(
        string='Maximum Stock Level',
    )
    
    warehouse_notes = fields.Text(
        string='Warehouse Notes',
    )


class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    # Related fields to template (so they work on variants too)
    storage_temperature = fields.Selection(related='product_tmpl_id.storage_temperature', store=True)
    shelf_life_days = fields.Integer(related='product_tmpl_id.shelf_life_days', store=True)
    minimum_stock_level = fields.Float(related='product_tmpl_id.minimum_stock_level', store=True)
    maximum_stock_level = fields.Float(related='product_tmpl_id.maximum_stock_level', store=True)
    warehouse_notes = fields.Text(related='product_tmpl_id.warehouse_notes')