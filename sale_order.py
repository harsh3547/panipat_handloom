# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm
from datetime import datetime
from openerp.tools.translate import _


class sale_order(models.Model):
    _inherit = "sale.order"
    
    order_group = fields.Many2one(comodel_name='panipat.order.group', string="Order Group")