# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm
from datetime import datetime
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class panipat_crm_lead(models.Model):
    _name = "panipat.crm.lead"
    _rec_name = 'sequence'
    _order = 'sequence desc'


    def _get_custom_company_default(self):
        value= self.env.user.company_id
        #print value
        return value

    
    def _get_amount_paid(self):
        amount_paid=0.0
        for rec_self in self:
            rec_self.total_paid_amount = -1*rec_self.partner_id.credit if rec_self.partner_id and rec_self.partner_id.credit and rec_self.partner_id.credit<=0 else 0.00
        
    def lead_amount_paid_records(self,cr,uid,id,context=None):
        obj = self.browse(cr,uid,id,context=None)
        abc=(obj.sequence or '') + (obj.order_group and ':') + (obj.order_group and obj.order_group.name or '') +':'+'ADVANCE (lead)'
        print "-=-=-=-=-=",abc
        return {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'account.voucher',
                    'type': 'ir.actions.act_window',
                    'context': {
                            'form_view_ref':'account_voucher.view_vendor_receipt_form',
                            'default_partner_id': obj.partner_id.parent_id.id if obj.partner_id.parent_id else obj.partner_id.id,
                            'default_name':abc,
                            'order_group':obj.order_group.id,
                            'search_disable_custom_filters': False
                            }

                    }

    

    def button_quote(self,cr,uid,id,context=None):
        lead_obj = self.browse(cr,uid,id,context)
        values=[]
        vals={}
        if context is None:context={}
        if lead_obj.product_line :
            for i in lead_obj.product_line :
                values.append((0,0,{'product_id':i.product_id.id,
                                    'name':i.description or self.pool.get('product.product').name_get(cr,uid,[i.product_id.id],context)[0][1] or "",
                                    'product_uom_qty':i.product_uom_qty,
                                    'product_uom':i.product_uom.id,
                                    'price_unit':i.sale_price,
                                    
                                    }))
            vals.update({'order_line':values})
                
        if lead_obj.partner_id and lead_obj.partner_id.id:
            vals.update({'partner_id':lead_obj.partner_id.id}) 
        vals['order_group'] = lead_obj.order_group.id
        vals['origin']=lead_obj.sequence
        vals['client_order_ref']=lead_obj.client_order_ref
        print "---------vals in make_qutaion ==========",vals
        quotation_id = self.pool.get('sale.order').create(cr,uid,vals,context=None)
        self.write(cr,uid,id,{'state':'quotation','sale_order':quotation_id},context=None)
        return {
                'name': 'Sale Order Form',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window',
                'res_id': quotation_id,
                }
    
    
    def view_quotation(self,cr,uid,id,context=None):
        vals = {}
        obj = self.browse(cr,uid,id,context=None)
        sale_id = obj.sale_order
        if sale_id :
            return {
                'name': 'Sale Order Form',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window',
                'res_id': sale_id.id,
                }
        else :
            return {
                    'type': 'ir.actions.client',
                    'tag': 'action_warn',
                    'name': 'Warning',
                    'params': {
                               'title': 'Warning!',
                               'text': 'Quotation is not available or has been deleted .',
                               }
                    }
            



    def button_install(self,cr,uid,id,context=None):
        lead_obj = self.browse(cr,uid,id,context)
        values=[]
        vals={}
        vals['customer']=lead_obj.partner_id.id
        vals['order_group']=lead_obj.order_group.id
        vals['origin']=lead_obj.sequence
        if lead_obj.product_line :
            for i in lead_obj.product_line :
                values.append((0,0,{'product_id':i.product_id.id,
                                    'name':i.description or self.pool.get('product.product').name_get(cr,uid,[i.product_id.id],context=context)[0][1] or "",
                                    'product_uom':i.product_uom.id,
                                    'product_uom_qty':i.product_uom_qty,
                                    }))
            vals.update({'product_lines':values})
        install_id=self.pool.get('panipat.install').create(cr,uid,vals,context=None)
        self.write(cr,uid,id,{'state':'install','install_id':install_id},context=None)
        return {
                'name': 'Installation Form',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'panipat.install',
                'type': 'ir.actions.act_window',
                'res_id': install_id,
                }
    
    def view_install_job(self,cr,uid,id,context=None):
        vals = {}
        obj=self.browse(cr,uid,id,context=None)
        install_id = obj.install_id
        if install_id:
            return {
                'name': 'Installation Form',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'panipat.install',
                'type': 'ir.actions.act_window',
                'res_id': obj.install_id.id,
                }
        else :
            return {
                    'type': 'ir.actions.client',
                    'tag': 'action_warn',
                    'name': 'Warning',
                    'params': {
                               'title': 'Warning!',
                               'text': 'Install Job is not available or has been deleted .',
                               }
                    }

    
    def button_confirm(self,cr,uid,id,context=None):
        lead_obj=self.browse(cr,uid,id,context)
        vals={'state':'confirm'}
        if lead_obj.sequence in ('draft','/'):vals['sequence']=self.pool.get('ir.sequence').get(cr,uid,'CRM.Lead.Order.No',context) or '/'
        if not lead_obj.order_group:vals['order_group']=self.pool.get('panipat.order.group').create(cr,uid,{'partner_id':lead_obj.partner_id.id,'created_on':lead_obj.creation_date},context)
        employee_ids=map(int,self.browse(cr,uid,id).employee_line or [])
        self.pool.get('panipat.employee.schedule').create_employee_from_schedule(cr,uid,employee_ids,override_vals={'state':'confirm','origin':lead_obj.sequence or '/'},context=context)
        self.write(cr,uid,id,vals,context=None)
        if lead_obj.order_group:
            self.pool.get("panipat.order.group").write(cr,uid,lead_obj.order_group.id,{'custom_company':lead_obj.custom_company.id},context=context)
        return True
    
    def button_to_draft(self,cr,uid,id,context=None):
        self.write(cr, uid, id, {'state':'draft'}, context)
        return True
    
    def unlink(self,cr,uid,ids,context=None):
        for id in ids:
            obj=self.browse(cr, uid, id, context)
            if obj.state!='cancel':
                raise except_orm(('Error'),('Cancel the record before deleting it !!'))
        return super(panipat_crm_lead, self).unlink(cr,uid,ids,context)
    
    def button_cancel(self,cr,uid,id,context=None):
        obj=self.browse(cr, uid, id, context)
        if obj.install_id:
            if obj.install_id.state not in ('cancel'):
                raise except_orm(('Error'),('Cancel the Install Job %s before cancelling this record !!'%(obj.install_id.name_get()[0][1])))
            self.pool.get('panipat.install').unlink(cr,uid,obj.install_id.id,context)
        if obj.sale_order:
            if obj.sale_order.state not in ('cancel'):
                warning_id=self.pool.get('warning.wizard').create(cr,uid,{'sale_order':obj.sale_order.id},context=context)
                return {
                   'name': 'Warning Wizard',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'warning.wizard',
                    'type': 'ir.actions.act_window',
                    'res_id': warning_id,
                    'target':'new',
                    'context':{'check':'lead','form_view_ref':'panipat_handloom.warning_wizard_sale_view'}
               }
            else:
                self.pool.get('sale.order').unlink(cr,uid,[obj.sale_order.id],context=context)

        schedule_ids=map(int,obj.employee_line or [])
        self.pool.get('panipat.employee.schedule').cancel_employee_from_schedule(cr,uid,schedule_ids,context)
        self.pool.get('panipat.employee.schedule').delete_employee_from_schedule(cr,uid,schedule_ids,context)
        self.write(cr, uid, id, {'state':'cancel'}, context=context)
        return True

    def after_lead_cancel(self,cr,uid,id,context=None):
        obj=self.browse(cr, uid, id, context)
        if obj.sale_order:
            self.pool.get('sale.order').write(cr, uid, obj.sale_order.id,{'order_group':False}, context=context)
            self.write(cr, uid, id, {'sale_order':False}, context)
        
        schedule_ids=map(int,obj.employee_line or [])
        self.pool.get('panipat.employee.schedule').cancel_employee_from_schedule(cr,uid,schedule_ids,context)
        self.pool.get('panipat.employee.schedule').delete_employee_from_schedule(cr,uid,schedule_ids,context)
        self.write(cr, uid, id, {'state':'cancel'}, context=context)
        return True
    
    @api.one
    @api.depends('partner_id')    
    def _get_partner_details(self):
        for rec in self:
            if rec.partner_id:
                partner = rec.partner_id
                if partner.parent_id:
                    rec.partner_name = partner.parent_id.name
                elif partner.is_company:
                    rec.partner_name = partner.name
                else:
                    rec.partner_name = ''
                rec.contact_name = partner.name if partner.parent_id else False
                rec.title = partner.title and partner.title.id or False
                rec.street = partner.street
                rec.street2 = partner.street2
                rec.city = partner.city
                rec.state_id = partner.state_id and partner.state_id.id or False
                rec.country_id = partner.country_id and partner.country_id.id or False
                rec.email_from = partner.email
                rec.phone = partner.phone
                rec.mobile = partner.mobile
                rec.fax = partner.fax
                rec.zip = partner.zip
                rec.user_id = partner.user_id and partner.user_id.id or False

    @api.multi
    def write(self,vals):
        print "in write crm.lead self,vals--",self,vals
        for rec in self:
            if vals.get('creation_date',False):
                if rec.order_group:
                    rec.order_group.created_on=vals['creation_date']
        return_check = super(panipat_crm_lead, self).write(vals)
        for rec in self:
            if rec.state not in ('draft','cancel') and vals.get('employee_line'):
                rec.employee_line.cancel_employee_from_schedule()
                rec.employee_line.delete_employee_from_schedule()
                rec.employee_line.create_employee_from_schedule(override_vals={'state':'confirm','origin':rec.sequence or '/'})
                
        return return_check
                
                
    custom_company=fields.Many2one(comodel_name='res.company',string="Company",required=True,default=_get_custom_company_default)
    partner_name = fields.Char(compute='_get_partner_details',string="Company Name")
    partner_id = fields.Many2one('res.partner', 'Partner',track_visibility='onchange',
        select=True)
    name = fields.Char(string='Subject', select=1)
    email_from = fields.Char(compute='_get_partner_details',string='Email', size=128, help="Email address of the contact", select=1)
    creation_date = fields.Date('Creation Date',required=True,readonly=False)
    description = fields.Text('Internal Notes')
    contact_name = fields.Char(compute='_get_partner_details',string='Contact Name', size=64)
    priority = fields.Selection(selection=[('0', 'Very Low'),('1', 'Low'),('2', 'Normal'),('3', 'High'),('4', 'Very High')], string='Priority', select=True,default='2')
    user_id = fields.Many2one('hr.employee', 'Salesperson', select=True, track_visibility='onchange')
    product_line = fields.One2many('panipat.crm.product','crm_lead_id',string="Products",copy=True)
    employee_line = fields.One2many('panipat.employee.schedule','crm_lead_id',string="Employees for Measurement",copy=True)
    street = fields.Char(compute='_get_partner_details',string='Street')
    street2 = fields.Char(compute='_get_partner_details',string='Street2')
    zip = fields.Char(compute='_get_partner_details',string='Zip', change_default=True, size=24)
    city = fields.Char(compute='_get_partner_details',string='City')
    state_id = fields.Many2one(compute='_get_partner_details',comodel_name="res.country.state", string='State')
    country_id = fields.Many2one(compute='_get_partner_details',comodel_name='res.country', string='Country')
    phone = fields.Char(compute='_get_partner_details',string='Phone')
    fax = fields.Char(compute='_get_partner_details',string='Fax')
    mobile = fields.Char(compute='_get_partner_details',string='Mobile')
    title = fields.Many2one(compute='_get_partner_details',comodel_name='res.partner.title', string='Title')
    sequence = fields.Char(string="Order No.",copy=False,default='draft')
    state = fields.Selection(string="State",selection=[('draft','Draft'),('confirm','Confirm'),('quotation','Quotation'),('install','Install'),('cancel','Cancel')],copy=False,default='draft')
    total_paid_amount =fields.Float(compute='_get_amount_paid',string="Payment",default=00.00)
    order_group =fields.Many2one('panipat.order.group',string="Order Group",readonly=True,copy=False)
    sale_order=fields.Many2one(comodel_name="sale.order", string='Quotation',copy=False,readonly=True)
    install_id=fields.Many2one(comodel_name='panipat.install', string='Install Id',copy=False,readonly=True)
    client_order_ref=fields.Char('Buyer Order No./Ref', copy=False)

