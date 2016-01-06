# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm
from datetime import datetime
from openerp.tools.translate import _

class panipat_install(models.Model):
    _name="panipat.install"
    
    name=fields.Char(readonly=True,default='/',string='Name')
    supplier=fields.Many2one(comodel_name='res.partner', string='Contractor',required=True,domain=[('supplier', '=', True)])
    customer=fields.Many2one(comodel_name='res.partner', string='For Customer',domain=[('customer', '=', True)])
    date=fields.Date(string='Date',default=fields.Date.today())
    procurement_group=fields.Many2one(comodel_name='procurement.group')
    order_group=fields.Many2one(comodel_name='panipat.order.group', string='Order Group',readonly=True)
    install_lines=fields.One2many(comodel_name="panipat.install.lines", inverse_name="install_id", string='Order Lines')
    
class panipat_install_lines(models.Model):
    _name="panipat.install.lines"
    
    install_id=fields.Many2one(comodel_name='panipat.install', copy=False)
    product_id=fields.Many2one(comodel_name='product.product', string='Product')
    
