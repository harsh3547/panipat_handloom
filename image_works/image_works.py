# -*- encoding: utf-8 -*-
import os
import base64
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
from PIL import Image
from openerp import models, fields, api , tools
from openerp.exceptions import except_orm
from datetime import datetime


class panipat_image_works(models.Model):
    _name="panipat.image.works"
    
    name=fields.Char(string="Name")
    path_main=fields.Char(string="Path of Main Folder",required=True)
    blinds=fields.Char(string="Blind folder",required=True)
    wallpaper=fields.Char(string="Wallpaper folder",required=True)
    carpets=fields.Char(string="Carpets folder",required=True)
    fabric=fields.Char(string="Fabric folder",required=True)
    flooring=fields.Char(string="Flooring folder",required=True)
    others=fields.Char(string="Others folder",required=True)
    
    @api.model
    def create(self,vals):
        total_ids=map(int,self.search(args=[]) or [])
        print total_ids,len(total_ids)
        if len(total_ids)>=1:
            raise except_orm(("Error !!!"), ("Cannot Create More Than One Record"))
        return super(panipat_image_works, self).create(vals)
    
    
    @api.multi
    def test_paths(self):
        try:
            if not os.path.isdir(self.path_main):
                raise except_orm(("Error !!!"), ("The main Folder Path does not Exist !!!"))
            if not os.access(self.path_main, os.R_OK):
                raise except_orm(("Error !!!"), ("The main Folder Path does not have read permissions !!!"))
            fields=['blinds','wallpaper','carpets','fabric','flooring','others']
            values = self.read(fields)
            for rec in fields:
                if not os.path.isdir(os.path.join(self.path_main,values[0].get(rec,False))):
                    raise except_orm(("Error !!!"), ("The %s folder ('%s') in Main Folder ('%s') does not Exist !!!"%(rec,values[0].get(rec,False),self.path_main)))
                #all_paths[rec]=os.path.join(self.path_main,values[0].get(rec,False))
        except:
            raise
        # context change from view_init (panipat_product_image_links) from product.py
        if not self._context.get('from_method',False):
            raise except_orm(("File Path Succeeded !!!"),("Everything Seems Properly Setup !!!"))

