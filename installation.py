# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm
from datetime import datetime
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class panipat_install(models.Model):
    _name="panipat.install"
    _order="schedule_date desc,state"
    
    name=fields.Char(readonly=True,default='/',string='Name',copy=False)
    desc=fields.Char(string="Description")
    supplier=fields.Many2one(comodel_name='res.partner', string='Contractor',domain=[('supplier', '=', True)])
    customer=fields.Many2one(comodel_name='res.partner', string='For Customer',domain=[('customer', '=', True)])
    date=fields.Date(string='Created Date',default=fields.Date.today())
    schedule_date=fields.Date(string='Schedule Date')
    order_group=fields.Many2one(comodel_name='procurement.group', string='Order Group',readonly=True,copy=False)
    install_lines=fields.One2many(comodel_name="panipat.install.lines", inverse_name="install_id", string='Order Lines')
    notes=fields.Text(string="Internal Notes")
    employee_add=fields.Boolean(string="Add Employees")
    employees=fields.One2many(comodel_name='panipat.employee', inverse_name='install_id', string="Employees Schedule")
    state = fields.Selection(string="State",selection=[('draft','Draft'),('confirm','Confirmed')],default='draft')
    supplier_invoice = fields.Selection(string="Supplier Invoice",selection=[('invoiced','Invoiced'),('2binvoiced','To be Invoiced')],default='2binvoiced',copy=False)
    customer_invoice = fields.Selection(string="Customer Invoice",selection=[('invoiced','Invoiced'),('2binvoiced','To be Invoiced')],default='2binvoiced',copy=False)

    
    @api.multi
    def schedule_employee(self):
        if not self.employees and not self.supplier:
            raise except_orm(('Warning'),('Please add employees or supplier for installation work'))
        if not self.schedule_date:
            raise except_orm(('Warning'),('Please enter a schedule date (for deadlines)'))
        self.employees.schedule_employee()
        self.write({'state':'confirm','name':self.env['ir.sequence'].get(code="panipat.install")})
        return True
    
    @api.multi
    def make_supplier_invoice(self):
        if self.supplier:
            expense_account_id=self.env['product.category'].default_get(['property_account_expense_categ'])['property_account_expense_categ']
            payable_account_id=self.env['res.partner'].default_get(['property_account_payable'])['property_account_payable']
            line_ids=[]
            for order_line in self.install_lines:
                
                final_qty=self.pool.get('product.uom')._compute_qty(self._cr,self._uid,order_line.product_uom.id,order_line.product_uom_qty,order_line.product_id.uom_po_id.id)
                ctx=self._context.copy()
                ctx['partner_id']=self.supplier and self.supplier.id or False
                line_id = {
                'name':order_line.product_id.with_context(ctx).name_get()[0][1],
                'account_id': expense_account_id,
                'quantity': final_qty,
                'product_id': order_line.product_id.id or False,
                'uos_id': order_line.product_id.uom_po_id.id or False,
                    }
                line_ids.append((0,0,line_id))
    
            
            journal_ids = self.env['account.journal'].search([('type', '=', 'purchase'),],limit=1)
            if not journal_ids:
                raise except_orm(
                    _('Error!'),
                    _('Define purchase journal for this company: ') )
            print journal_ids[0].id
            vals = {
                'name': self.name,
                'account_id': self.supplier.property_account_payable.id or payable_account_id,
                'type': 'in_invoice',
                'partner_id': self.supplier.id,
                'journal_id': len(journal_ids) and journal_ids[0].id or False,
                'invoice_line': line_ids,
                'origin': self.name,
            }
            print vals
            supplier_inv=self.env['account.invoice'].create(vals)
            self.write({'supplier_invoice':'invoiced'})
        else:
            raise except_orm(
                    _('Error!'),
                    _('No Supplier defined for the defined work ') )
        
        return True
    
    @api.multi
    def make_customer_invoice(self):
        if self.customer:
            income_account_id=self.env['product.category'].default_get(['property_account_income_categ'])['property_account_income_categ']
            receivable_account_id=self.env['res.partner'].default_get(['property_account_receivable'])['property_account_receivable']
            line_ids=[]
            for order_line in self.install_lines:
                
                final_qty=self.pool.get('product.uom')._compute_qty(self._cr,self._uid,order_line.product_uom.id,order_line.product_uom_qty,order_line.product_id.uom_id.id)
                line_id = {
                'name':order_line.product_id.name_get()[0][1],
                'account_id': income_account_id,
                'quantity': final_qty,
                'product_id': order_line.product_id.id or False,
                'uos_id': order_line.product_id.uom_id.id or False,
                    }
                line_ids.append((0,0,line_id))
    
            
            journal_ids = self.env['account.journal'].search([('type', '=', 'sale'),],limit=1)
            if not journal_ids:
                raise except_orm(
                    _('Error!'),
                    _('Define sale journal for this company: ') )
            print journal_ids[0].id
            vals = {
                'name': self.name,
                'account_id': self.customer.property_account_receivable.id or receivable_account_id,
                'type': 'out_invoice',
                'partner_id': self.customer.id,
                'journal_id': len(journal_ids) and journal_ids[0].id or False,
                'invoice_line': line_ids,
                'origin': self.name,
            }
            print vals
            supplier_inv=self.env['account.invoice'].create(vals)
            self.write({'customer_invoice':'invoiced'})
        else:
            raise except_orm(
                    _('Error!'),
                    _('No Customer defined for the defined work ') )
        
        return True
    
    
    
        
    @api.multi
    def view_invoices(self):
        print self._context
        if self._context.get('supplier','False')==True:
            inv_objs=self.env['account.invoice'].search([('origin','=',self.name),('type','=','in_invoice')])
            new_ctx_tree_form={'tree_view_ref':'account.invoice_tree',
                           'form_view_ref':'account.invoice_supplier_form',}
            new_ctx_form={'form_view_ref':'account.invoice_supplier_form'}
        if self._context.get('customer','False')==True:
            inv_objs=self.env['account.invoice'].search([('origin','=',self.name),('type','=','out_invoice')])
            new_ctx_tree_form={'tree_view_ref':'account.invoice_tree',
                           'form_view_ref':'account.invoice_form',}
            new_ctx_form={'form_view_ref':'account.invoice_form'}
        
        inv_ids=map(int, inv_objs or []) 
        if inv_ids:
            if len(inv_ids) == 1 :
                return {
                'name': 'Installation Works Invoice',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.invoice',
                'type': 'ir.actions.act_window',
                'res_id': inv_ids[0],
                'context':new_ctx_form,
                }
            else :
                return {
                'name': 'Installation Works Invoices',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.invoice',
                'type': 'ir.actions.act_window',
                'domain':[('id','in',inv_ids)],
                'context':new_ctx_tree_form,
                }
        else :
            return {
                    'type': 'ir.actions.client',
                    'tag': 'action_warn',
                    'name': 'Warning',
                    'params': {
                               'title': 'Warning!',
                               'text': 'No invoices attached to this work.',
                               }
                    }
    


    
class panipat_install_lines(models.Model):
    _name="panipat.install.lines"
    
    @api.one
    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom=self.product_id.uom_id.id
            self.name=self.product_id.name_get()[0][1] if self.product_id.name_get() else self.product_id.name 
    
    install_id=fields.Many2one(comodel_name='panipat.install',copy=False)
    sequence = fields.Integer(string="Seq",default=10)
    product_id=fields.Many2one(comodel_name='product.product', string='Product',required=True)
    name=fields.Char(string="Description")
    product_uom_qty=fields.Float(string="Qty",digits_compute= dp.get_precision('Product UoS'),default=1.0,required=True)
    product_uom=fields.Many2one(comodel_name='product.uom', string='Unit',required=True)
    
    
