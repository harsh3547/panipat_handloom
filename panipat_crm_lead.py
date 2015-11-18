# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm
from datetime import datetime
from openerp.tools.translate import _

class panipat_crm_lead(models.Model):
    _name = "panipat.crm.lead"
    _rec_name = 'sequence'
    
    
    def _get_amount_paid(self):
        amount_paid=0.0
        #voucher_obj = self.env['account.voucher']
        for rec_self in self:
            #voucher_recs = voucher_obj.search([('partner_id','=',rec_self.partner_id.parent_id.id if rec_self.partner_id.parent_id else rec_self.partner_id.id),('state','=','posted')])
            #print "voucher_ids-----------------------------",voucher_ids
            #for obj in voucher_recs:
            #    amount_paid += obj.amount
            rec_self.total_paid_amount = -1*rec_self.partner_id.credit if rec_self.partner_id and rec_self.partner_id.credit else 0.00
        
    
    
    def lead_amount_paid_records(self,cr,uid,id,context=None):
        obj = self.browse(cr,uid,id,context=None)
        #voucher_ids = self.pool.get('account.voucher').search(cr,uid,[('partner_id','=',obj.partner_id.parent_id.id if obj.partner_id.parent_id else obj.partner_id.id)])
        #if len(voucher_ids)==1:
        return {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'account.voucher',
                    'type': 'ir.actions.act_window',
                    #'res_id': voucher_ids[0],
                    'context': {
                            'form_view_ref':'account_voucher.view_vendor_receipt_form',
                            'default_partner_id': obj.partner_id.parent_id.id if obj.partner_id.parent_id else obj.partner_id.id,
                            # customer payment only done by company if company exists for the contact
                            'default_name':obj.sequence+':'+obj.order_group.name,
                            'order_group':obj.order_group.id,
                            'search_disable_custom_filters': False
                            }

                    }

        '''return {
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.voucher',
                'type': 'ir.actions.act_window',
                'domain':[('id','in',voucher_ids)],
                'context': {
                            'tree_view_ref':'account_voucher.view_voucher_tree',
                            'form_view_ref':'account_voucher.view_vendor_receipt_form',
                            'default_partner_id': obj.partner_id.parent_id.id if obj.partner_id.parent_id else obj.partner_id.id,
                            'order_group':obj.order_group.id,
                            'default_name':obj.sequence+':'+obj.order_group.name,
                            'search_disable_custom_filters': False
                            }
                }'''
    
    def create(self,cr,uid,vals,context=None):

        if vals.get('sequence','/')=='/':
            print "in sequnece"
            vals['sequence']=self.pool.get('ir.sequence').get(cr,uid,'CRM.Lead.Order.No',context) or '/'
            vals['order_group'] = self.pool.get('panipat.order.group').create(cr,uid,{'partner_id':vals.get('partner_id',False)},context)
            print "========vals crm lead=====",vals
        return super(panipat_crm_lead,self).create(cr,uid,vals,context=None)
    
    def confirm_and_allocate(self,cr,uid,id,context=None):
        self.write(cr,uid,id,{'state':'employee'},context=None)
        carry_fields = self.browse(cr,uid,id,context=None)
        vals = {'partner_id':carry_fields.partner_id.id,'order_group':carry_fields.order_group.id}
        allocated_id=self.pool.get('crm.lead.allocated').create(cr,uid,vals,context=None)
        return True

    def view_allocation_order(self,cr,uid,id,context=None):
        order_group=self.browse(cr,uid,id,context=None).order_group.id
        allocated_ids=self.pool.get('crm.lead.allocated').search(cr,uid,[('order_group','=',order_group)],context=None)
        if allocated_ids :
            if len(allocated_ids) == 1 :
                return {
                'name': 'CRM - Leads Allocated Form',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'crm.lead.allocated',
                'type': 'ir.actions.act_window',
                'res_id': allocated_ids[0],
                }
            else :
                return {
                'name': 'CRM - Leads Allocated Form',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'crm.lead.allocated',
                'type': 'ir.actions.act_window',
                'domain':[('id','in',allocated_ids)],
                }
        else :
            return {
                    'type': 'ir.actions.client',
                    'tag': 'action_warn',
                    'name': 'Warning',
                    'params': {
                               'title': 'Warning!',
                               'text': 'Allocated Lead is not available .',
                               }
                    }
    


    def confirm_and_quote(self,cr,uid,id,context=None):
        lead_obj = self.browse(cr,uid,id,context)
        values=[]
        vals={}
        if lead_obj.product_line :
            for i in lead_obj.product_line :
                values.append((0,0,{'product_id':i.product_id.id,
                                    'name':i.description or self.pool.get('product.product').name_get(cr,uid,[i.product_id.id],context=context)[0][1] or "",
                                    }))
            vals.update({'order_line':values})
                
        if lead_obj.partner_id and lead_obj.partner_id.id:
            vals.update({'partner_id':lead_obj.partner_id.id})  
        vals['order_group'] = lead_obj.order_group.id
        print "---------vals in make_qutaion crm.lead.allocated==========",vals
        quotation_id = self.pool.get('sale.order').create(cr,uid,vals,context=None)
        self.write(cr,uid,id,{'state':'quotation'},context=None)
        return True
    
    
    def view_quotation(self,cr,uid,id,context=None):
        vals = {}
        order_group = self.browse(cr,uid,id,context=None).order_group.id
        sale_ids = self.pool.get('sale.order').search(cr,uid,[('order_group','=',order_group)],context=None)
        if sale_ids :
            if len(sale_ids) == 1 :
                return {
                'name': 'Sale Order Form',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window',
                'res_id': sale_ids[0],
                }
            else :
                return {
                'name': 'Sale Order Form',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window',
                'domain':[('id','in',sale_ids)],
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
            



    def confirm_and_redesign(self,cr,uid,id,context=None):
        self.write(cr,uid,id,{'state':'redesign'},context=None)
        return True
    
    def confirm_and_install(self,cr,uid,id,context=None):
        self.write(cr,uid,id,{'state':'install'},context=None)
        return True
    
    
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

    
    
    partner_name = fields.Char(compute='_get_partner_details',string="Company Name")
    partner_id = fields.Many2one('res.partner', 'Partner', ondelete='set null', track_visibility='onchange',
        select=True, required=True)
    name = fields.Char(string='Subject', select=1)
    email_from = fields.Char(compute='_get_partner_details',string='Email', size=128, help="Email address of the contact", select=1)
    create_date = fields.Datetime('Creation Date', readonly=True,default=fields.Datetime.now)
    description = fields.Text('Internal Notes')
    contact_name = fields.Char(compute='_get_partner_details',string='Contact Name', size=64)
    priority = fields.Selection(selection=[('0', 'Very Low'),('1', 'Low'),('2', 'Normal'),('3', 'High'),('4', 'Very High')], string='Priority', select=True,default='2')
    user_id = fields.Many2one('res.users', 'Salesperson', select=True, track_visibility='onchange')
    current_date = fields.Datetime('Date',Readonly=True)
    product_line = fields.One2many('panipat.crm.product','crm_lead_id',string="Products",copy=True)
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
    sequence = fields.Char(string="Order No.",copy=False,default='/')
    state = fields.Selection(string="State",selection=[('draft','Draft'),('employee','Employee Allocated'),('quotation','Quotation'),('redesign','Redesign'),('install','Install'),('cancel','Cancel')],copy=False,default='draft')
    total_paid_amount =fields.Float(compute='_get_amount_paid',string="Payment",default=00.00)
    order_group =fields.Many2one('panipat.order.group',string="Order Group",readonly=True)

