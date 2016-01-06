# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm
from datetime import datetime
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class account_move_line(models.Model):
    _inherit='account.move.line'
    
    sample_in=fields.Many2one(comodel_name='panipat.sample')
    sample_out=fields.Many2one(comodel_name='panipat.sample')

class panipat_sample(models.Model):
    _name="panipat.sample"
    _order="date desc,name desc"
    
    name=fields.Char(string="Order No.",copy=False,default='/',readonly=True)
    partner_id=fields.Many2one(comodel_name="res.partner", string="Customer",required=True)
    date=fields.Date(string="Date")
    state=fields.Selection(selection=[('draft','Draft'),('confirm', 'Confirmed'),('sample_sent','Sample Sent'),('sample_returned','Sample Returned'),('done','Closed'),('cancel','Cancelled')],copy=False,default='draft')
    state_paid=fields.Selection(selection=[('deposit','Deposit Paid'),('deposit_returned','Deposit Returned'),('credit','Credited'),('done','Closed'),('cancel','Cancel')],copy=False)
    sample_out=fields.One2many(comodel_name='panipat.sample.lines', inverse_name='sample_out', string="Outgoing Samples")
    sample_in=fields.One2many(comodel_name='panipat.sample.lines', inverse_name='sample_in', string="Returned Samples")
    amount_paid=fields.Float('Amount Paid',readonly=True,copy=False)
    amount_returned=fields.Float('Amount Returned',readonly=True,copy=False)
    sample_in_account_lines=fields.One2many(comodel_name='account.move.line', inverse_name='sample_in', string='Sample Return Entries',copy=False)
    sample_out_account_lines=fields.One2many(comodel_name='account.move.line', inverse_name='sample_out', string='Sample Outgoing Entries',copy=False)
    
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
        if not self.sample_out:
            raise except_orm(_('Warning!'), _('No Outgoing Samples !'))
        if self.date:vals={'state':'confirm'}
        else:vals={'state':'confirm','date':fields.Date.today()}
        self.write(vals)
        return True
    
    @api.multi
    def button_done(self):
        self.write({'state':'done','state_paid':'done'})
        return True
    
    @api.multi
    def send_sample_wizard(self):
        return {
                'name': 'Sample Wizard Form',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id':self.env.ref('panipat_handloom.panipat_wizard_pay_form_view').id,
                'res_model': 'panipat.pay.wizard',
                'type': 'ir.actions.act_window',
                'target':'new'
                }
        
    
    @api.multi
    def send_sample(self):
        print "====context==send_sample===",self._context,self.env['account.period'].find().id
        
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
        
        income_account_id=self.env['product.category'].default_get(['property_account_income_categ'])['property_account_income_categ']
        receivable_account_id=self.env['res.partner'].default_get(['property_account_receivable'])['property_account_receivable']
        journal_id=self.env.ref('panipat_handloom.panipat_sample_journal')
        
        if self._context.get('paid_amount',0.0)!=0.0:
            account_move_id=self.env['account.move'].create({'journal_id':journal_id.id,'date':fields.Date.today(),'ref':self.name,'period_id':self.env['account.period'].find().id})
            print "======account_move_id====",account_move_id
            ### product sale credit
            self.env['account.move.line'].create({'name':self._context.get('ref') or '/',
                                                  'partner_id':self.partner_id.id,
                                                  'account_id':income_account_id,
                                                  'debit':0.0,
                                                  'credit':self._context.get('paid_amount',0.0),
                                                  'move_id':account_move_id.id,
                                                  'sample_out':self.id,
                                                  'date':self._context.get('date',False)
                                                  })
            ### cash/bank credit
            self.env['account.move.line'].create({'name':self._context.get('ref') or '/',
                                                  'partner_id':self.partner_id.id,
                                                  'account_id':self._context.get('payment_method'),
                                                  'debit':self._context.get('paid_amount',0.0),
                                                  'credit':0.0,
                                                  'move_id':account_move_id.id,
                                                  'sample_out':self.id,
                                                  'date':self._context.get('date',False)
                                                  })
            account_move_id.button_validate()
        self.write({'amount_paid':self._context.get('paid_amount',0.0),'state_paid':'deposit'})
        return True

    @api.multi
    def return_sample_wizard(self):
        print "-----in return sample wizard----"
        wizard_id=self.env['panipat.sample.wizard'].create({'state_paid':self.state_paid})
        in_out_rel_ids=[[rec.sample_in_out_rel.id,rec.qty] for rec in self.sample_in]
        # if the same line of products is returned less than original qty
        # in_out_rel_ids_dict is for checking which line has received how much back
        in_out_rel_ids_dict={}
        for rec in in_out_rel_ids:
            if in_out_rel_ids_dict.get(rec[0],False):
                in_out_rel_ids_dict[rec[0]] += rec[1]
            else: in_out_rel_ids_dict[rec[0]] = rec[1]
            
        print "=====in_out_rel_ids==",in_out_rel_ids,in_out_rel_ids_dict
        for line in self.sample_out:
            if line.product_id and line.product_id.type == 'service' or (in_out_rel_ids_dict.get(line.id,False) and in_out_rel_ids_dict.get(line.id,False)>=line.qty ):
                continue

            self.pool.get('panipat.sample.lines').copy(self._cr,self._uid,line.id,default={'sample_wizard':wizard_id.id,'sample_in_out_rel':line.id,'qty':line.qty-in_out_rel_ids_dict.get(line.id,0.0)},context=self._context)
        
        return {
                'name': 'Sample Wizard Form',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id':self.env.ref('panipat_handloom.panipat_sample_wizard_form_view').id,
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
        if self.sample_out: # for conditions when sample out is empty
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
                if out_product_qty[key]>in_product_qty.get(key,-1):check=False
            if check:self.write({'state':'sample_returned'})
            print "====out_product_qty={},,,in_product_qty={}====",out_product_qty,in_product_qty
        else:
            self.write({'state':'sample_returned'})
        vals={}
        vals['amount_returned']=self.amount_returned+self._context.get('amount_returned',0.0)
        if self.amount_paid==self.amount_returned :vals['state_paid']='deposit_returned'
        if self._context.get('diff_option',False)=='credit':vals['state_paid']='credit'
        self.write(vals)
        return True
    
    @api.multi
    def button_cancel(self):
        for rec in self.sample_in_account_lines:
            if rec.reconcile_ref:
                raise except_orm(_('Warning!'), _('You cannot cancel the order whose payment has been adjusted with another record/invoice/order !'))
        return {
                'name': 'Sample Cancel Wizard Form',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id':self.env.ref('panipat_handloom.panipat_cancel_wizard_form_view').id,
                'res_model': 'panipat.cancel.wizard',
                'type': 'ir.actions.act_window',
                'target':'new'
                }
            
    
    
class panipat_sample_lines(models.Model):
    _name="panipat.sample.lines"
    
    def _get_sample_categ(self):
        return self.env.ref("panipat_handloom.panipat_sample_category")
    
    
    product_categ=fields.Many2one(comodel_name='product.category', string='Category',default=_get_sample_categ)
    product_id=fields.Many2one(comodel_name='product.product', string='Product',required=True)
    product_uom=fields.Many2one(comodel_name='product.uom', string='Unit',required=True)
    qty=fields.Float(String='Quantity',digits= dp.get_precision('Product Unit of Measure'), required=True,default=1)
    sample_out=fields.Many2one(comodel_name='panipat.sample')
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
    
class panipat_pay_wizard(models.Model):
    _name='panipat.pay.wizard'
    
    def _get_cash_journal(self):
        id=self.env['account.journal'].search([('type','=','cash')])
        if id:
            return id[0]
        else:
            return False 
    
    paid_amount=fields.Float('Paid Amount',required=True)
    payment_method=fields.Many2one(comodel_name='account.journal', string='Payment Method',domain=[('type','=','cash')],required=True,default=_get_cash_journal)
    date=fields.Date('Date',default=fields.Date.today(),required=True)
    ref=fields.Char('Ref')
    
    @api.multi
    def register_payment(self):
        ctx=dict(self._context)
        panipat_obj=self.env['panipat.sample'].browse(self._context.get('active_id',False))
        ctx['paid_amount']=self.paid_amount
        ctx['payment_method']=self.payment_method.default_debit_account_id.id
        ctx['date']=self.date
        ctx['ref']=self.ref
        panipat_obj.with_context(ctx).send_sample()
        return True
        
class panipat_sample_wizard(models.Model):
    _name='panipat.sample.wizard'
    
    def _get_cash_journal(self):
        id=self.env['account.journal'].search([('type','=','cash')])
        if id:
            return id[0]
        else:
            return False 
    
    @api.depends('return_amount')    
    def get_diff_amount(self):
        active_id_obj=self.env['panipat.sample'].browse(self._context.get('active_id'))
        self.diff_amount=active_id_obj.amount_paid - active_id_obj.amount_returned - self.return_amount
    
    sample_in_lines=fields.One2many(comodel_name='panipat.sample.lines', inverse_name='sample_wizard', string="Sample Lines")
    return_amount=fields.Float('Return Amount')
    date=fields.Date('Date',default=fields.Date.today(),required=True)
    ref=fields.Char('Ref')
    diff_amount=fields.Float(compute='get_diff_amount',string='Difference Amount')
    diff_option=fields.Selection(selection=[('open','Keep Open'),('credit','Credit to Customer')], string='Payment Difference',default='open')
    payment_method=fields.Many2one(comodel_name='account.journal', string='Payment Method',domain=[('type','=','cash')],required=True,default=_get_cash_journal)
    state_paid=fields.Selection(selection=[('deposit','Deposit Paid'),('deposit_returned','Deposit Returned'),('credit','Credited')],copy=False)
        
    @api.multi
    def return_sample(self):
        print self._context
        panipat_obj=self.env['panipat.sample'].browse(self._context.get('active_id',False))
        partner_obj = self.env['res.partner']
        move_obj = self.pool.get('stock.move')
        user = self.env['res.users'].browse(self._uid)
        res = self.env['stock.warehouse'].search([('company_id', '=', user.company_id.id)], limit=1)

        default_stock_location = res.lot_stock_id.id
        destination_id = partner_obj.default_get(['property_stock_customer'])['property_stock_customer']
        move_list = []
        
        for line in self.sample_in_lines:
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
            
        
        income_account_id=self.env['product.category'].default_get(['property_account_income_categ'])['property_account_income_categ']
        receivable_account_id=self.env['res.partner'].default_get(['property_account_receivable'])['property_account_receivable']
        journal_id=self.env.ref('panipat_handloom.panipat_sample_journal')
        account_move_id=False
        for journal_entry in panipat_obj.sample_out_account_lines:
            if journal_entry.move_id:
                account_move_id=journal_entry.move_id
                break
        
        if self.state_paid=='deposit' and self.return_amount!=0.0 and account_move_id:

            print "======account_move_id====",account_move_id
            ### product sale credit
            self.env['account.move.line'].create({'name':self.ref or '/',
                                                  'partner_id':panipat_obj.partner_id.id,
                                                  'account_id':income_account_id,
                                                  'debit':self.return_amount,
                                                  'credit':0.0,
                                                  'move_id':account_move_id.id,
                                                  'sample_in':panipat_obj.id,
                                                  'date':self.date
                                                  })
            ### cash/bank or partner credit
            self.env['account.move.line'].create({'name':self.ref or '/',
                                                  'partner_id':panipat_obj.partner_id.id,
                                                  'account_id':self.payment_method.default_debit_account_id.id,
                                                  'debit':0.0,
                                                  'credit':self.return_amount,
                                                  'move_id':account_move_id.id,
                                                  'sample_in':panipat_obj.id,
                                                  'date':self.date
                                                  })
            account_move_id.button_validate()
        
        if self.state_paid=='deposit' and self.diff_option=='credit' and account_move_id:
            
            print "======account_move_id====",account_move_id
            ### product sale credit
            self.env['account.move.line'].create({'name':self.ref or '/',
                                                  'partner_id':panipat_obj.partner_id.id,
                                                  'account_id':income_account_id,
                                                  'debit':self.diff_amount,
                                                  'credit':0.0,
                                                  'move_id':account_move_id.id,
                                                  'sample_in':panipat_obj.id,
                                                  'date':self.date
                                                  })
            ### cash/bank or partner credit
            self.env['account.move.line'].create({'name':self.ref or '/',
                                                  'partner_id':panipat_obj.partner_id.id,
                                                  'account_id':receivable_account_id,
                                                  'debit':0.0,
                                                  'credit':self.diff_amount,
                                                  'move_id':account_move_id.id,
                                                  'sample_in':panipat_obj.id,
                                                  'date':self.date
                                                  })
            account_move_id.button_validate()
         
                
        ctx=dict(self._context)
        ctx['amount_returned']=self.return_amount or 0.0
        ctx['diff_option']=self.diff_option or False
        panipat_obj.with_context(ctx).return_sample()
                    
        return True
    
class cancel_wizard(models.TransientModel):
    _name='panipat.cancel.wizard'
    
    @api.multi
    def button_cancel(self):
        panipat_obj=self.env['panipat.sample'].browse(self._context.get('active_id',False))
        product_qty={}
        for rec in panipat_obj.sample_out:
            if rec.product_id.type == 'service':continue
            if product_qty.get(rec.product_id.id,False):product_qty['rec.product_id.id'] += rec.qty
            else: product_qty['rec.product_id.id'] = rec.qty
        for rec in panipat_obj.sample_in:
            if product_qty.get(rec.product_id.id,False):product_qty['rec.product_id.id'] -= rec.qty
            else: product_qty['rec.product_id.id'] = -rec.qty
        
        product_obj = self.env['product.product']
        partner_obj = self.env['res.partner']
        move_obj = self.pool.get('stock.move')
        user = self.env['res.users'].browse(self._uid)
        res = self.env['stock.warehouse'].search([('company_id', '=', user.company_id.id)], limit=1)

        default_stock_location = res.lot_stock_id.id
        destination_id = partner_obj.default_get(['property_stock_customer'])['property_stock_customer']
        move_list = []
        
        for line in product_qty:
            if product_qty(line)==0:continue
            move_list.append(move_obj.create(self._cr, self._uid,{
                'name': panipat_obj.name+":cancel",
                'product_uom': product_obj.browse(line).uom_id.id,
                'product_uos': product_obj.browse(line).uom_id.id,
                'product_id': line,
                'product_uos_qty': abs(product_qty(line)),
                'product_uom_qty': abs(product_qty(line)),
                'state': 'draft',
                'location_id': destination_id if product_qty(line)>0 else default_stock_location,
                'location_dest_id': default_stock_location if product_qty(line) else destination_id,
                'invoice_state':'none',
                'procure_method':'make_to_stock',
            }, context=self._context))
            
        if move_list:
            move_obj.action_confirm(self._cr, self._uid, move_list, context=self._context)
            move_obj.force_assign(self._cr,self._uid, move_list, context=self._context)
            move_obj.action_done(self._cr, self._uid, move_list, context=self._context)
        
        account_move_id=False
        for rec in panipat_obj.sample_out_account_lines:
            if rec.move_id:
                account_move_id=rec.move_id
                break
        if not account_move_id:
            for rec in panipat_obj.sample_in_account_lines:
                if rec.move_id:
                    account_move_id=rec.move_id
                    break
        print "=-=-=-=-=-account_move_id=-=-=-=-=",account_move_id
        if account_move_id and account_move_id.state=='posted':
            account_move_id.button_cancel()
            account_move_id.unlink()
        return True
    
    
    
    
    
    
        