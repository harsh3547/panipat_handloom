from openerp.osv import fields, osv

class panipat_product(osv.osv):
    _name = "panipat.product"
    
    _columns = {
        'product_id': fields.many2one('product.product',string="product"),
        'crm_lead_id': fields.many2one('panipat.crm.lead'),
        'description':fields.text(string="Description"),
                }
