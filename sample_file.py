# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm
from datetime import datetime
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class panipat_sample(models.Model):
    _name="panipat.sample"
    _order="date desc,name desc"
    
    
    name=fields.Char(string="Order No.",copy=False,default='/',readonly=True)
    partner_id=fields.Many2one(comodel_name="res.partner", string="Customer",required=True)
    date=fields.Date(string="Date",default=fields.Date.today())
    state=fields.Selection(selection=[('draft','Draft'),('confirm', 'Confirmed'),('sample_sent','Sample Sent'),('sample_returned','Sample Returned'),('done','Done')],copy=False,default='draft')
    state_paid=fields.Selection(selection=[('deposit','Deposit Paid'),('deposit_returned','Deposit Returned')],copy=False)
    sample_out=fields.One2many(comodel_name='panipat.sample.lines', inverse_name='sample_out', string="Outgoing Samples")
    sample_in=fields.One2many(comodel_name='panipat.sample.lines', inverse_name='sample_in', string="Returned Samples")
    
    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ('draft','cancel'):
                raise except_orm(_('Warning!'), _('Cannot delete a record which has been confirmed. Please cancel the record and then delete it !'))
        return super(panipat_sample, self).unlink()
    
    @api.multi
    def write(self,vals):
        if vals.get('state',False)=='confirm':
            vals['name']=self.env['ir.sequence'].get('panipat.sample.sequence.type') or '/'
        return super(panipat_sample, self).write(vals)
    
    @api.multi
    def button_confirm(self):
        self.write({'state':'confirm','date':fields.Date.today()})
        return True
    
    @api.multi
    def send_sample(self):
        if not self.sample_out:
            raise except_orm(_('Warning!'), _('No Outgoing Samples !'))
        partner_obj = self.env['res.partner']
        move_obj = self.pool.get('stock.move')
        user = self.env['res.users'].browse(self._uid)
        res = self.env['stock.warehouse'].search([('company_id', '=', user.company_id.id)], limit=1)

        default_stock_location = res.lot_stock_id.id
        destination_id = partner_obj.default_get(['property_stock_customer'])['property_stock_customer']
        move_list = []
        for line in self.sample_out:
            if line.product_id and line.product_id.type == 'service':
                continue

            move_list.append(move_obj.create(self._cr, self._uid,{
                'name': self.name,
                'product_uom': line.product_id.uom_id.id,
                'product_uos': line.product_id.uom_id.id,
                'product_id': line.product_id.id,
                'product_uos_qty': abs(line.qty),
                'product_uom_qty': abs(line.qty),
                'state': 'draft',
                'location_id': default_stock_location,
                'location_dest_id': destination_id,
                'invoice_state':'none',
                'procure_method':'make_to_stock',
            }, context=self._context))
            
        if move_list:
            move_obj.action_confirm(self._cr, self._uid, move_list, context=self._context)
            move_obj.force_assign(self._cr,self._uid, move_list, context=self._context)
            move_obj.action_done(self._cr, self._uid, move_list, context=self._context)
        self.write({'state':'sample_sent'})
        return True

    @api.multi
    def return_sample_wizard(self):
        self._cr.execute("delete from panipat_sample_wizard")
        print "-----in return sample wizard----"
        wizard_id=self.env['panipat.sample.wizard'].create({})
        in_out_rel_ids=[rec.sample_in_out_rel.id for rec in self.sample_in]
        print "=====in_out_rel_ids==",in_out_rel_ids
        for line in self.sample_out:
            if line.product_id and line.product_id.type == 'service' or line.id in in_out_rel_ids:
                continue
            wizard_line_id=self.pool.get('panipat.sample.lines').copy(self._cr,self._uid,line.id,default={'sample_wizard':wizard_id.id,'sample_in_out_rel':line.id},context=self._context)
        return {
                'name': 'Sample Wizard Form',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'panipat.sample.wizard',
                'type': 'ir.actions.act_window',
                'res_id': wizard_id.id,
                'target':'new'
                }
            
    @api.multi
    def return_sample(self):
        print "=====in return sample====="
        out_product_qty={}
        in_product_qty={}
        if self.sample_out:
            for rec in self.sample_out:
                if out_product_qty.get(str(rec.product_id.id),False):
                    out_product_qty[str(rec.product_id.id)] += rec.qty
                else: out_product_qty[str(rec.product_id.id)] = rec.qty
            
            for rec in self.sample_in:
                if in_product_qty.get(str(rec.product_id.id),False):
                    in_product_qty[str(rec.product_id.id)] += rec.qty
                else: in_product_qty[str(rec.product_id.id)] = rec.qty
            
            check=True
            for key in out_product_qty:
                if out_product_qty[key]>in_product_qty[key]:check=False
            if check:self.write({'state':'sample_returned'})
            print "====out_product_qty={},,,in_product_qty={}====",out_product_qty,in_product_qty
        else:
            self.write({'state':'sample_returned'})
        return True
    
    
    
