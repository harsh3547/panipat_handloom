# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm
from datetime import datetime

    
class stock_invoice_onshipping(models.TransientModel):
    _inherit="stock.invoice.onshipping"
    
    @api.multi
    def create_invoice(self):
        print self._context
        res=super(stock_invoice_onshipping, self).create_invoice()
        print "=========in panipat handloom======",res
        inv_obj=self.env['account.invoice'].browse(res)
        origin_picking=self.env['stock.picking'].browse(self._context.get('active_id')).origin
        if origin_picking:
            inv_obj.write({'origin':origin_picking+":"+inv_obj.origin})
        return res


