# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import except_orm
from datetime import datetime
from openerp.tools.translate import _


class panipat_crm_lead(models.Model):
    _name = "panipat.crm.lead"
    _rec_name = 'sequence'
    
    
    def _get_amount_paid(self):
        amount_paid=0.0
        voucher_obj = self.env['account.voucher']
        for rec_self in self:
            voucher_recs = voucher_obj.search([('crm_lead_id','=',rec_self.id),('state','=','posted')])
            #print "voucher_ids-----------------------------",voucher_ids
            for obj in voucher_recs:
                amount_paid += obj.amount
            rec_self.total_paid_amount = amount_paid
        
    
    
    def lead_amount_paid_records(self,cr,uid,id,context=None):
        obj = self.browse(cr,uid,id,context=None)
        voucher_ids = self.pool.get('account.voucher').search(cr,uid,[('crm_lead_id','=',id[0])])
        if len(voucher_ids)==1:
            return {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'account.voucher',
                    'type': 'ir.actions.act_window',
                    'res_id': voucher_ids[0],
                    'context': {
                            'form_view_ref':'account_voucher.view_vendor_receipt_form',
                            'default_partner_id': obj.partner_id.parent_id.id if obj.partner_id.parent_id else obj.partner_id.id,
                            # customer payment only done by company if company exists for the contact
                            'crm_lead_id':obj.id,
                            'search_disable_custom_filters': False
                            }

                    }

        return {
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.voucher',
                'type': 'ir.actions.act_window',
                'domain':[('id','in',voucher_ids)],
                'context': {
                            'tree_view_ref':'account_voucher.view_voucher_tree',
                            'form_view_ref':'account_voucher.view_vendor_receipt_form',
                            'default_partner_id': obj.partner_id.parent_id.id if obj.partner_id.parent_id else obj.partner_id.id,
                            'crm_lead_id':obj.id,
                            'search_disable_custom_filters': False
                            }
                }
    
    def create(self,cr,uid,vals,context=None):

        if vals.get('sequence','/')=='/':
            print "in sequnece"
            vals['sequence']=self.pool.get('ir.sequence').get(cr,uid,'CRM.Lead.Order.No',context) or '/'
            vals['order_group'] = self.pool.get('panipat.order.group').create(cr,uid,{'partner_id':vals.get('partner_id',False)},context)
            print "========vals crm lead=====",vals
        return super(panipat_crm_lead,self).create(cr,uid,vals,context=None)
    
    def confirm_and_allocate(self,cr,uid,id,context=None):
        self.write(cr,uid,id,{'state':'employee'},context=None)
        carry_fields = self.read(cr,uid,id,['sequence','partner_id'],context=None)
        crm_id = carry_fields[0].pop('id')
        vals=carry_fields[0]
        if vals.get('partner_id',False) :
            vals['partner_id'] = vals.get('partner_id')[0]
        vals['sequence'] = crm_id
        vals.update({'state':'draft'})
        allocated_id=self.pool.get('crm.lead.allocated').create(cr,uid,vals,context=None)
        print "------------------------------",allocated_id
        return True

    def confirm_and_quote(self,cr,uid,id,context=None):
        self.write(cr,uid,id,{'state':'quotation'},context=None)
        return True
    
    def confirm_and_redesign(self,cr,uid,id,context=None):
        return True
    
    def confirm_and_install(self,cr,uid,id,context=None):
        return True
    
    def view_allocation_order(self,cr,uid,id,context=None):
        sequence=self.read(cr,uid,id,['sequence'],context=None)[0].get('sequence')
        allocated_ids=self.pool.get('crm.lead.allocated').search(cr,uid,[('sequence','=',sequence)],context=None)
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
    
    @api.depends('partner_id')    
    def _get_partner_details(self):
        for rec in self:
            if rec.partner_id:
                partner = rec.partner_id
                rec.partner_name = partner.parent_id.name if partner.parent_id else ''
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
    product_line = fields.One2many('panipat.crm.product','crm_lead_id',string="Products")
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
    order_group =fields.Many2one('panipat.order.group',string="Order Group")