class panipat_crm_product(models.Model):
    _name = "panipat.crm.product"

    product_id = fields.Many2one('product.product',string="product")
    crm_lead_id = fields.Many2one('panipat.crm.lead')
    description = fields.Text(string="Description",required=True)
    hsn_code=fields.Many2one("hsn.code",string="HSN Code")
    sequence = fields.Integer(default=10)
    product_uom_qty=fields.Float(string="Qty",digits_compute= dp.get_precision('Product UoS'))
    product_uom=fields.Many2one(comodel_name='product.uom', string='Unit')
    sale_price = fields.Float('Unit Sale Price', digits_compute= dp.get_precision('Product Price'))
    

    _order='sequence'

    @api.onchange("product_id")
    def _onchange_product_id(self):
        description = self.product_id and self.product_id.name_get()[0][1] or ""
        #print "------description=====",description
        self.description = description
        self.product_uom=self.product_id.uom_id.id
        try:
            pricelist=self.pool.get('res.partner').default_get(self._cr, self._uid, ['property_product_pricelist'], context=self._context)['property_product_pricelist']
            abc=self.pool.get('sale.order.line').product_id_change(self._cr,self._uid,[],pricelist,self.product_service_id.id,partner_id=self.install_service_id.customer.id,context=self._context)
            #print "-=-=-abc-==-=",abc
            self.sale_price=abc['value']['price_unit']
        except:
            self.sale_price=self.product_id.lst_price


