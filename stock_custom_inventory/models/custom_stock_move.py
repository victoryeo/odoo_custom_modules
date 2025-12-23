# models/custom_stock_move.py
from odoo import models, fields, api
from odoo.exceptions import ValidationError  # ✅ Added missing import

class StockMoveCustom(models.Model):
    """Extend stock.move for Odoo 19"""
    _inherit = 'stock.move'
    
    # Quality control fields
    quality_check_required = fields.Boolean(
        string='Quality Check Required',
        default=False,
        tracking=True  # ✅ Track changes in chatter
    )
    
    quality_status = fields.Selection(
        selection=[
            ('pending', '⏳ Pending'),
            ('passed', '✅ Passed'),
            ('failed', '❌ Failed'),
            ('quarantine', '🚫 Quarantine'),
        ],
        string='Quality Status',
        default='pending',
        tracking=True,  # ✅ Track changes
        help='Current quality control status'
    )
    
    quality_check_date = fields.Datetime(
        string='Quality Check Date',
        readonly=True,
        help='When the quality check was performed'
    )
    
    quality_check_notes = fields.Text(
        string='Quality Notes',
        help='Notes from quality inspection'
    )
    
    # Odoo 19: Related fields for easy access
    picking_shipping_priority = fields.Selection(
        related='picking_id.priority',
        string='Picking Priority',
        store=True,
        readonly=True
    )
    
    # ✅ Add computed field for visual indicators
    quality_status_color = fields.Char(
        string='Status Color',
        compute='_compute_quality_status_color',
        store=False
    )
    
    # ========== COMPUTED FIELDS ==========
    
    @api.depends('quality_status')
    def _compute_quality_status_color(self):
        """Set color based on quality status"""
        for move in self:
            if move.quality_status == 'passed':
                move.quality_status_color = 'green'
            elif move.quality_status == 'failed':
                move.quality_status_color = 'red'
            elif move.quality_status == 'quarantine':
                move.quality_status_color = 'orange'
            else:
                move.quality_status_color = 'gray'
    
    # ========== OVERRIDE METHODS ==========
    
    @api.model
    def create(self, vals):
        """Set default quality status"""
        if 'quality_status' not in vals:
            vals['quality_status'] = 'pending'
        return super().create(vals)
    
    def write(self, vals):
        """Track quality status changes"""
        if 'quality_status' in vals:
            vals['quality_check_date'] = fields.Datetime.now()
        return super().write(vals)
    
    def _action_assign(self, force_qty=False):
        """Custom assign logic with quality check"""
        # Check quality before assignment
        moves_with_quality_check = self.filtered(
            lambda m: m.quality_check_required and m.quality_status != 'passed'
        )
        
        if moves_with_quality_check:
            product_names = moves_with_quality_check.mapped('product_id.name')
            raise ValidationError(
                "Cannot assign moves. Quality check not passed for:\n" +
                "\n".join([f"- {name}" for name in product_names])
            )
        
        # Call parent method
        return super()._action_assign(force_qty=force_qty)
    
    def action_mark_quality_passed(self):
        """Mark quality check as passed"""
        self.write({
            'quality_status': 'passed',
            'quality_check_date': fields.Datetime.now()
        })
        return True
    
    def action_mark_quality_failed(self):
        """Mark quality check as failed"""
        self.write({
            'quality_status': 'failed',
            'quality_check_date': fields.Datetime.now()
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Quality Notes',
            'res_model': 'stock.move',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'views': [(False, 'form')],
        }
    
    def action_quarantine_product(self):
        """Move product to quarantine"""
        self.write({
            'quality_status': 'quarantine',
            'quality_check_date': fields.Datetime.now()
        })
        
        # Create quarantine location move if needed
        quarantine_location = self.env['stock.location'].search([
            ('usage', '=', 'quarantine')
        ], limit=1)
        
        if quarantine_location:
            self.copy({
                'location_dest_id': quarantine_location.id,
                'state': 'confirmed',
                'quality_status': 'quarantine',
            })
        
        return True
    
    # ========== VALIDATION METHODS ==========
    
    def _check_quality_before_validation(self):
        """Check quality before validating picking"""
        moves_needing_check = self.filtered(
            lambda m: m.quality_check_required and m.quality_status == 'pending'
        )
        
        if moves_needing_check:
            raise ValidationError(
                "Quality check required for:\n" +
                "\n".join([f"- {m.product_id.name}" for m in moves_needing_check])
            )
    
    def button_validate(self):
        """Override validation to include quality checks"""
        self._check_quality_before_validation()
        return super().button_validate()
    
    # ========== BUSINESS LOGIC ==========
    
    def get_quality_summary(self):
        """Get summary of quality status"""
        summary = []
        if self.quality_check_required:
            summary.append(f"Quality Check: REQUIRED")
        summary.append(f"Status: {self.quality_status}")
        if self.quality_check_date:
            summary.append(f"Checked: {self.quality_check_date}")
        return " | ".join(summary)
    
    @api.model
    def get_pending_quality_checks(self):
        """Get all moves requiring quality checks"""
        return self.search([
            ('quality_check_required', '=', True),
            ('quality_status', '=', 'pending'),
            ('state', 'in', ['confirmed', 'assigned'])
        ])