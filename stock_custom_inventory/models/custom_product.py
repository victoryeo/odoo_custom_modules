# models/custom_product.py

from odoo import models, fields, api
from odoo.exceptions import UserError

class ProductProductCustom(models.Model):
    """Extend product.product for Odoo 19 - Enhanced Visibility"""
    _inherit = 'product.product'
    
    # ========== STORAGE & SHELF LIFE ==========
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
        help='Required storage temperature conditions'
    )
    
    shelf_life_days = fields.Integer(
        string='Shelf Life (Days)',
        default=0,
        tracking=True,
        help='Number of days until expiration from production date'
    )
    
    shelf_life_status = fields.Selection(
        [
            ('fresh', 'Fresh'),
            ('warning', 'Expiring Soon'),
            ('expired', 'Expired'),
            ('na', 'N/A'),
        ],
        string='Shelf Life Status',
        compute='_compute_shelf_life_status',
        store=False,
        help='Visual indicator of product freshness'
    )
    
    # ========== VISUAL INDICATORS ==========
    color_indicator = fields.Char(
        string='Color Indicator',
        compute='_compute_color_indicator',
        store=False,
        help='Color coding for list views'
    )
    
    storage_summary = fields.Char(
        string='Storage Summary',
        compute='_compute_storage_summary',
        store=True,
        help='Quick summary of storage requirements'
    )
    
    # ========== ADDITIONAL PRACTICAL FIELDS ==========
    reorder_when_low = fields.Boolean(
        string='Reorder When Low',
        default=True,
        help='Automatically create reordering when stock is low'
    )
    
    minimum_stock_level = fields.Float(
        string='Minimum Stock Level',
        default=10.0,
        help='Minimum quantity to maintain in stock'
    )
    
    maximum_stock_level = fields.Float(
        string='Maximum Stock Level',
        help='Maximum quantity to store'
    )
    
    warehouse_notes = fields.Text(
        string='Warehouse Notes',
        help='Special instructions for warehouse handling'
    )
    
    # ========== SMART BUTTONS & COUNTERS ==========
    custom_pickings_count = fields.Integer(
        string='Express Pickings',
        compute='_compute_custom_pickings_count',
        store=False,
        help='Number of express priority pickings for this product'
    )
    
    low_stock_count = fields.Integer(
        string='Low Stock Alerts',
        compute='_compute_low_stock_count',
        store=False,
        help='Count of locations where stock is below minimum'
    )
    
    # ========== COMPUTED METHODS ==========
    @api.depends('shelf_life_days')
    def _compute_shelf_life_status(self):
        """Calculate shelf life status with visual indicators"""
        for product in self:
            if product.shelf_life_days <= 0:
                product.shelf_life_status = 'na'
            else:
                # Add actual expiry logic here using lot/serial dates
                product.shelf_life_status = 'fresh'
    
    @api.depends('storage_temperature', 'shelf_life_days')
    def _compute_storage_summary(self):
        """Create a quick summary text"""
        for product in self:
            if product.shelf_life_days > 0:
                product.storage_summary = f"{product.storage_temperature} | {product.shelf_life_days} days"
            else:
                product.storage_summary = product.storage_temperature or ''
    
    @api.depends('storage_temperature')
    def _compute_color_indicator(self):
        """Color coding for visual identification"""
        for product in self:
            if product.storage_temperature == 'frozen':
                product.color_indicator = 'blue'
            elif product.storage_temperature == 'cool':
                product.color_indicator = 'lightblue'
            elif product.storage_temperature == 'controlled':
                product.color_indicator = 'green'
            else:
                product.color_indicator = 'white'
    
    def _compute_custom_pickings_count(self):
        """Count express pickings for this product"""
        StockPicking = self.env['stock.picking']
        for product in self:
            product.custom_pickings_count = StockPicking.search_count([
                ('move_ids.product_id', '=', product.id),
                ('priority', 'in', ['1', 'urgent'])
            ])
    
    def _compute_low_stock_count(self):
        """Count locations where stock is below minimum"""
        StockQuant = self.env['stock.quant']
        for product in self:
            if product.type != 'product':
                product.low_stock_count = 0
                continue
                
            product.low_stock_count = StockQuant.search_count([
                ('product_id', '=', product.id),
                ('quantity', '<', product.minimum_stock_level),
                ('quantity', '>', 0)
            ])
    
    # ========== ACTION METHODS ==========
    def action_view_custom_pickings(self):
        """Smart button to view express pickings"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Express Pickings - {self.name}',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [
                ('move_ids.product_id', '=', self.id),
                ('priority', 'in', ['1', 'urgent'])
            ],
            'context': {
                'create': False,
                'default_priority': '1',
            },
            'target': 'current',
        }
    
    def action_view_low_stock(self):
        """Smart button to view low stock locations"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Low Stock - {self.name}',
            'res_model': 'stock.quant',
            'view_mode': 'tree,form',
            'domain': [
                ('product_id', '=', self.id),
                ('quantity', '<', self.minimum_stock_level),
                ('quantity', '>', 0)
            ],
            'context': {'search_default_groupby_location': True},
            'target': 'current',
        }
    
    def action_set_minimum_stock(self):
        """Quick action to set minimum stock"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Set Minimum Stock',
            'res_model': 'product.product',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'flags': {'mode': 'edit'},
        }
    
    # ========== BUSINESS LOGIC ==========
    def check_storage_compliance(self, location):
        """Check if product can be stored in given location"""
        self.ensure_one()
        # Example logic
        if self.storage_temperature == 'frozen' and not hasattr(location, 'temperature_controlled'):
            raise UserError(f"{self.name} requires frozen storage but {location.name} doesn't support it")
        return True
    
    def get_storage_requirements(self):
        """Get formatted storage requirements"""
        requirements = []
        if self.storage_temperature:
            requirements.append(f"Storage: {self.storage_temperature}")
        if self.shelf_life_days > 0:
            requirements.append(f"Shelf Life: {self.shelf_life_days} days")
        if self.warehouse_notes:
            requirements.append(f"Notes: {self.warehouse_notes}")
        return " | ".join(requirements)
    
    # ========== CREATE/WRITE METHODS ==========
    @api.model_create_multi
    def create(self, vals_list):
        """Add default values for custom fields - FIXED VERSION"""
        # Ensure vals_list is always a list
        if not isinstance(vals_list, list):
            vals_list = [vals_list]
        
        # Process each dictionary in the list
        processed_vals_list = []
        for vals in vals_list:
            # Skip if vals is not a dictionary (e.g., when called with string/ID)
            if not isinstance(vals, dict):
                processed_vals_list.append(vals)
                continue
                
            # Make a copy to avoid modifying the original
            vals_copy = vals.copy()
            
            # Set defaults only if not already set
            if 'storage_temperature' not in vals_copy:
                vals_copy['storage_temperature'] = 'ambient'
            if 'reorder_when_low' not in vals_copy:
                vals_copy['reorder_when_low'] = True
                
            processed_vals_list.append(vals_copy)
        
        return super().create(processed_vals_list)
    
    def write(self, vals):
        """Add validation when updating"""
        # Check min/max stock levels
        if 'minimum_stock_level' in vals and 'maximum_stock_level' in vals:
            if vals['minimum_stock_level'] > vals['maximum_stock_level']:
                raise UserError("Minimum stock level cannot exceed maximum stock level")
        
        # Also check if updating one when other exists
        for record in self:
            min_val = vals.get('minimum_stock_level', record.minimum_stock_level)
            max_val = vals.get('maximum_stock_level', record.maximum_stock_level)
            if max_val and min_val > max_val:
                raise UserError(f"Minimum stock ({min_val}) cannot exceed maximum ({max_val})")
        
        return super().write(vals)