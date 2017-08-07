##############################################################################

import time

from openerp.report import report_sxw
from openerp.tools.translate import _
from openerp.osv import osv
from openerp.tools.amount_to_text_en import amount_to_text
from openerp.tools.float_utils import float_round, float_compare
import string

class order_group_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        print "-=-=-=-order_group_report init=-=-=-",self
        super(order_group_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update( {
            'time': time,
            'round_off_fmt':self._round_off_fmt,
            'lead_obj':self._get_lead_obj,
            'sale_obj':self._get_sale_obj,
            'delivery_obj':self._get_delivery_obj,
            'purchase_obj':self._get_purchase_obj,
            'incoming_obj':self._get_incoming_obj,
            'install_obj':self._get_install_obj,
            'custinv_obj':self._get_custinv_obj,
            'supplierinv_obj':self._get_supplier_obj,
        })
        self.context = context

    def _get_lead_obj(self,id,context=None):
        lead_id=self.pool.get('panipat.order.group').do_view_leads(self.cr,self.uid,id,context=context)
        #print "lead-----id---",lead_id,id
        if lead_id and type(lead_id) is dict and lead_id.get('res_id',False):
            lead_obj=self.pool.get('panipat.crm.lead').browse(self.cr,self.uid,lead_id.get('res_id',False),context=context)
            if lead_obj:return lead_obj
        return False

    def _get_install_obj(self,id,context=None):
        install_ids=self.pool.get('panipat.install').search(self.cr,self.uid,[('order_group','=',id)])
        install_objs=self.pool.get('panipat.install').browse(self.cr,self.uid,install_ids,context=context)
        if install_objs:return install_objs
        else: return False

    def _get_sale_obj(self,id,context=None):
        sale_ids=self.pool.get('sale.order').search(self.cr,self.uid,[('order_group','=',id)])
        sale_objs=self.pool.get('sale.order').browse(self.cr,self.uid,sale_ids,context=context)
        if sale_objs:return sale_objs
        else: return False

    def _get_custinv_obj(self,id,context=None):
        #print "----in cust inv-----",id
        cust_and_commission_ids=[]
        custinv=self.pool.get('panipat.order.group').do_view_customer_invoice(self.cr,self.uid,id,context=context)

        if custinv and type(custinv) is dict and (custinv.get('res_id',False) or custinv.get('domain',False)):
            cust_and_commission_ids=[custinv.get('res_id',False)] if custinv.get('res_id',False) else custinv.get('domain',[(0,0,[])])[0][2]

        commissioninv=self.pool.get('panipat.order.group').do_view_commission_invoice(self.cr,self.uid,id,context=context)
        if commissioninv and type(commissioninv) is dict and (commissioninv.get('res_id',False) or commissioninv.get('domain',False)):
            cust_and_commission_ids += [commissioninv.get('res_id',False)] if commissioninv.get('res_id',False) else commissioninv.get('domain',[(0,0,[])])[0][2]

        if cust_and_commission_ids:
            cust_and_comm_inv_obj=self.pool.get('account.invoice').browse(self.cr,self.uid,cust_and_commission_ids,context=context)
            if cust_and_comm_inv_obj:return cust_and_comm_inv_obj


        #print "--------false-------"
        return False

    def _get_supplier_obj(self,id,context=None):
        #print "----in supplier inv-----",id
        supplierinv=self.pool.get('panipat.order.group').do_view_supplier_invoice(self.cr,self.uid,id,context=context)
        if supplierinv and type(supplierinv) is dict and (supplierinv.get('res_id',False) or supplierinv.get('domain',False)):
            supplierinv_obj=self.pool.get('account.invoice').browse(self.cr,self.uid,supplierinv.get('res_id',False) or supplierinv.get('domain',[(0,0,False)])[0][2],context=context)
            #print "----suplier_inv----",supplierinv_obj
            if supplierinv_obj:return supplierinv_obj
        #print "--------false-------"
        return False

    def _get_delivery_obj(self,sale_obj,context=None):
        pick_objs=[]
        pick_objs += [picking for picking in sale_obj.picking_ids if picking.picking_type_id.code=='outgoing']
        if pick_objs:return pick_objs
        else: return False

    def _get_incoming_obj(self,po_obj,context=None):
        pick_objs=[]
        pick_objs += [picking for picking in po_obj.picking_ids if picking.picking_type_id.code=='incoming']
        if pick_objs:return pick_objs
        else: return False

    def _get_purchase_obj(self,id,context=None):
        purchase=self.pool.get('panipat.order.group').do_view_purchase_order(self.cr,self.uid,id,context=context)
        #print "purchase---",purchase
        if purchase and type(purchase) is dict and (purchase.get('res_id',False) or purchase.get('domain',False)):
            purchase_obj=self.pool.get('purchase.order').browse(self.cr,self.uid,purchase.get('res_id',False) or purchase.get('domain',[(0,0,False)])[0][2],context=context)
            if purchase_obj:return purchase_obj
        return False
    
    def _round_off_fmt(self,round_off,context=None):
        prec=self.pool.get('decimal.precision').precision_get(self.cr, self.uid, 'Account')
        round_off_fmt = "%.{0}f".format(prec)%round_off
        return round_off_fmt
        

class order_group_report_class(osv.AbstractModel):
    _name = 'report.panipat_handloom.order_group_report'
    _inherit = 'report.abstract_report'
    _template = 'panipat_handloom.order_group_report'
    _wrapped_report_class = order_group_report


