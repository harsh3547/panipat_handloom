# -*- coding: utf-8 -*-
from openerp import models, fields, api ,osv

class procurement_order(osv.osv.osv):
    _inherit="procurement.order"
    
    # to deal with product reserve from stock when move is of type make_to_order in delivery order lines
    # basically clicking the 'check availability' and 'recheck availability' button in picking 
    
    def _run(self, cr, uid, procurement, context=None):
        print "-----in overidden _run=-=-=-=panipat.supplier_return-=-=-=-=-"
        if procurement.rule_id and procurement.rule_id.action == 'buy':
            #make a purchase order for the procurement
            customer_location = self.pool.get('res.partner').default_get(cr,uid,['property_stock_customer'],context)['property_stock_customer']
            if procurement.move_dest_id and procurement.move_dest_id.location_dest_id.id == customer_location:
                print "-in _get_po_line_values_from_proc--procurement.move_dest_id--",procurement.move_dest_id.id
                #procurement.move_dest_id.action_assign()
                stock_move_obj = self.pool.get('stock.move')
                proc_obj = self.pool.get('procurement.order')
                stock_move_obj.do_unreserve(cr, uid, [procurement.move_dest_id.id], context=context)
                stock_move_obj.action_assign(cr, uid,[procurement.move_dest_id.id], context=context)
                stock_id_obj=stock_move_obj.browse(cr,uid,procurement.move_dest_id.id,context)
                ordered_qty=stock_id_obj.product_uom_qty
                reserved_qty = 0
                for quant in stock_id_obj.reserved_quant_ids:
                    reserved_qty += quant.qty if quant.qty>0 else 0
                remaining_qty=ordered_qty-reserved_qty
                print "=====reserved_qty=,=ordered_qty==",reserved_qty,ordered_qty
                if remaining_qty==0:
                    print "=====reserved_qty=,=ordered_qty==",reserved_qty,ordered_qty
                    self.message_post(cr, uid, procurement.id, body=("Ordered Fulfilled From Stock"), context=context)
                    return False
                if remaining_qty>0:
                    self.write(cr,uid,procurement.id,{'product_qty':remaining_qty})
                    self.message_post(cr, uid, procurement.id, body=(str(reserved_qty)+procurement.product_uom.name+" Fulfilled From Stock"), context=context)
                    

            return self.make_po(cr, uid, [procurement.id], context=context)[procurement.id]
        return super(procurement_order, self)._run(cr, uid, procurement, context=context)

    
    