# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm
from datetime import datetime
from openerp.tools.translate import _

class panipat_order_group(models.Model):
    _name="panipat.order.group"
    _order='state desc,name desc'

    def _get_custom_company_default(self):
        value= self.env.user.company_id
        #print value
        return value

    @api.one
    @api.depends()
    def _count_all(self):
        lead=self.env['panipat.crm.lead'].search([('order_group','=',self.id)])
        cust_inv_ids=[]
        supplier_inv_ids=[]
        po_count=[]
        pick_ids=[]
        delivery_count=0
        incoming_shipment_count=0
        if lead:
            self.lead_count=1
            if lead[0].state not in ('draft','cancel'):
                self.lead_employee_count=len(map(int,lead[0].employee_line or []))
                self.lead_state=dict(lead[0]._columns['state'].selection).get(lead[0].state)
            
        if lead and lead[0]:
            sale_objs=self.env['sale.order'].search([('order_group','=',lead[0].order_group.id)])
            self.quotation_count=len(sale_objs)
            cust_inv_ids += [invoice.id for invoice in sale_objs.invoice_ids if invoice.id]
            
            for rec in sale_objs:
                if rec.procurement_group_id:
                    self._cr.execute('select distinct order_id from purchase_order_line where id in (select distinct purchase_line_id from procurement_order where group_id = %s and group_id is not null) and order_id is not null',(rec.procurement_group_id.id,))
                    po_count += self._cr.fetchall()
                    delivery_ids=self.env['stock.picking'].search([('group_id','=',rec.procurement_group_id.id)])
                    for rec1 in delivery_ids:
                        if rec1.picking_type_id.code=='outgoing':delivery_count+=1                    
            self.purchase_order_count=len(po_count)
            po_ids = [i[0] for i in po_count if i[0]]
            for po in self.env['purchase.order'].browse(po_ids):
                supplier_inv_ids += [invoice.id for invoice in po.invoice_ids]
                pick_ids += [picking.id for picking in po.picking_ids if picking.picking_type_id.code=='incoming']
        self.delivery_count=delivery_count
        self.incoming_shipment_count=len(pick_ids)

        if lead and lead[0]:
            install_objs=self.env['panipat.install'].search([('order_group','=',lead[0].order_group.id)])
            self.install_count=len(install_objs)
            commission_invoice_count=0
            for rec_comm in install_objs:
                if rec_comm.commission_invoice:
                    commission_invoice_count += 1
            self.commission_invoice_count=commission_invoice_count
            install_employee_count=0
            for rec in install_objs:
                if rec.state not in ('draft','cancel'):install_employee_count+=len(rec.employees)
            self.install_employee_count=install_employee_count
            cust_inv_ids += [rec.customer_invoice.id for rec in install_objs if (rec.customer_invoice and rec.customer_invoice.id not in cust_inv_ids)]
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
    def do_view_quotation(self):
        print "-=-=-=-context===",self._context
        lead=self.env['panipat.crm.lead'].search([('order_group','=',self.id)])
        if lead:
            sale_objs=self.env['sale.order'].search([('order_group','=',lead[0].order_group.id)])
            sale_ids=[]
            pick_ids=[]
            if sale_objs:
                if self._context.get("delivery_count",False):
                    for so in sale_objs:
                        pick_ids += [picking.id for picking in so.picking_ids if picking.picking_type_id.code=='outgoing']
                    if pick_ids:
                        if len(pick_ids)==1:
                            return {
                                   'name':'Delivery Order',
                                   'view_type': 'form',
                                   'view_mode': 'form',
                                   'res_model': 'stock.picking',
                                   'type': 'ir.actions.act_window',
                                   'res_id': pick_ids[0],
                                    }
                        if len(pick_ids)>1:
                            return {
                                   'name':'Delivery Orders',
                                   'view_type': 'form',
                                   'view_mode': 'tree,form',
                                   'res_model': 'stock.picking',
                                   'type': 'ir.actions.act_window',
                                   'domain':[('id','in',pick_ids)],
                                    }
                    else:return True
                
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
            pick_ids=[]
            for rec in sale_objs:
                if rec.procurement_group_id.id:
                    self._cr.execute('select distinct order_id from purchase_order_line where id in (select distinct purchase_line_id from procurement_order where group_id = %s and group_id is not null) and order_id is not null',(rec.procurement_group_id.id,))
                    result_cr=self._cr.fetchall()
                    po_ids += [i[0] for i in result_cr if i[0]]
            if self._context.get("incoming_shipment_count",False):
                for po in self.env['purchase.order'].browse(po_ids):
                    pick_ids += [picking.id for picking in po.picking_ids if picking.picking_type_id.code=='incoming']
                if pick_ids:
                    if len(pick_ids)==1:
                        return {
                               'name':'Incoming Shipments',
                               'view_type': 'form',
                               'view_mode': 'form',
                               'res_model': 'stock.picking',
                               'type': 'ir.actions.act_window',
                               'res_id': pick_ids[0],
                                }
                    if len(pick_ids)>1:
                        return {
                               'name':'Incoming Shipments',
                               'view_type': 'form',
                               'view_mode': 'tree,form',
                               'res_model': 'stock.picking',
                               'type': 'ir.actions.act_window',
                               'domain':[('id','in',pick_ids)],
                                }
                else:return True
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
    def do_view_commission_invoice(self):
        lead=self.env['panipat.crm.lead'].search([('order_group','=',self.id)])
        if lead:
            install_objs=self.env['panipat.install'].search([('order_group','=',lead[0].order_group.id)])
            if install_objs:
                commission_invoice_ids=[rec.commission_invoice.id for rec in install_objs if rec.commission_invoice.id]
                if len(commission_invoice_ids)==1:
                    return{
                       'name':'Invoice',
                       'view_type': 'form',
                       'view_mode': 'form',
                       'res_model': 'account.invoice',
                       'type': 'ir.actions.act_window',
                       'context':{'form_view_ref':'account.invoice_form',},
                       'res_id': commission_invoice_ids[0],
                       }
                if len(commission_invoice_ids)>1:
                    return {
                        'name':'Invoice',
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        'res_model': 'account.invoice',
                        'type': 'ir.actions.act_window',
                        'context':{'form_view_ref':'account.invoice_form',
                                   'tree_view_ref':'account.action_invoice_tree1'},
                        'domain':[('id','in',commission_invoice_ids)],
                        }
                    


        return True


    
    @api.multi
    def do_view_customer_invoice(self):
        lead=self.env['panipat.crm.lead'].search([('order_group','=',self.id)])
        if lead:
            install_objs=self.env['panipat.install'].search([('order_group','=',lead[0].order_group.id)])
            sale_objs=self.env['sale.order'].search([('order_group','=',lead[0].order_group.id)])
            cust_inv_ids = [invoice.id for invoice in sale_objs.invoice_ids if invoice.id]
            cust_inv_ids += [rec.customer_invoice.id for rec in install_objs if (rec.customer_invoice and rec.customer_invoice.id not in cust_inv_ids)]
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
    def do_view_lead_employee(self):
        lead=self.env['panipat.crm.lead'].search([('order_group','=',self.id)])
        if lead:
            if lead[0].state not in ('draft','cancel'):
                employee_ids=[rec.panipat_employee_link.id for rec in lead[0].employee_line if rec.panipat_employee_link]
                return{
                   'view_type': 'form',
                   'view_mode': 'tree,form',
                   'res_model': 'panipat.employee',
                   'type': 'ir.actions.act_window',
                   'domain':[('id','in',employee_ids)],
                   }
        return True
    
    @api.multi
    def do_view_install_employee(self):
        lead=self.env['panipat.crm.lead'].search([('order_group','=',self.id)])
        if lead:
            install_objs=self.env['panipat.install'].search([('order_group','=',lead[0].order_group.id)])
            employee_ids=[]
            if install_objs:
                for rec in install_objs:
                    if rec.state not in ('draft','cancel'):
                        for emp in rec.employees:
                            if emp.panipat_employee_link:employee_ids.append(emp.panipat_employee_link.id)
                
                if employee_ids:return{
                                       'view_type': 'form',
                                       'view_mode': 'tree,form',
                                       'res_model': 'panipat.employee',
                                       'type': 'ir.actions.act_window',
                                       'domain':[('id','in',employee_ids)],
                                       }
        return True
            
    @api.multi
    def unlink(self):
        raise except_orm(_('Error!'), _('You cannot delete a order group. PLS CANCEL the ORDER GROUP'))
        return super(panipat_order_group, self).unlink()
    
    @api.multi
    def button_cancel(self):
        self.state='cancel'
        return True
    
    @api.multi
    def button_done(self):
        self.state='done'
        return True
  
    @api.multi
    def button_progress(self):
        self.state='in_progress'
        return True
            
    name=fields.Char(string='Order Group',readonly=True,default="/",required=True)
    partner_id=fields.Many2one(comodel_name='res.partner', string='Partner',readonly=True)
    notes=fields.Text(string="Notes")
    lead_employee_count=fields.Integer(compute='_count_all',default=0)
    install_employee_count=fields.Integer(compute='_count_all',default=0)
    lead_count=fields.Integer(compute='_count_all',default=0)
    lead_state=fields.Char(compute='_count_all',default='')
    quotation_count=fields.Integer(compute='_count_all',default=0)
    delivery_count=fields.Integer(compute='_count_all',default=0)
    incoming_shipment_count=fields.Integer(compute='_count_all',default=0)
    install_count=fields.Integer(compute='_count_all',default=0)
    created_on=fields.Date(string='Created On',default=fields.Date.today())
    customer_invoice_count=fields.Integer(compute='_count_all',default=0)
    commission_invoice_count=fields.Integer(compute='_count_all',default=0)
    supplier_invoice_count=fields.Integer(compute='_count_all',default=0)
    purchase_order_count=fields.Integer(compute='_count_all',default=0)
    state = fields.Selection(string="State",selection=[('in_progress','Progress'),('done','Done'),('cancel','Cancel')],default='in_progress',copy=False)
    custom_company=fields.Many2one(comodel_name='res.company',string="Company",required=True,default=_get_custom_company_default)
        
    
    @api.model
    def create(self,vals):
        if vals.get('name','/')=='/':
            vals['name']=self.env['ir.sequence'].get(code='panipat.order.group') or '/'
            print "=======vals panipat_order_group======",vals
        return super(panipat_order_group, self).create(vals)
    
    
    