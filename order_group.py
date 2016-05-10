# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm
from datetime import datetime
from openerp.tools.translate import _

class panipat_order_group(models.Model):
    _name="panipat.order.group"
    _order='state desc,name'
    
    @api.one
    @api.depends()
    def _count_all(self):
        lead=self.env['panipat.crm.lead'].search([('order_group','=',self.id)])
        cust_inv_ids=[]
        supplier_inv_ids=[]
        po_count=[]
        if lead:
            self.lead_count=1
            
        if lead and lead[0].allocation_id.id:
            self.allocation_count=1
            
        if lead and lead[0]:
            sale_objs=self.env['sale.order'].search([('order_group','=',lead[0].order_group.id)])
            self.quotation_count=len(sale_objs)
            cust_inv_ids += [invoice.id for invoice in sale_objs.invoice_ids if invoice.id]
            
            for rec in sale_objs:
                if rec.procurement_group_id:
                    self._cr.execute('select distinct order_id from purchase_order_line where id in (select distinct purchase_line_id from procurement_order where group_id = %s and group_id is not null) and order_id is not null',(rec.procurement_group_id.id,))
                    po_count += self._cr.fetchall()
            self.purchase_order_count=len(po_count)
            po_ids = [i[0] for i in po_count if i[0]]
            for po in self.env['purchase.order'].browse(po_ids):
                supplier_inv_ids += [invoice.id for invoice in po.invoice_ids]

        if lead and lead[0]:
            install_objs=self.env['panipat.install'].search([('order_group','=',lead[0].order_group.id)])
            self.install_count=len(install_objs)
            cust_inv_ids += [rec.customer_invoice.id for rec in install_objs if rec.customer_invoice]
            supplier_inv_ids += [rec.supplier_invoice.id for rec in install_objs if rec.supplier_invoice]
        
        self.supplier_invoice_count=len(supplier_inv_ids)
        self.customer_invoice_count=len(cust_inv_ids)
            


    @api.multi
    def do_view_leads(self):
        lead_count=self.env['panipat.crm.lead'].search([('order_group','=',self.id)])
        if len(lead_count)==0:return True
        return{
               'view_type': 'form',
               'view_mode': 'form',
               'res_model': 'panipat.crm.lead',
               'type': 'ir.actions.act_window',
               'res_id': lead_count[0].id,
               }
            
    @api.multi
    def do_view_allocation(self):
        lead=self.env['panipat.crm.lead'].search([('order_group','=',self.id)])
        if lead and lead[0].allocation_id.id != False:
            return{
                   'view_type': 'form',
                   'view_mode': 'form',
                   'res_model': 'crm.lead.allocated',
                   'type': 'ir.actions.act_window',
                   'res_id': lead[0].allocation_id.id,
                   }
        return True
        
            
    @api.multi
    def do_view_quotation(self):
        lead=self.env['panipat.crm.lead'].search([('order_group','=',self.id)])
        if lead:
            sale_objs=self.env['sale.order'].search([('order_group','=',lead[0].order_group.id)])
            sale_ids=[]
            if sale_objs:
                sale_ids=[rec.id for rec in sale_objs]
                if len(sale_ids)==1:
                    return{
                       'view_type': 'form',
                       'view_mode': 'form',
                       'res_model': 'sale.order',
                       'type': 'ir.actions.act_window',
                       'res_id': sale_ids[0],
                       }
                if len(sale_ids)>1:
                    return{
                       'view_type': 'form',
                       'view_mode': 'tree,form',
                       'res_model': 'sale.order',
                       'type': 'ir.actions.act_window',
                       'domain':[('id','in',sale_ids)],
                       }
        return True
    
    @api.multi
    def do_view_install(self):
        lead=self.env['panipat.crm.lead'].search([('order_group','=',self.id)])
        if lead:
            install_objs=self.env['panipat.install'].search([('order_group','=',lead[0].order_group.id)])
            if install_objs:
                install_ids=[rec.id for rec in install_objs]
                if len(install_ids)==1:
                    return{
                           'view_type': 'form',
                           'view_mode': 'form',
                           'res_model': 'panipat.install',
                           'type': 'ir.actions.act_window',
                           'res_id': install_ids[0],
                           }
                if len(install_ids)>1:
                    return{
                           'view_type': 'form',
                           'view_mode': 'tree,form',
                           'res_model': 'panipat.install',
                           'type': 'ir.actions.act_window',
                           'domain':[('id','in',install_ids)],
                           }
        return True
            
        
    @api.multi
    def do_view_purchase_order(self):
        lead=self.env['panipat.crm.lead'].search([('order_group','=',self.id)])
        if lead:
            sale_objs=self.env['sale.order'].search([('order_group','=',lead[0].order_group.id)])
            po_ids=[]
            for rec in sale_objs:
                if rec.procurement_group_id.id:
                    self._cr.execute('select distinct order_id from purchase_order_line where id in (select distinct purchase_line_id from procurement_order where group_id = %s and group_id is not null) and order_id is not null',(rec.procurement_group_id.id,))
                    result_cr=self._cr.fetchall()
                    po_ids += [i[0] for i in result_cr if i[0]]
            if len(po_ids)==1:
                return{
                       'name':'Purchase',
                       'view_type': 'form',
                       'view_mode': 'form',
                       'res_model': 'purchase.order',
                       'type': 'ir.actions.act_window',
                       'res_id': po_ids[0],
                       }
            if len(po_ids)>1:
                return {
                        'name':'Purchases',
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        'res_model': 'purchase.order',
                        'type': 'ir.actions.act_window',
                        'domain':[('id','in',po_ids)],
                        }
        return True
        
    
    @api.multi
    def do_view_customer_invoice(self):
        lead=self.env['panipat.crm.lead'].search([('order_group','=',self.id)])
        if lead:
            install_objs=self.env['panipat.install'].search([('order_group','=',lead[0].order_group.id)])
            sale_objs=self.env['sale.order'].search([('order_group','=',lead[0].order_group.id)])
            cust_inv_ids = [invoice.id for invoice in sale_objs.invoice_ids if invoice.id]
            cust_inv_ids += [rec.customer_invoice.id for rec in install_objs if rec.customer_invoice]
            if len(cust_inv_ids)==1:
                return{
                       'name':'Invoice',
                       'view_type': 'form',
                       'view_mode': 'form',
                       'res_model': 'account.invoice',
                       'type': 'ir.actions.act_window',
                       'context':{'form_view_ref':'account.invoice_form',},
                       'res_id': cust_inv_ids[0],
                       }
            if len(cust_inv_ids)>1:
                return {
                        'name':'Invoice',
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        'res_model': 'account.invoice',
                        'type': 'ir.actions.act_window',
                        'context':{'form_view_ref':'account.invoice_form',
                                   'tree_view_ref':'account.action_invoice_tree1'},
                        'domain':[('id','in',cust_inv_ids)],
                        }
        return True
    
    
    @api.multi
    def do_view_supplier_invoice(self):
        lead=self.env['panipat.crm.lead'].search([('order_group','=',self.id)])
        if lead:
            sale_objs=self.env['sale.order'].search([('order_group','=',lead[0].order_group.id)])
            install_objs=self.env['panipat.install'].search([('order_group','=',lead[0].order_group.id)])
            po_ids=[]
            inv_ids = []
            inv_ids += [rec.supplier_invoice.id for rec in install_objs if rec.supplier_invoice]
            for rec in sale_objs:
                if rec.procurement_group_id.id:
                    self._cr.execute('select distinct order_id from purchase_order_line where id in (select distinct purchase_line_id from procurement_order where group_id = %s and group_id is not null) and order_id is not null',(rec.procurement_group_id.id,))
                    result_cr=self._cr.fetchall()
                    po_ids += [i[0] for i in result_cr if i[0]]
            for po in self.env['purchase.order'].browse(po_ids):
                inv_ids+= [invoice.id for invoice in po.invoice_ids]
            if len(inv_ids)==1:
                return{
                       'name':'Invoice',
                       'view_type': 'form',
                       'view_mode': 'form',
                       'res_model': 'account.invoice',
                       'type': 'ir.actions.act_window',
                       'context':{'form_view_ref':'account.invoice_supplier_form',},
                       'res_id': inv_ids[0],
                       }
            if len(inv_ids)>1:
                return {
                        'name':'Invoice',
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        'res_model': 'account.invoice',
                        'type': 'ir.actions.act_window',
                        'context':{'form_view_ref':'account.invoice_form',
                                   'tree_view_ref':'account.action_invoice_tree2'},
                        'domain':[('id','in',inv_ids)],
                        }
        return True
    
    @api.multi
    def button_done(self):
      self.state='done'
      return True
            
    name=fields.Char(string='Order Group',readonly=True,default="/",required=True)
    partner_id=fields.Many2one(comodel_name='res.partner', string='Partner',readonly=True)
    notes=fields.Text(string="Notes")
    lead_count=fields.Integer(compute='_count_all',default=0)
    allocation_count=fields.Integer(compute='_count_all',default=0)
    quotation_count=fields.Integer(compute='_count_all',default=0)
    install_count=fields.Integer(compute='_count_all',default=0)
    created_on=fields.Date(string='Created On',default=fields.Date.today())
    customer_invoice_count=fields.Integer(compute='_count_all',default=0)
    supplier_invoice_count=fields.Integer(compute='_count_all',default=0)
    purchase_order_count=fields.Integer(compute='_count_all',default=0)
    state = fields.Selection(string="State",selection=[('in_progress','Progress'),('done','Done')],default='in_progress',copy=False)
    
    
    @api.model
    def create(self,vals):
        if vals.get('name','/')=='/':
            vals['name']=self.env['ir.sequence'].get(code='panipat.order.group') or '/'
            print "=======vals panipat_order_group======",vals
        return super(panipat_order_group, self).create(vals)
    
    
    