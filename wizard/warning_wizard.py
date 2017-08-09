# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm

class warning_wizard(models.TransientModel):
    _name='warning.wizard'

    sale_order=fields.Many2one(comodel_name='sale.order', string='Sale Order',readonly=True,copy=False)
    customer_invoice=fields.Many2one(comodel_name='account.invoice',string='Customer Invoice',readonly=True,copy=False)
    supplier_invoice=fields.Many2one(comodel_name='account.invoice',string='Supplier Invoice',readonly=True,copy=False)
    commission_invoice=fields.Many2one(comodel_name='account.invoice',string='Commission Invoice',readonly=True,copy=False)
    
    def call_method(self,cr,uid,id,context=None):
        
        lead_obj=self.pool.get('panipat.crm.lead')
        if context.get('check',False)=='lead':
            return lead_obj.after_lead_cancel(cr,uid,context.get('active_id',False), context=context)
    
        install_obj=self.pool.get('panipat.install')
        if context.get('check',False)=='install':
            return install_obj.after_install_cancel(cr,uid,context.get('active_id',False),context=context)