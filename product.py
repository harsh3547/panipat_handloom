# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm
from datetime import datetime
from openerp.tools.translate import _
import math
import openerp.addons.decimal_precision as dp
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
from PIL import Image
import os , fnmatch
import time


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
    vol_file_name=fields.Many2one(comodel_name='panipat.brand.vol', string='Vol/File No.')
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
    
class product_supplierinfo(models.Model):
    _inherit="product.supplierinfo"
    
    roll_rates=fields.One2many(comodel_name='roll.rates', inverse_name='roll_rate_partnerinfo', string="Roll Rates")
    delay=fields.Integer(string='Delivery Lead Time', required=True, help="Lead time in days between the confirmation of the purchase order and the receipt of the products in your warehouse. Used by the scheduler for automatic computation of the purchase order planning.",default=0)
        
    
class roll_rates(models.Model):
    _name="roll.rates"
    
    name=fields.Many2one(comodel_name='roll.rate.name', string='Name')
    rate=fields.Float(string="Roll rates",digits_compute=dp.get_precision('Product Price'))
    roll_rate_partnerinfo=fields.Many2one(comodel_name='product.supplierinfo',string='one 2 many rel')
    roll_rate_product=fields.Many2one(comodel_name='product.template', string='one 2 many rel')
    
class roll_rate_name(models.Model):
    _name="roll.rate.name"    
        
    name=fields.Char(string="Name")    
        
    
            
