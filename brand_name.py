# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm
from datetime import datetime
from openerp.tools.translate import _

class panipat_brand_name(models.Model):
    _name='panipat.brand.name'
    
    name=fields.Char('Brand Name',required=True)
    barcode_no=fields.Char('Barcode Prefix',readonly=True,copy=False)
    seq=fields.Many2one(comodel_name='ir.sequence', string="Sequence",readonly=True,copy=False)
    product_ids = fields.One2many('product.template','panipat_brand_name',string='Brand Products',)
    products_count = fields.Integer(string='Number of products',compute='_get_products_count',)
    vol_ids=fields.One2many(comodel_name='panipat.brand.vol', inverse_name="panipat_brand_name", string="Files / Volumes")
    vol_count=fields.Integer(string="Number Of Files",compute="_get_vol_count",store=True)
    _sql_constraints = [('name_uniq','UNIQUE (name)','Brand Name must be unique!')]
    seq1=fields.Integer()
    
    @api.depends('product_ids')
    def _get_products_count(self):
        for rec in self:
            rec.products_count = len(rec.product_ids)
    
    @api.depends('vol_ids')
    def _get_vol_count(self):
        #print "=-=-="
        for rec in self:
            rec.vol_count=len(rec.vol_ids)
            
    @api.model
    def create(self,vals):
        vals['barcode_no']=self.env['ir.sequence'].get(code="panipat.1")
        vals_seq={'name':vals['name'], 'active':True, 'padding':3}
        vals['seq']=self.env['ir.sequence'].create(vals_seq).id
        return super(panipat_brand_name, self).create(vals)
    
    @api.multi
    def unlink(self):
        seq_id=self.seq
        ans = super(panipat_brand_name, self).unlink()
        seq_id.unlink()
        return ans
    
class panipat_brand_vol(models.Model):
    _name='panipat.brand.vol'
    
    panipat_brand_name=fields.Many2one(comodel_name='panipat.brand.name', string='Brand Name',required=True)
    name=fields.Char('Vol/File No.')
        