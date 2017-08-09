# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm
from datetime import datetime

class stock_move(models.Model):
    _inherit="stock.move"

    def _get_invoice_line_vals(self, cr, uid, move, partner, inv_type, context=None):
        
        res = super(stock_move, self)._get_invoice_line_vals(cr, uid, move, partner, inv_type, context)
        #print "===in panipat handloom stock_move _get_invoice_line_vals===res=",res
        print "===in _get_invoice_line_vals==res_old=",res
        if res.get('name',False):
            name_old=self.pool.get('product.product').name_get(cr, uid, [move.product_id.id], context=context)
            if name_old and name_old[0][1]==res['name']:
                ctx=context.copy()
                ctx['cust_inv_name_get']=True
                name_new=self.pool.get('product.product').name_get(cr, uid, [move.product_id.id], context=ctx)
                if name_new:
                    res['name'] = name_new[0][1]
        print "===in _get_invoice_line_vals==res_new=",res
        return res
    