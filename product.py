# -*- coding: utf-8 -*-
from openerp import models, fields, api , tools
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
    #print finalean
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

    def _get_filetype(self,base64_source):
        image_stream = StringIO.StringIO(base64_source.decode('base64'))
        try:
            image = Image.open(image_stream)
        except:
            raise except_orm(("ERROR !!"),("Invalid Image Type"))
        # store filetype here, as Image.new below will lose image.format
        filetype = None
        filetype = (filetype or image.format).upper()
        filetype = {
            'BMP': 'PNG','JPEG':'JPG'
        }.get(filetype, filetype)
        return filetype.lower() or 'jpg'

    @api.one
    @api.depends('image_1_path')
    def _get_img_1_file_name(self):
        if self.image_1_path:
            filetype=self._get_filetype(self.image_1_path)
            self.image_1_file_name=str(int(self.ean13))+"_1"+"."+filetype

    @api.one
    @api.depends('image_2_path')
    def _get_img_2_file_name(self):
        if self.image_2_path:
            filetype=self._get_filetype(self.image_2_path)
            self.image_2_file_name=str(int(self.ean13))+"_2"+"."+filetype
    
    @api.one
    @api.depends('image_3_path')
    def _get_img_3_file_name(self):
        if self.image_3_path:
            filetype=self._get_filetype(self.image_3_path)
            self.image_3_file_name=str(int(self.ean13))+"_3"+"."+filetype
    
    @api.one
    @api.depends('image_4_path')
    def _get_img_4_file_name(self):
        if self.image_4_path:
            filetype=self._get_filetype(self.image_4_path)
            self.image_4_file_name=str(int(self.ean13))+"_4"+"."+filetype
            
    @api.one
    @api.depends('image_1_path')
    def _get_image_1_img(self):
        if self.image_1_path:
            self.image_1_img=self.check_and_resize_image_medium(self.image_1_path,size=(180,180))

    @api.one
    @api.depends('image_2_path')
    def _get_image_2_img(self):
        if self.image_2_path:
            self.image_2_img=self.check_and_resize_image_medium(self.image_2_path,size=(180,180))

    @api.one
    @api.depends('image_3_path')
    def _get_image_3_img(self):
        if self.image_3_path:
            self.image_3_img=self.check_and_resize_image_medium(self.image_3_path,size=(180,180))

    @api.one
    @api.depends('image_4_path')
    def _get_image_4_img(self):
        if self.image_4_path:
            self.image_4_img=self.check_and_resize_image_medium(self.image_4_path,size=(180,180))


    def check_and_resize_image_medium(self,base64_source,size=(None,None)):
        if size==(None,None):size=(90,90)
        image_stream = StringIO.StringIO(base64_source.decode('base64'))
        try:
            image = Image.open(image_stream)
        except:
            raise except_orm(("ERROR !!"),("Invalid Image Type"))
        return tools.image_resize_image_medium(base64_source,size=size,avoid_if_small=True)


    def _get_image_1(self):
        if self.image:
            return self.image
        return False

    @api.multi
    @api.depends('name','default_code','panipat_brand_name','vol_file_name','serial_no','shade_no','design_code','color_code','other_code','color_name')
    def _get_caption_value(self):
        for p_obj in self:
            attrs=''
            attrs=(('['+p_obj.default_code+'] ') if p_obj.default_code else '' ) + (p_obj.name or '')
            attrs=(attrs + ' '+str(p_obj.panipat_brand_name.name)) if p_obj.panipat_brand_name.name else ''
            attrs=(attrs + ';'+str(p_obj.vol_file_name.name)) if p_obj.vol_file_name.name else ''
            if p_obj.serial_no:
                attrs=attrs + ' (S/No-'+str(p_obj.serial_no)+')'
            if p_obj.shade_no:
                attrs=attrs + ' (Sh/No-'+str(p_obj.shade_no)+')'
            if p_obj.design_code:
                attrs=attrs + ' (D/No-'+str(p_obj.design_code)+')'
            if p_obj.color_code:
                attrs=attrs + ' (Co/Co-'+str(p_obj.color_code)+')'
            if p_obj.other_code:
                attrs=attrs + ' (Ot/Co-'+str(p_obj.other_code)+')'
            if p_obj.color_name:
                attrs=attrs + ' COLOR-'+str(p_obj.color_name)+''
            p_obj.caption=p_obj.custom_caption if (p_obj.custom_caption_boolean and p_obj.custom_caption) else attrs            

    caption=fields.Text(string="Image Caption",compute=_get_caption_value)
    custom_caption=fields.Text(string="Custom Caption")
    custom_caption_boolean = fields.Boolean(string='Insert Custom Caption',)
    uom_id=fields.Many2one(comodel_name='product.uom',string= 'Unit of Measure', required=True,default=False, help="Default Unit of Measure used for all stock operation.")
    panipat_brand_name=fields.Many2one(comodel_name='panipat.brand.name', string='Brand Name')
    vol_file_name=fields.Many2one(comodel_name='panipat.brand.vol', string='Vol/File No.')
    serial_no=fields.Char(string="Serial No./Page No.(S/No.)",select=True)
    design_code=fields.Char(string="Design/Item Code(D/No.)",select=True)
    shade_no=fields.Char(string="Shade No.(Sh/No.)",select=True)
    color_code=fields.Char(string="Color Code(Co/Co.)",select=True)
    material=fields.Char(string="Material")
    pattern=fields.Char(string="Pattern")
    color_name=fields.Char(string="Color",select=True)
    size=fields.Char(string="Size")
    panipat_product_type=fields.Char(string="Type")
    other_code=fields.Char(string="Other Code(Ot/Co.)")
    type = fields.Selection([('product', 'Stockable Product'),('consu', 'Consumable'),('service','Service')], 'Product Type', required=True, help="Consumable are product where you don't manage stock, a service is a non-material product provided by a company or an individual.",default='product')  
    sale_delay= fields.Float('Customer Lead Time', help="The average delay in days between the confirmation of the customer order and the delivery of the finished products. It's the time you promise to your customers.",default=0)
    roll_rates=fields.One2many(comodel_name='roll.rates', inverse_name='roll_rate_product', string="Roll Rates",copy=True)
    seller_ids=fields.One2many(comodel_name='product.supplierinfo', inverse_name='product_tmpl_id', string='Supplier',copy=True)

    image_1_img=fields.Binary(compute='_get_image_1_img',store=True,copy=False)
    image_1_path=fields.Binary(default=_get_image_1,copy=False)
    image_1_file_name=fields.Char(compute='_get_img_1_file_name',store=True,copy=False)
    image_1_true= fields.Boolean(string="Is this Main Image ?",default=True,copy=False)

    image_2_img=fields.Binary(compute='_get_image_2_img',store=True,copy=False)
    image_2_path=fields.Binary(copy=False)
    image_2_file_name=fields.Char(compute='_get_img_2_file_name',store=True,copy=False)
    image_2_true= fields.Boolean(string="Is this Main Image ?",default=False,copy=False)

    image_3_img=fields.Binary(compute='_get_image_3_img',store=True,copy=False)
    image_3_path=fields.Binary(copy=False)
    image_3_file_name=fields.Char(compute='_get_img_3_file_name',store=True,copy=False)
    image_3_true= fields.Boolean(string="Is this Main Image ?",default=False,copy=False)

    image_4_img=fields.Binary(compute='_get_image_4_img',store=True,copy=False)
    image_4_path=fields.Binary(copy=False)
    image_4_file_name=fields.Char(compute='_get_img_4_file_name',store=True,copy=False)        
    image_4_true= fields.Boolean(string="Is this Main Image ?",default=False,copy=False)

    hsn_code=fields.Many2one("hsn.code",string="HSN Code")

    
    @api.multi
    def button_main_image(self):
        if self.image_1_true and self.image_1_path:
            self.image=self.image_1_path
            self.image_1_file_name=str(int(self.ean13))+"_1."+self._get_filetype(self.image_1_path)
        elif self.image_2_true and self.image_2_path:
            self.image=self.image_2_path
            self.image_2_file_name=str(int(self.ean13))+"_2."+self._get_filetype(self.image_2_path)
        elif self.image_3_true and self.image_3_path:
            self.image=self.image_3_path
            self.image_3_file_name=str(int(self.ean13))+"_3."+self._get_filetype(self.image_3_path)
        elif self.image_4_true and self.image_4_path:
            self.image=self.image_4_path
            self.image_4_file_name=str(int(self.ean13))+"_4."+self._get_filetype(self.image_4_path)
        elif self.image_1_path:
            self.image=self.image_1_path
            self.image_1_true=True
            self.image_1_file_name=str(int(self.ean13))+"_1."+self._get_filetype(self.image_1_path)
        elif self.image and not self.image_1_path:
            self.image_1_path=self.image
            self.image_1_file_name=str(int(self.ean13))+"_1."+self._get_filetype(self.image)
            self.image_1_true=True
        else: return True
            
    @api.onchange('image_1_true')
    def onchange_main_image_1(self):
        if self.image_1_true:
            self.image_2_true=False
            self.image_3_true=False
            self.image_4_true=False
            
    @api.onchange('image_2_true')
    def onchange_main_image_2(self):
        if self.image_2_true:
            self.image_1_true=False
            self.image_3_true=False
            self.image_4_true=False

    @api.onchange('image_3_true')
    def onchange_main_image_3(self):
        if self.image_3_true:
            self.image_2_true=False
            self.image_1_true=False
            self.image_4_true=False

    @api.onchange('image_4_true')
    def onchange_main_image_4(self):
        if self.image_4_true:
            self.image_2_true=False
            self.image_3_true=False
            self.image_1_true=False


    def check_and_resize_image_big(self,base64_source):
        image_stream = StringIO.StringIO(base64_source.decode('base64'))
        try:
            image = Image.open(image_stream)
        except:
            raise except_orm(("ERROR !!"),("Invalid Image Type"))
        return tools.image_resize_image_big(base64_source)

    @api.model
    def create(self,vals):
        if vals.get('image_1_path',False):
            vals['image_1_path']=self.check_and_resize_image_big(vals['image_1_path'])
        if vals.get('image_2_path',False):
            vals['image_2_path']=self.check_and_resize_image_big(vals['image_2_path'])
        if vals.get('image_3_path',False):
            vals['image_3_path']=self.check_and_resize_image_big(vals['image_3_path'])
        if vals.get('image_4_path',False):
            vals['image_4_path']=self.check_and_resize_image_big(vals['image_4_path'])
        

        #print "--------------in product template create-------------",vals
        return super(product_template, self).create(vals)
    
    @api.multi
    def write(self,vals):
        for rec in self:
            if vals.get('image_1_path',False):
                vals['image_1_path']=rec.check_and_resize_image_big(vals['image_1_path'])
                if not rec.image_1_true and not rec.image_2_true and not rec.image_3_true and not rec.image_4_true:
                    vals['image']=vals['image_1_path']
                    vals['image_1_true']=True
                elif rec.image_1_true:vals['image']=vals['image_1_path']
            if vals.get('image_2_path',False):
                vals['image_2_path']=rec.check_and_resize_image_big(vals['image_2_path'])
            if vals.get('image_3_path',False):
                vals['image_3_path']=rec.check_and_resize_image_big(vals['image_3_path'])
            if vals.get('image_4_path',False):
                vals['image_4_path']=rec.check_and_resize_image_big(vals['image_4_path'])
            
        #print "-----------in product template write=------------",vals
        return super(product_template, self).write(vals)
        
    
    @api.multi
    def remove_barcode(self):
        self.write({'default_code':''})
        return True
    
    @api.multi
    def display_barcode(self):
        self.write({'default_code':str(int(self.ean13))})
        return True
                