class panipat_sample_lines(models.Model):
    _name="panipat.sample.lines"
    
    def _get_sample_categ(self):
        return self.env.ref("panipat_handloom.panipat_sample_category")
    
    
    product_categ=fields.Many2one(comodel_name='product.category', string='Category',default=_get_sample_categ)
    product_id=fields.Many2one(comodel_name='product.product', string='Product',required=True)
    product_uom=fields.Many2one(comodel_name='product.uom', string='Unit',required=True)
    qty=fields.Float(String='Quantity',digits= dp.get_precision('Product Unit of Measure'),        required=True,default=1)
    sample_out=fields.Many2one(comodel_name='panipat.sample',copy=False)
    # sample_out if for one2many of samples_sent
    sample_in=fields.Many2one(comodel_name='panipat.sample',copy=False)
    # sample_in if for one2many of samples coming back in
    sample_wizard=fields.Many2one(comodel_name='panipat.sample.wizard', ondelete='cascade',copy=False)
    sample_in_out_rel=fields.Many2one(comodel_name='panipat.sample.lines')
    # sample_in_out_rel ..value of this is to link sample_in lines with sample_out lines for the wizard
    # and to know which samples have been returned 
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.product_uom=self.product_id.uom_id.id
        
class panipat_sample_wizard(models.Model):
    _name='panipat.sample.wizard'
    
    sample_out_lines=fields.One2many(comodel_name='panipat.sample.lines', inverse_name='sample_wizard', string="Sample Lines")
    
    @api.multi
    def return_sample(self):
        print self._context
        partner_obj = self.env['res.partner']
        move_obj = self.pool.get('stock.move')
        user = self.env['res.users'].browse(self._uid)
        res = self.env['stock.warehouse'].search([('company_id', '=', user.company_id.id)], limit=1)

        default_stock_location = res.lot_stock_id.id
        destination_id = partner_obj.default_get(['property_stock_customer'])['property_stock_customer']
        move_list = []
        
        panipat_obj=self.env['panipat.sample'].browse(self._context.get('active_id',False))
        
        for line in self.sample_out_lines:
            self.pool.get('panipat.sample.lines').copy(self._cr,self._uid,line.id,default={'sample_in':self._context.get('active_id',False)},context=self._context)
            
            if line.product_id and line.product_id.type == 'service':
                continue

            move_list.append(move_obj.create(self._cr, self._uid,{
                'name': panipat_obj.name,
                'product_uom': line.product_id.uom_id.id,
                'product_uos': line.product_id.uom_id.id,
                'product_id': line.product_id.id,
                'product_uos_qty': abs(line.qty),
                'product_uom_qty': abs(line.qty),
                'state': 'draft',
                'location_id': destination_id,
                'location_dest_id': default_stock_location,
                'invoice_state':'none',
                'procure_method':'make_to_stock',
            }, context=self._context))
            
        if move_list:
            move_obj.action_confirm(self._cr, self._uid, move_list, context=self._context)
            move_obj.force_assign(self._cr,self._uid, move_list, context=self._context)
            move_obj.action_done(self._cr, self._uid, move_list, context=self._context)
        
            
        panipat_obj.return_sample()
        return True
    
    
    
    
        