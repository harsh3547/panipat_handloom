# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm
from datetime import datetime
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class panipat_install(models.Model):
    _name="panipat.install"
    _order="schedule_date desc,state"
    
    name=fields.Char(readonly=True,default='draft',string='Name',copy=False)
    desc=fields.Char(string="Description")
    supplier=fields.Many2one(comodel_name='res.partner', string='Contractor',domain=[('supplier', '=', True)])
    customer=fields.Many2one(comodel_name='res.partner', string='For Customer',domain=[('customer', '=', True)])
    date=fields.Date(string='Created Date',default=fields.Date.today())
    schedule_date=fields.Date(string='Schedule Date')
    order_group=fields.Many2one(comodel_name='panipat.order.group', string='Order Group',readonly=True,copy=False)
    service_lines=fields.One2many(comodel_name="panipat.install.lines", inverse_name="install_service_id", string='Service Lines')
    product_lines=fields.One2many(comodel_name="panipat.install.lines", inverse_name="install_product_id", string='Product Lines')
    notes=fields.Text(string="Internal Notes")
    employee_add=fields.Boolean(string="Add Employees")
    employees=fields.One2many(comodel_name='panipat.employee.schedule', inverse_name='install_id', string="Employees for Installation")
    state = fields.Selection(string="State",selection=[('draft','Draft'),('confirm','Confirmed'),('invoiced','Invoiced'),('cancel','Cancelled')],default='draft',copy=False)
    supplier_invoice = fields.Many2one(comodel_name='account.invoice', string='Supplier Invoice',copy=False,readonly=True)
    customer_invoice = fields.Many2one(comodel_name='account.invoice', string='Customer Invoice',copy=False,readonly=True)
    origin = fields.Char("Source Document",copy=False)
    commission_invoice=fields.Many2one(comodel_name='account.invoice', string='Commission Invoice',copy=False,readonly=True)
    
    @api.model
    def create(self,vals):
        if vals.get('name','draft')=='draft':
            seq=self.env['ir.sequence'].get(code="panipat.install")
            vals['name']=seq
        return super(panipat_install, self).create(vals)
    
    @api.multi
    def write(self,vals):
        print "in write panipat_install self,vals--",self,vals
        return_check = super(panipat_install, self).write(vals)
        for rec in self:
            if rec.state not in ('draft','cancel') and vals.get('employees'):
                rec.employees.cancel_employee_from_schedule()
                rec.employees.delete_employee_from_schedule()
                rec.employees.create_employee_from_schedule(override_vals={'state':'confirm','origin':rec.name or '/'})
                
        return return_check
    
    @api.multi
    def cancel_job(self):
        if not self.supplier_invoice and not self.customer_invoice and not self.commission_invoice:
            return self.after_install_cancel()
        warning_id=self.env['warning.wizard'].create({'customer_invoice':self.customer_invoice.id or False,'supplier_invoice':self.supplier_invoice.id or False,'commission_invoice':self.commission_invoice.id or False,})
        return {
               'name': 'Warning Wizard',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'warning.wizard',
                'type': 'ir.actions.act_window',
                'res_id': warning_id.id,
                'target':'new',
                'context':{'check':'install','form_view_ref':'panipat_handloom.warning_wizard_invoice_view'}
               }
    
    @api.multi
    def after_install_cancel(self):
        if self.supplier_invoice:self.supplier_invoice.write({'origin':''})
        if self.customer_invoice:self.customer_invoice.write({'origin':''})
        if self.commission_invoice:self.commission_invoice.write({'origin':''})
        self.supplier_invoice=False
        self.customer_invoice=False
        self.commission_invoice=False
        self.state='cancel'
        self.employees.cancel_employee_from_schedule()
        self.employees.delete_employee_from_schedule()
        return True
        
    @api.multi
    def button_to_draft(self):
        self.state='draft'
        return True
    
    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state!='cancel':
                raise except_orm(('Error'),('Cancel the record before deleting it !!'))
        return super(panipat_install, self).unlink()
            
    
    @api.multi
    def schedule_employee(self):
        if not self.employees and not self.supplier:
            raise except_orm(('Warning'),('Please add employees or supplier for installation work'))
        self.write({'state':'confirm'})
        self.employees.create_employee_from_schedule(override_vals={'state':'confirm','origin':self.origin+":"+self.name if self.origin else self.name})
        return True
    
    @api.multi
    def make_supplier_invoice(self):
        if self.supplier:
            expense_account_id=self.env['product.category'].default_get(['property_account_expense_categ'])['property_account_expense_categ']
            payable_account_id=self.env['res.partner'].default_get(['property_account_payable'])['property_account_payable']
            line_ids=[]
            for order_line in self.service_lines:
                final_qty=self.pool.get('product.uom')._compute_qty(self._cr,self._uid,order_line.product_uom.id,order_line.product_uom_qty,order_line.product_service_id.uom_po_id.id)
                ctx=self._context.copy()
                ctx['partner_id']=self.supplier and self.supplier.id or False
                line_id = {
                'name':order_line.name or (order_line.product_service_id and order_line.product_service_id.with_context(ctx).name_get()[0][1] or False),
                'account_id': expense_account_id,
                'quantity': final_qty,
                'price_unit':order_line.cost_price or 0.0,
                'product_id': order_line.product_service_id.id or False,
                'uos_id': order_line.product_service_id.uom_po_id.id or False,
                    }
                line_ids.append((0,0,line_id))
    
            
            journal_ids = self.env['account.journal'].search([('type', '=', 'purchase'),],limit=1)
            journal_ids_ch = self.env['account.journal'].search([('type', '=', 'purchase'),('name','ilike','challan')],limit=1)
            if not journal_ids:
                raise except_orm(
                    _('Error!'),
                    _('Define purchase journal for this company: ') )
            print journal_ids[0].id
            vals = {
                'name': '',
                'account_id': self.supplier.property_account_payable.id or payable_account_id,
                'type': 'in_invoice',
                'partner_id': self.supplier.id,
                'journal_id': (len(journal_ids_ch) and journal_ids_ch[0].id) or (len(journal_ids) and journal_ids[0].id) or False,
                'invoice_line': line_ids,
                'origin': self.origin+":"+self.name if self.origin else self.name,
            }
            print vals
            supplier_inv=self.env['account.invoice'].create(vals)
            self.write({'supplier_invoice':supplier_inv.id,'state':'invoiced'})
            self.employees.done_employee_from_schedule()
            new_ctx_form={'form_view_ref':'account.invoice_supplier_form'}
            if supplier_inv.id:
                return {
                        'name': 'Installation Works Invoice',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'account.invoice',
                        'type': 'ir.actions.act_window',
                        'res_id': supplier_inv.id,
                        'context':new_ctx_form,
                        }

        else:
            raise except_orm(
                    _('Error!'),
                    _('No Supplier defined for the defined work ') )
        
        return True
    
    @api.multi
    def make_customer_invoice(self):
        self.ensure_one()
        if self.customer or self._context.get('commission',False):
            income_account_id=self.env['product.category'].default_get(['property_account_income_categ'])['property_account_income_categ']
            receivable_account_id=self.env['res.partner'].default_get(['property_account_receivable'])['property_account_receivable']
            line_ids=[]
            for order_line in self.service_lines:
                
                final_qty=self.pool.get('product.uom')._compute_qty(self._cr,self._uid,order_line.product_uom.id,order_line.product_uom_qty,order_line.product_service_id.uom_id.id)
                line_id = {
                'name':order_line.name or (order_line.product_service_id and order_line.product_service_id.partner_ref) or False,
                'account_id': income_account_id,
                'quantity': final_qty,
                'product_id': order_line.product_service_id.id or False,
                'price_unit':order_line.sale_price or 0.0,
                'uos_id': order_line.product_service_id.uom_id.id or False,
                
                    }
                line_ids.append((0,0,line_id))
            
            if not self._context.get('commission',False):
                # will search for sale rder invoices and if no service line then will attach
                # sale order invoice to this INS job
                sale_objs=self.env['sale.order'].search([('order_group','=',self.order_group.id)])
                cust_inv_ids = [invoice for invoice in sale_objs.invoice_ids if invoice.id]
                if cust_inv_ids:
                    valid_cust_inv=[]
                    for inv in cust_inv_ids:
                        if inv.state=='draft':
                            valid_cust_inv.append(inv)
                            break  # to get only one if there's many that fit this condition
                    if valid_cust_inv:
                        if line_ids:
                            origin_0 = self.origin.split(':')[1] if self.origin else ''
                            origin = valid_cust_inv[0].origin +", "+origin_0+":"+self.name
                            print "-=-=-origin=-=-=-",origin
                            valid_cust_inv[0].write({'invoice_line':line_ids,'origin':origin})

                        self.write({'customer_invoice':valid_cust_inv[0].id,'state':'invoiced'})
                        new_ctx_form={'form_view_ref':'account.invoice_form'}
                        return {
                                'name': 'Installation Works Invoice',
                                'view_type': 'form',
                                'view_mode': 'form',
                                'res_model': 'account.invoice',
                                'type': 'ir.actions.act_window',
                                'res_id': valid_cust_inv[0].id,
                                'context':new_ctx_form,
                                }




            journal_ids = self.env['account.journal'].search([('type', '=', 'sale'),],limit=1)
            journal_ids_ch = self.env['account.journal'].search([('type', '=', 'sale'),('name','ilike','challan')],limit=1)
            if not journal_ids:
                raise except_orm(
                    _('Error!'),
                    _('Define sale journal for this company: ') )
            vals = {
                'name': '',
                'account_id': self.customer.property_account_receivable.id or receivable_account_id,
                'type': 'out_invoice',
                'partner_id': self.supplier.id if self._context.get('commission',False) else self.customer.id,
                'journal_id': (len(journal_ids_ch) and journal_ids_ch[0].id) or (len(journal_ids) and journal_ids[0].id) or False,
                'invoice_line': line_ids,
                'origin': self.origin+":"+self.name if self.origin else self.name,
                'commission_invoice':True if self._context.get('commission',False) else False,
            }
            print vals
            customer_inv=self.env['account.invoice'].create(vals)
            if self._context.get('commission',False):
                self.supplier.write({'customer':True}) # so that in customer payment the supplier name is mentioned
                self.write({'commission_invoice':customer_inv.id,'state':'invoiced'})
            else:
                self.write({'customer_invoice':customer_inv.id,'state':'invoiced'})
            new_ctx_form={'form_view_ref':'account.invoice_form'}
            if customer_inv.id:
                return {
                        'name': 'Installation Works Invoice',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'account.invoice',
                        'type': 'ir.actions.act_window',
                        'res_id': customer_inv.id,
                        'context':new_ctx_form,
                        }


        else:
            raise except_orm(
                    _('Error!'),
                    _('No Customer defined for the defined work ') )
        
        return True
    
    
    
        
    @api.multi
    def view_invoices(self):
        print self._context
        if self._context.get('supplier','False')==True:
            inv_id=self.supplier_invoice.id
            new_ctx_form={'form_view_ref':'account.invoice_supplier_form'}
        if self._context.get('customer','False')==True:
            inv_id=self.customer_invoice.id
            new_ctx_form={'form_view_ref':'account.invoice_form'}
        if self._context.get('commission','False')==True:
            inv_id=self.commission_invoice.id
            new_ctx_form={'form_view_ref':'account.invoice_form'}
        
        
        if inv_id:
            return {
                'name': 'Installation Works Invoice',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.invoice',
                'type': 'ir.actions.act_window',
                'res_id': inv_id,
                'context':new_ctx_form,
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
    @api.onchange('product_service_id','product_lines_id')
    def onchange_product_id(self):
        if self.product_service_id:
            self.product_uom=self.product_service_id.uom_id.id
            self.name=self.product_service_id.name_get()[0][1] if self.product_service_id.name_get() else self.product_service_id.name
            try:
                pricelist=self.pool.get('res.partner').default_get(self._cr, self._uid, ['property_product_pricelist'], context=self._context)['property_product_pricelist']
                abc=self.pool.get('sale.order.line').product_id_change(self._cr,self._uid,[],pricelist,self.product_service_id.id,partner_id=self.install_service_id.customer.id,context=self._context)
                #print "-=-=-abc-==-=",abc
                self.sale_price=abc['value']['price_unit']
            except:
                self.sale_price=self.product_service_id.lst_price
                
            try:
                pricelist_id=self.pool.get('res.partner').default_get(self._cr, self._uid, ['property_product_pricelist_purchase'], context=self._context)['property_product_pricelist_purchase']
                abc=self.pool.get('purchase.order.line').onchange_product_id(self._cr, self._uid, [], pricelist_id, self.product_service_id.id, qty=1.0, uom_id=self.product_uom.id,
            partner_id=self.install_service_id.supplier.id,context=self._context)
                #print "-=-=-abc-==-=",abc
                self.cost_price=abc['value']['price_unit']
            except:
                self.cost_price=self.product_service_id.standard_price
        if self.product_lines_id:
            self.product_uom=self.product_lines_id.uom_id.id
            self.name=self.product_lines_id.name_get()[0][1] if self.product_lines_id.name_get() else self.product_lines_id.name 
    
    install_product_id=fields.Many2one(comodel_name='panipat.install',copy=False)
    install_service_id=fields.Many2one(comodel_name='panipat.install',copy=False)
    sequence = fields.Integer(string="Seq",default=10)
    product_service_id=fields.Many2one(comodel_name='product.product', string='Product',domain=[('type','=','service')])
    product_lines_id=fields.Many2one(comodel_name='product.product', string='Product',domain=[('type','!=','service')])
    name=fields.Char(string="Description")
    product_uom_qty=fields.Float(string="Qty",digits_compute= dp.get_precision('Product UoS'),default=1.0)
    product_uom=fields.Many2one(comodel_name='product.uom', string='Unit')
    sale_price = fields.Float('Sale Price', digits_compute= dp.get_precision('Product Price'))
    cost_price = fields.Float('Cost Price', digits_compute= dp.get_precision('Product Price'))
    
class crm_lead_allocated(models.Model):
    _name="crm.lead.allocated"