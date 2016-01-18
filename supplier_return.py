# -*- coding: utf-8 -*-
from openerp import models, fields, api ,osv
from openerp.exceptions import except_orm
from datetime import datetime

'''class stock_picking(models.Model):
    _inherit="stock.picking"
    
    def _search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False, access_rights_uid=None):
        print "==== in search ===args,context= in stock_picking****==",self,args,context
        ids= super(stock_picking,self)._search(cr, user, args, offset, limit, order, context, count, access_rights_uid)
        print "in search of stock_picking returnig ids ",ids
        return ids
'''
    
class stock_transfer_details_items(models.TransientModel):
    _inherit = 'stock.transfer_details_items'

    back_to_supplier=fields.Boolean('Return To Supplier',default=False,copy=False)
    
    
class stock_transfer_details(models.TransientModel):
    _inherit = 'stock.transfer_details'
    
    # https://www.odoo.com/documentation/8.0/reference/views.html#reference-views-inheritance
    @api.multi
    def wizard_view(self):
        res = super(stock_transfer_details, self).wizard_view()
        if self.picking_id.picking_type_id.id==self.env.ref('panipat_handloom.picking_type_customer_return').id:
            view = self.env.ref('panipat_handloom.panipat_back_to_supplier_wizard_view')
            res['views']=[(view.id, 'form')]
            res['view_id']=view.id
        print res
        return res
    
    @api.one
    def do_detailed_transfer(self):
        print self._context
        res = super(stock_transfer_details, self).do_detailed_transfer()
        if not res:return res
        supplier_location = self.pool.get('res.partner').default_get(self._cr,self._uid,['property_stock_supplier'],self._context)['property_stock_supplier']
        data = []
        stock_location = self.env.ref("stock.warehouse0").lot_stock_id.id
        for item in self.item_ids:
            if item.back_to_supplier:
                if item.packop_id and item.packop_id.linked_move_operation_ids:
                    for op in item.packop_id.linked_move_operation_ids:
                        done=False
                        if op.reserved_quant_id:
                            for history_move in op.reserved_quant_id.history_ids:
                                print history_move
                                if history_move.location_id.id == supplier_location and history_move.location_dest_id.id == stock_location:
                                    if history_move.picking_id and history_move.picking_id.partner_id:
                                        final_qty=self.pool.get('product.uom')._compute_qty(self._cr,self._uid,op.move_id.product_uom.id,op.qty,history_move.product_uom.id)
                                        data=self.add_partner_product_qty(history_move.picking_id.partner_id.id,op.move_id.product_id.id,history_move.product_uom.id,final_qty,data)
                                        done=True
                                        break
                        if not done:
                            self._cr.execute("select name from product_supplierinfo where product_tmpl_id=%s order by sequence limit 1",(op.move_id.product_id.product_tmpl_id.id,))
                            check=self._cr.fetchall()
                            ans = check[0][0] if check else False
                            final_qty=self.pool.get('product.uom')._compute_qty(self._cr,self._uid,op.move_id.product_uom.id,op.qty,op.move_id.product_id.uom_po_id.id)
                            data=self.add_partner_product_qty(ans,op.move_id.product_id.id,op.move_id.product_id.uom_po_id.id,final_qty,data)
                                
                else:
                    self._cr.execute("select name from product_supplierinfo where product_tmpl_id=%s order by sequence limit 1",(op.move_id.product_id.product_tmpl_id.id,))
                    check=self._cr.fetchall()
                    ans = check[0][0] if check else False
                    final_qty=self.pool.get('product.uom')._compute_qty(self._cr,self._uid,item.product_uom_id.id,item.quantity,item.product_id.uom_po_id.id)
                    data=self.add_partner_product_qty(ans,item.product_id.id,item.product_id.uom_po_id.id,final_qty,data)
        
        stock_pick_obj=self.env['stock.picking'].browse(self._context.get('active_id',False))
        for rec in data:
            picking_id=self.env['stock.picking'].create({
                             'partner_id':rec[0],
                             'origin':stock_pick_obj.name+":"+stock_pick_obj.origin,
                             'move_type':'direct',
                             'invoice_state':'2binvoiced',
                             'group_id':stock_pick_obj.group_id.id,
                             'picking_type_id':self.env.ref('panipat_handloom.picking_type_supplier_return').id
                             })
            for rec2 in rec[1]:
                self.env['stock.move'].create({'name':self.env['product.product'].browse(rec2[0]).name,
                                               'picking_id':picking_id.id,
                                               'product_id':rec2[0],
                                               'procure_method':'make_to_stock',
                                               'product_uom_qty':rec2[2],
                                               'product_uom':rec2[1],
                                               'location_id':stock_location,
                                               'location_dest_id':supplier_location,
                                               'group_id':stock_pick_obj.group_id.id,
                                               'invoice_state':'2binvoiced',
                                               'propagate':True,
                                               })
        return res


    def add_partner_product_qty(self,partner,product_id,product_uom_id,qty,data=[]):
        partner_in=False
        for rec in data:
            if rec[0]==partner:
                partner_in=True
                product_in=False
                for rec2 in rec[1]:
                    if product_id==rec2[0] and product_uom_id==rec2[1]:
                        product_in=True
                        rec2[2] += qty
                if not product_in:
                    rec[1].append([product_id,product_uom_id,qty])    
        if not partner_in:
            data.append([partner,[[product_id,product_uom_id,qty]]])
        return data
                

