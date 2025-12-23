from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockPickingCustom(models.Model):
    """Customize stock.picking for Odoo 19"""
    _inherit = 'stock.picking'
    
    # Add new priority option
    priority = fields.Selection(
        selection_add=[('urgent', 'Urgent')],
        ondelete={'urgent': 'set default'},
        tracking=True  # Track changes in chatter
    )
    
    # Add custom field
    custom_notes = fields.Text(
        string='Custom Notes',
        help='Internal notes for warehouse team'
    )
    
    @api.model
    def create(self, vals):
        """Custom logic when creating picking"""
        if 'priority' not in vals:
            vals['priority'] = '1'  # Default to normal
        return super().create(vals)
    
    def action_confirm(self):
        """Override confirmation"""
        # Custom validation
        if self.priority == 'urgent' and not self.scheduled_date:
            raise ValidationError("Urgent pickings require scheduled date")
        
        # Call parent with Odoo 19 context
        return super().with_context(
            skip_sms=True,           # Odoo 19: Skip SMS
            default_priority='1',    # Odoo 19: Default
            from_custom_module=True, # Your custom flag
        ).action_confirm()
    
    def button_validate(self):
        """Custom validation logic"""
        # Add pre-validation checks
        self._pre_validation_checks()
        
        # Call parent with context
        return super().with_context(
            skip_sms=True,
            skip_email_notification=True,  # Odoo 19 feature
        ).button_validate()
    
    def _pre_validation_checks(self):
        """Your custom validation logic"""
        if self.priority == 'urgent':
            # Check if urgent requirements are met
            pass