class product_product(models.Model):
    _inherit="product.product"
    
    
    def get_valid_ean(self,brand_obj_id=False):
        if not brand_obj_id:
            product_barcode=self.env['ir.sequence'].get(code="panipat.default.code")
            brand_barcode=10
        else:
            product_barcode=brand_obj_id.seq.next_by_id(sequence_id=brand_obj_id.seq.id)
            brand_barcode=brand_obj_id.barcode_no
        no_of_zeroes=12-len(str(brand_barcode)+str(product_barcode))
        ean_12=no_of_zeroes*"0"+str(brand_barcode)+str(product_barcode)
        #print "=====ean12====",ean_12
        final_barcode=ean_12+str(ean_checksum(ean_12))
        #print "final barcode======",final_barcode,int(final_barcode)
        return final_barcode
    
    @api.model
    def create(self,vals):
        #print "--------------in product.product create-------------",vals
        if vals.get('product_tmpl_id',False):
            tmpl_obj=self.env['product.template'].browse(vals['product_tmpl_id'])
            vals['ean13']=self.get_valid_ean(brand_obj_id=tmpl_obj.panipat_brand_name or False)
            vals['default_code']=int(vals['ean13'])
            #print "--------------in product.product create-------------",vals
            res = super(product_product, self).create(vals)
            # writing on related fields
            self.pool.get('product.template').write(self._cr, self._uid, vals['product_tmpl_id'], {'ean13':vals['ean13'],'default_code':vals['default_code']} ,context=self._context)
        else:
            brand_obj_id=self.env['panipat.brand.name'].browse(vals.get('panipat_brand_name',False))
            vals['ean13']=self.get_valid_ean(brand_obj_id or False)
            vals['default_code']=int(vals['ean13'])
            #print "--------------in product.product create-------------",vals
            res = super(product_product, self).create(vals)
        return res
    
