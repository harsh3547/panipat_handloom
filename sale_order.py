# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm
from datetime import datetime
from openerp.tools.translate import _

class sale_order(models.Model):
    _inherit = "sale.order"
    
    order_group = fields.Many2one(comodel_name='panipat.order.group', string="Order Group")

    def do_view_po(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display the Purchase order related to this sales order
        '''
        
        cr.execute('select distinct order_id from purchase_order_line where id in (select distinct purchase_line_id from procurement_order where group_id in (select distinct procurement_group_id from sale_order where id in %s))',(tuple(ids),))
        result_cr=cr.fetchall()
        print "query==============",result_cr
        po_ids=[i[0] for i in result_cr if i[0]]
        print "ids=========",po_ids
        if len(po_ids)==1:
            return{
                   'name':'Purchase',
                   'view_type': 'form',
                   'view_mode': 'form',
                   'res_model': 'purchase.order',
                   'type': 'ir.actions.act_window',
                   'res_id': po_ids[0],
                   }
        else:
            return {
                    'name':'Purchases',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'purchase.order',
                    'type': 'ir.actions.act_window',
                    'domain':[('id','in',po_ids)],
                    }
        
        
    def do_view_pickings_sale(self, cr, uid, ids, context=None):
        if not context:context={}
        '''
        This function returns an action that display the pickings of the procurements belonging
        to the same procurement group of given ids.
        '''
        obj = self.browse(cr,uid,ids,context=None)
        group_ids = list(set([proc.procurement_group_id.id for proc in obj if proc.procurement_group_id]))
        picking_ids=self.pool.get('stock.picking').search(cr,uid,[('group_id','in',group_ids)])
        if len(picking_ids)==1:
            return{
                   'view_type': 'form',
                   'view_mode': 'form',
                   'res_model': 'stock.picking',
                   'type': 'ir.actions.act_window',
                   'res_id': picking_ids[0],
                   }
        else:
            return {
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'stock.picking',
                    'type': 'ir.actions.act_window',
                    'domain':[('id','in',picking_ids)],
                    }
        
        
    @api.one
    @api.depends()
    def _count_all(self):
        cr=self._cr
        print "====================== in _count_all"
        group_id=False
        if self.procurement_group_id:group_id=[self.procurement_group_id.id]
        if group_id:
            cr.execute('select distinct order_id from purchase_order_line where id in (select distinct purchase_line_id from procurement_order where group_id = %s and group_id is not null) and order_id is not null',(group_id))
            po_count=cr.fetchall()
            print "po_count============",po_count
            self.po_count=len(po_count)
            
            cr.execute('select distinct id from stock_picking where group_id = %s and id is not null',(group_id))
            picking_count=cr.fetchall()
            print "picking_count============",picking_count
            self.picking_count=len(picking_count)
    
    def _get_amount_paid(self):
        #print "========in _get_amount_paid====="
        amount_paid=0.0
        #voucher_obj = self.env['account.voucher']
        for rec_self in self:
            #voucher_recs = voucher_obj.search([('partner_id','=',rec_self.partner_id.parent_id.id if rec_self.partner_id.parent_id else rec_self.partner_id.id),('state','=','posted')])
            #print "voucher_ids-----------------------------",voucher_recs
            #for obj in voucher_recs:
            #    amount_paid += obj.amount
            rec_self.total_paid_amount = -1*rec_self.partner_id.credit if rec_self.partner_id and rec_self.partner_id.credit and rec_self.partner_id.credit<=0 else 0.00
    
    
    def total_amount_paid_records(self,cr,uid,id,context=None):
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
                            'default_name':obj.name+':'+obj.order_group.name if obj.order_group else obj.name,
                            'order_group':obj.order_group and obj.order_group.id or False,
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
                            'order_group':obj.order_group and obj.order_group.id or False,
                            'default_name':obj.name+':'+obj.order_group.name if obj.order_group else obj.name,
                            'search_disable_custom_filters': False
                            }
                }'''
    



    po_count=fields.Integer(compute='_count_all')
    picking_count=fields.Char(compute='_count_all')
    total_paid_amount =fields.Float(compute='_get_amount_paid',string="Payment")
    
    