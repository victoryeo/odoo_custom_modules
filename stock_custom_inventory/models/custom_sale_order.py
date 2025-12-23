from odoo import models, fields, api

class SaleOrderCustom(models.Model):
    """Extend sale.order for inventory customizations"""
    _inherit = 'sale.order'
    
    # Add inventory-related fields to sales
    warehouse_notes = fields.Text(
        string='Warehouse Notes',
        help='Special instructions for warehouse'
    )
    
    def action_confirm(self):
        """Custom sales confirmation affecting inventory"""
        # Set priority on created pickings
        ctx = self._context.copy()
        ctx.update({
            'default_priority': 'urgent' if self.require_urgent else '1',
            'skip_sms': True,
        })
        
        return super(SaleOrderCustom, self.with_context(ctx)).action_confirm()