class product_hsn_code(models.Model):
    _name="hsn.code"
    name=fields.Char(string="HSN Code")

    _sql_constraints = [
                     ('name_unique', 
                      'unique(name)',
                      'Value already Exists - HSN Code has to be unique!')
]

    @api.model
    def create(self,vals):
        print "====hsn code create context ===",self._context,vals
        res = super(product_hsn_code, self).create(vals)
        print res
        prod_temp_obj = self.env['product.product'].browse(self._context.get('product_id',False))
        if self._context.get('product_id',False):
            prod_temp_obj.product_tmpl_id.hsn_code=res.id
            print prod_temp_obj.product_tmpl_id.hsn_code
        return res


    
class product_supplierinfo(models.Model):
    _inherit="product.supplierinfo"
    
    roll_rates=fields.One2many(comodel_name='roll.rates', inverse_name='roll_rate_partnerinfo', string="Roll Rates",copy=True)
    delay=fields.Integer(string='Delivery Lead Time', required=True, help="Lead time in days between the confirmation of the purchase order and the receipt of the products in your warehouse. Used by the scheduler for automatic computation of the purchase order planning.",default=0)
        
    
class roll_rates(models.Model):
    _name="roll.rates"
    
    name=fields.Many2one(comodel_name='roll.rate.name', string='Name')
    rate=fields.Float(string="Roll rates",digits_compute=dp.get_precision('Product Price'))
    roll_rate_partnerinfo=fields.Many2one(comodel_name='product.supplierinfo',string='one 2 many rel', ondelete='cascade',readonly=True)
    roll_rate_product=fields.Many2one(comodel_name='product.template', string='one 2 many rel', ondelete='cascade',readonly=True)
    
class roll_rate_name(models.Model):
    _name="roll.rate.name"    
        
    name=fields.Char(string="Name")    
        
class panipat_product_template_duplicate(models.TransientModel):
    _name="panipat.product.template.duplicate"
    
    duplicates_to_create = fields.Integer(string="Duplicates To Create",default=0)

    @api.multi
    def duplicate_product(self):
        product_id=self._context.get('active_id',False)
        if product_id:
            copy_ids=[product_id]
            for i in range(self.duplicates_to_create):
                copy_ids.append(self.pool.get('product.template').copy(self._cr,self._uid,product_id,context=self._context))
            if len(copy_ids)==1:return True
            return{
                   'view_type': 'form',
                   'view_mode': 'tree,form,kanban',
                   'res_model': 'product.template',
                   'type': 'ir.actions.act_window',
                   'domain':[('id','in',copy_ids)],
                   }
        return True

    def view_init(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        res = super(panipat_product_template_duplicate, self).view_init(cr, uid, fields_list, context=context)
        active_ids = context.get('active_ids',[])
        if len(active_ids) > 1:
            raise except_orm(_('ERROR!'), _('Cannot Duplicate More Than 1 Product at Once'))
        return res
            
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
