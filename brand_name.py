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
    
    _sql_constraints = [('name_uniq','UNIQUE (name)','Brand Name must be unique!')]
    
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