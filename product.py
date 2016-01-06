# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm
from datetime import datetime
from openerp.tools.translate import _
import math


def ean_checksum(eancode):
    """returns the check value of an ean string of length 12, returns -1 if the string has the wrong length"""
    if len(eancode) != 12:
        return -1
    oddsum=0
    evensum=0
    total=0
    eanvalue=eancode
    finalean=eanvalue[::-1]
    print finalean
    for i in range(len(finalean)):
        if i % 2 == 0:
            oddsum += int(finalean[i])
        else:
            evensum += int(finalean[i])
    total=(oddsum * 3) + evensum

    check = int(10 - math.ceil(total % 10.0)) %10
    return check

    
class product_template(models.Model):
    _inherit='product.template'

    panipat_brand_name=fields.Many2one(comodel_name='panipat.brand.name', string='Brand Name')
    ean13=fields.Char(readonly=True,copy=False)
    default_code=fields.Char(readonly=True,copy=False)
    
    
class product_product(models.Model):
    _inherit="product.product"
    
    ean13=fields.Char(readonly=True)
    default_code=fields.Char(readonly=True)
    
    def get_valid_ean(self,brand_obj_id=False):
        if not brand_obj_id:
            product_barcode=self.env['ir.sequence'].get(code="panipat.default.code")
            brand_barcode=10
        else:
            product_barcode=brand_obj_id.seq.next_by_id(sequence_id=brand_obj_id.seq.id)
            brand_barcode=brand_obj_id.barcode_no
        no_of_zeroes=12-len(str(brand_barcode)+str(product_barcode))
        ean_12=no_of_zeroes*"0"+str(brand_barcode)+str(product_barcode)
        print "=====ean12====",ean_12
        final_barcode=ean_12+str(ean_checksum(ean_12))
        print "final barcode======",final_barcode,int(final_barcode)
        return final_barcode
    
    @api.model
    def create(self,vals):
        print "=====vals create product.product===",vals
        if vals.get('product_tmpl_id',False):
            print "=====vals create product.product===",vals
            tmpl_obj=self.env['product.template'].browse(vals['product_tmpl_id'])
            vals['ean13']=self.get_valid_ean(brand_obj_id=tmpl_obj.panipat_brand_name or False)
            vals['default_code']=int(vals['ean13'])
        else:
            brand_obj_id=self.env['panipat.brand.name'].browse(vals.get('panipat_brand_name',False))
            vals['ean13']=self.get_valid_ean(brand_obj_id or False)
            vals['default_code']=int(vals['ean13'])
        #categ_seq=self.env['product.category'].browse(vals.get['categ_id'])
        return super(product_product, self).create(vals)
    
    
    