class panipat_product_image_links(models.TransientModel):
    _name="panipat.product.image.links"


    def view_init(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        path_rec=self.pool.get('panipat.image.works').search(cr,uid,[],context=context)
        if not path_rec:raise except_orm(_('ERROR!'), _('Please Set Paths In Menu "Settings/Configuration/Configure Image Works'))
        if path_rec:
            ctx=context.copy()
            ctx['from_method']=True
            self.pool.get('panipat.image.works').test_paths(cr,uid,path_rec[0],context=ctx)
        return super(panipat_product_image_links, self).view_init(cr, uid, fields_list, context=context)

    def _get_path_values(self):
        path_rec=self.env['panipat.image.works'].search([])
        if not path_rec:return ""
        main_path=path_rec.path_main
        blind_path=os.path.join(path_rec.path_main,path_rec.blinds)
        wallpaper_path=os.path.join(path_rec.path_main,path_rec.wallpaper)
        carpet_path=os.path.join(path_rec.path_main,path_rec.carpets)
        fabric_path=os.path.join(path_rec.path_main,path_rec.fabric)
        flooring_path=os.path.join(path_rec.path_main,path_rec.flooring)
        others_path=os.path.join(path_rec.path_main,path_rec.others)
        html_str =  ("""
        <table >
            <tr>
                <td style='font-size:18px;padding-left: 15px;padding-top: 5px;padding-bottom: 5px;text-align:left'><u><b>Main Folder :</b></u></td>
                <td style='font-size:14px;padding-left: 15px;padding-top: 5px;padding-bottom: 5px;'><b>%s</b></td>
            </tr>
            <tr>
                <td style='font-size:14px;padding-left: 15px;padding-top: 5px;padding-bottom: 5px;text-align:right'><u><b>Blind Folder :</b></u></td>
                <td style='font-size:14px;padding-left: 15px;padding-top: 5px;padding-bottom: 5px;'>%s</td>
            </tr>
            <tr>
                <td style='font-size:14px;padding-left: 15px;padding-top: 5px;padding-bottom: 5px;text-align:right'><u><b>Wallpaper Folder :</b></u></td>
                <td style='font-size:14px;padding-left: 15px;padding-top: 5px;padding-bottom: 5px;'>%s</td>
            </tr>
            <tr>
                <td style='font-size:14px;padding-left: 15px;padding-top: 5px;padding-bottom: 5px;text-align:right'><u><b>Carpets Folder :</b></u></td>
                <td style='font-size:14px;padding-left: 15px;padding-top: 5px;padding-bottom: 5px;'>%s</td>
            </tr>
            <tr>
                <td style='font-size:14px;padding-left: 15px;padding-top: 5px;padding-bottom: 5px;text-align:right'><u><b>Fabric Folder :</b></u></td>
                <td style='font-size:14px;padding-left: 15px;padding-top: 5px;padding-bottom: 5px;'>%s</td>
            </tr>
            <tr>
                <td style='font-size:14px;padding-left: 15px;padding-top: 5px;padding-bottom: 5px;text-align:right'><u><b>Flooring Folder :</b></u></td>
                <td style='font-size:14px;padding-left: 15px;padding-top: 5px;padding-bottom: 5px;'>%s</td>
            </tr>
            <tr>
                <td style='font-size:14px;padding-left: 15px;padding-top: 5px;padding-bottom: 5px;text-align:right'><u><b>Others Folder :</b></u></td>
                <td style='font-size:14px;padding-left: 15px;padding-top: 5px;padding-bottom: 5px;'>%s</td>
            </tr>
        </table>
"""%(main_path,blind_path,wallpaper_path,carpet_path,fabric_path,flooring_path,others_path))
        
        return html_str

    

    search_path=fields.Char(string="Search Path for files")
    all_path_values=fields.Html(string="Value of all Paths",default=_get_path_values)

    

    def file_find(self,filepat,top):
        photo_files=[]
        for path, dirlist, filelist in os.walk(top):
            for name in fnmatch.filter(filelist,filepat):
                photo_files.append([path,name]) # photo_files is [[path,file_name]]
        return self.make_vals_from_files(photo_files)
    
    def make_vals_from_files(self,photo_files=[]):
        # photo_files is [[path,file_name]] and path is exclusive of file_name

        vals={}
        if len(photo_files)>1:
            for rec1 in photo_files:
                if '_1' in rec1[1]:
                    img1=self._get_base64_image(os.path.join(rec1[0],rec1[1]))
                    if img1:vals['image_1_path']=img1
                elif '_2' in rec1[1]:
                    img2=self._get_base64_image(os.path.join(rec1[0],rec1[1]))
                    if img2:vals['image_2_path']=img2
                elif '_3' in rec1[1]:
                    img3=self._get_base64_image(os.path.join(rec1[0],rec1[1]))
                    if img3:vals['image_3_path']=img3
                elif '_4' in rec1[1]:
                    img4=self._get_base64_image(os.path.join(rec1[0],rec1[1]))
                    if img4:vals['image_4_path']=img4
                else:
                    img1=self._get_base64_image(os.path.join(rec1[0],rec1[1]))
                    if img1:vals['image_1_path']=img1
        elif len(photo_files)==1:
            img1=self._get_base64_image(os.path.join(photo_files[0][0],photo_files[0][1]))
            if img1:vals['image_1_path']=img1
        return vals



    ### matching algo
    ## first get a dictionary (category:path) of all path-directories mentioned in panipat.image.works 
    #   ("all_paths") in main path
    ## then get a list of all directories ("other_dir") not mentioned in 'all_paths' in main_path
    ## and get a dictionary (file_name:path) of all files in main_path
    ## 1. start matching barcodes with files in search_path of wizard
    ## 2. if vals then write else
    ## 3. start matching name,categ_name of product_ids with all_paths:keys and start searching for a
    ##    barcode match 
    ## 4. if no vals then search in other_dir
    ## 5. if no vals then search in other_file_path

    @api.multi
    def button_image_links(self):
        if self.search_path and not os.path.isdir(self.search_path):
            raise except_orm(("Error !!!"), ("The Search Path for Files is 'invalid' !!!")) 
        cr=self._cr
        all_paths={}
        other_file_path={}
        other_dir=[]
        path_id=self.env['panipat.image.works'].search([])

        path_main=path_id.path_main
        all_paths['blinds']=os.path.join(path_main,path_id.blinds)
        all_paths['wallpaper']=os.path.join(path_main,path_id.wallpaper)
        all_paths['carpets']=os.path.join(path_main,path_id.carpets)
        all_paths['fabric']=os.path.join(path_main,path_id.fabric)
        all_paths['flooring']=os.path.join(path_main,path_id.flooring)
        all_paths['others']=os.path.join(path_main,path_id.others)

        for rec in os.listdir(path_main):
            rec_path=os.path.join(path_main,rec)
            if os.path.isdir(rec_path):
                if rec_path not in all_paths.values():
                    other_dir.append(rec_path)
            else:
                if not fnmatch.fnmatch(rec,'.*'):
                    rec_path=path_main
                    other_file_path[rec]=rec_path


        #print "1===",path_main
        #print "2===",all_paths
        #print "3===",other_dir
        #print "4===",other_file_path
        #print "5===",self._context
        cr.execute("select p.id as product_id,lower(p.name) as product_name,p.default_code as code,lower(c.name) as categ_name from product_template p left join product_category c on (p.categ_id=c.id) where p.id in %s and p.default_code is not null and p.type != 'service' and (image_1_path is null or image_2_path is null or image_3_path is null or image_4_path is null)",(tuple(self._context.get('active_ids',False)),))
        product_ids=cr.fetchall() # list of tuples (id,name,default_code,categ_id.name)
        print "==product_ids===",product_ids
        start_time=time.time()
        for rec in product_ids:
            try:
                vals={}
                if self.search_path:
                    vals=self.file_find(str(rec[2])+"*",self.search_path)
                    if vals:print "===========from search_path--------"
                    # searching for files with name same as barcode in the given path
                if not vals:
                    all_path_keys=all_paths.keys() 
                    # match because to search in the folder with same name as name,categ_name first
                    match=[rec2 for rec2 in all_path_keys if ((rec2 in rec[1]) or (rec[1] in rec2) or (rec2 in rec[3]) or (rec[3] in rec2))]
                    if match:
                        vals=self.file_find(str(rec[2])+"*",all_paths[match[0]])
                        if vals:print "---------from all_path_keys match---------",match
                        all_path_keys.remove(match[0])
                    if not vals:
                        for key in all_path_keys:
                            vals=self.file_find(str(rec[2])+"*",all_paths[key])
                            if vals:print "---------from all_path_keys--------",all_path_keys
                            if vals:break
                if not vals:
                    for rec3 in other_dir:
                        vals=self.file_find(str(rec[2])+"*",rec3)
                        if vals:print "==============from other_dir========="
                        if vals:break
                if not vals:
                    other_file_match=[[other_file_path[rec4],rec4] for rec4 in other_file_path.keys() if str(rec[2]) in rec4]
                    if other_file_match:
                        print "----------from other file match--------"
                        vals=self.make_vals_from_files(other_file_match)
                print "-=-=--------rec-=-=-=-=-=-=-=-",rec
                print "-=-=-=-=-=-=-=vals=-=-=-=-=-",vals.keys()
                print "============================================================="
                if vals:self.pool.get('product.template').write(cr,self._uid,rec[0],vals,context=self._context)
            except:
                raise
                print """=============================================================
                =================ERROR IN def button_image_links================"""
        print "--- %s seconds ---" %(time.time() - start_time)
        return True

    def _get_base64_image(self,full_file_path, size=(1024, 1024), encoding='base64', filetype=None, avoid_if_small=True):
        try:
            image = Image.open(full_file_path)
        except:
            return ''
        # store filetype here, as Image.new below will lose image.format
        filetype = (filetype or image.format).upper()

        filetype = {
            'BMP': 'PNG',
        }.get(filetype, filetype)

        asked_width, asked_height = size
        if asked_width is None:
            asked_width = int(image.size[0] * (float(asked_height) / image.size[1]))
        if asked_height is None:
            asked_height = int(image.size[1] * (float(asked_width) / image.size[0]))
        size = asked_width, asked_height

        # check image size: do not create a thumbnail if avoiding smaller images
        if avoid_if_small and image.size[0] <= size[0] and image.size[1] <= size[1]:
            background_stream = StringIO.StringIO()
            image.save(background_stream, filetype)
            return background_stream.getvalue().encode(encoding)

        if image.size != size:
            image = tools.image_resize_and_sharpen(image, size,preserve_aspect_ratio=True)
        if image.mode not in ["1", "L", "P", "RGB", "RGBA"]:
            image = image.convert("RGB")

        background_stream = StringIO.StringIO()
        image.save(background_stream, filetype)
        return background_stream.getvalue().encode(encoding)
