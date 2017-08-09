from openerp import models, fields, api, exceptions ,_ 

class account_invoice(models.Model):
    _inherit = "account.invoice"
    _description = "Panipat POS Account"

    is_pos = fields.Boolean('Retail Invoice',default=False)
    picking_id = fields.Many2one('stock.picking','Picking Orders',copy=False)
    name = fields.Char(string='Buyer Order No./ Reference', index=True,
        readonly=True, states={'draft': [('readonly', False)]})
    dispatch_doc=fields.Char(string="Dispatch Doc. No.")
    dispatch_thru=fields.Char(string="Dispatch Through")
    destination=fields.Char(string="Destination")
    
    @api.multi
    def action_cancel(self):
        for inv in self:
            if inv.picking_id:
                raise exceptions.except_orm(_('Error!'), _('You cannot cancel an invoice before Returning the products'))
        return super(account_invoice, self).action_cancel()
    
    @api.onchange("is_pos")
    def onchange_is_pos(self):
        if self.is_pos:self.partner_id=self.env.ref("panipat_handloom.panipat_pos_default_customer")
        
    def _get_default_location(self, cr, uid, context=None):
        wh_obj = self.pool.get('stock.warehouse')
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        res = wh_obj.search(cr, uid, [('company_id', '=', user.company_id.id)], limit=1, context=context)
        if res and res[0]:
            return wh_obj.browse(cr, uid, res[0], context=context).lot_stock_id.id
        return False
    
    
    @api.multi
    def return_product(self):
        self.ensure_one()
        if self.state=='paid' and self.picking_id:
            return {
                'name': _('Delivery Order'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.picking',
                'target': 'current',
                'context': self._context,
                'res_id':self.picking_id.id
            }        
        if self.picking_id:
            self.create_picking(reverse_location=True)
            self.write({'picking_id':False})
            return True
            
    
    @api.multi
    def transfer_product(self):
        self.ensure_one()
        if all(not t.product_id for t in self.invoice_line):
            return {
                    'type': 'ir.actions.client',
                    'tag': 'action_warn',
                    'name': 'Warning',
                    'params': {
                               'title': _('Warning!'),
                               'text': _("There are no 'Product' in invoice lines."),
                               }
                    }
        
        if all(not t.product_id or (t.product_id and t.product_id.type == 'service') for t in self.invoice_line):
            return {
                    'type': 'ir.actions.client',
                    'tag': 'action_warn',
                    'name': 'Warning',
                    'params': {
                               'title': _('Warning!'),
                               'text': _('All the products are of type service.'),
                               }
                    }
        
        
        picking_id=self.create_picking()
        if picking_id:self.write({'picking_id':picking_id})
        return True
    
    @api.multi
    def create_picking(self,reverse_location=False):
        self.ensure_one()
        picking_obj = self.pool.get('stock.picking')
        partner_obj = self.pool.get('res.partner')
        move_obj = self.pool.get('stock.move')
        order = self
            
        addr = order.partner_id and partner_obj.address_get(self._cr, self._uid, [order.partner_id.id], ['delivery']) or {}
        picking_type_id = self.pool.get('ir.model.data').get_object_reference(self._cr, self._uid, 'panipat_handloom', 'picking_type_posout_panipat')[1]
        picking_type = self.pool.get('stock.picking.type').browse(self._cr,self._uid,picking_type_id,self._context)
        picking_id = False
        if picking_type:
            picking_id = picking_obj.create(self._cr, self._uid, {
                'origin': (order.number or '')+":Return" if reverse_location else (order.number or ''),
                'partner_id': addr.get('delivery',False),
                'date_done' : order.date_invoice,
                'picking_type_id': picking_type.id,
                'company_id': order.company_id.id,
                'move_type': 'direct',
                'note': order.comment or "",
                'invoice_state': 'none',
            }, context=self._context)
            self.picking_id = picking_id
        location_id = self._get_default_location()
        if order.partner_id:
            destination_id = order.partner_id.property_stock_customer.id
        elif picking_type:
            if not picking_type.default_location_dest_id:
                raise exceptions.except_orm(_('Error!'), _('Missing source or destination location for picking type %s. Please configure those fields and try again.' % (picking_type.name,)))
            destination_id = picking_type.default_location_dest_id.id
        else:
            destination_id = partner_obj.default_get(self._cr, self._uid, ['property_stock_customer'], context=self._context)['property_stock_customer']

        move_list = []
        for line in order.invoice_line:
            if not line.product_id or (line.product_id and line.product_id.type == 'service'):
                continue

            move_list.append(move_obj.create(self._cr, self._uid, {
                'name': line.name,
                'product_uom': line.product_id.uom_id.id,
                'product_uos': line.product_id.uom_id.id,
                'picking_id': picking_id,
                'picking_type_id': picking_type.id, 
                'product_id': line.product_id.id,
                'product_uos_qty': abs(line.quantity),
                'product_uom_qty': abs(line.quantity),
                'state': 'draft',
                'location_id': location_id if not reverse_location else destination_id,
                'location_dest_id': destination_id if not reverse_location else location_id,
            }, context=self._context))
            
        if picking_id:
            picking_obj.action_confirm(self._cr, self._uid, [picking_id], context=self._context)
            picking_obj.force_assign(self._cr, self._uid, [picking_id], context=self._context)
            picking_obj.action_done(self._cr, self._uid, [picking_id], context=self._context)
        elif move_list:
            move_obj.action_confirm(self._cr, self._uid, move_list, context=self._context)
            move_obj.force_assign(self._cr,self._uid, move_list, context=self._context)
            move_obj.action_done(self._cr, self._uid, move_list, context=self._context)
        return picking_id or False

            @api.multi
    @api.multi
    def product_id_change(self, product, uom_id, qty=0, name='', type='out_invoice',
            partner_id=False, fposition_id=False, price_unit=False, currency_id=False,
            company_id=None):
    
        res = super(account_invoice_line, self).product_id_change(product, uom_id, qty, name, type, partner_id, fposition_id, price_unit, currency_id, company_id)
        if product and type in ('in_invoice', 'in_refund'):
            if res.get('value',False) and res['value'].get('name',False):
                new_name=self.pool.get('product.product').name_get(self._cr, self._uid, [product], self._context)
                if new_name:res['value']['name']=new_name[0][1]

        if product and type in ('out_invoice', 'out_refund'):
            if res.get('value',False) and res['value'].get('name',False):
                ctx=self._context.copy()
                ctx['cust_inv_name_get']=True
                new_name=self.pool.get('product.product').name_get(self._cr, self._uid, [product], context=ctx)
                if new_name:res['value']['name']=new_name[0][1]

        res['value']['hsn_code']=self.pool.get("product.product").browse(self._cr, self._uid,product,context=self._context).product_tmpl_id.hsn_code