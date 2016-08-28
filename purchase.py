# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm
from datetime import datetime
from openerp.tools.translate import _

class purchase_order(models.Model):
    _inherit = "purchase.order"

    @api.one
    @api.depends()
    def _get_order_group(self):
        try:
            self._cr.execute("select order_group from sale_order where procurement_group_id in (select distinct group_id from procurement_order where purchase_line_id in (select id from purchase_order_line where order_id=%s))",(self.id,))
            ans=self._cr.fetchall()
            self.order_group=ans[0][0] if ans else False
        except:
            self.order_group=False

    order_group=fields.Many2one(compute="_get_order_group",comodel_name='panipat.order.group', string="Order Group")
    


    