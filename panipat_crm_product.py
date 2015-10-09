from openerp.osv import fields, osv

class panipat_crm_product(osv.osv):
    _name = "panipat.crm.product"
    
    _columns = {
    	'sequence':fields.integer(),
        'product_id': fields.many2one('product.product',string="product",required=True),
        'crm_lead_id': fields.many2one('panipat.crm.lead'),
        'description':fields.text(string="Description"),
                }
    _order='sequence'
    _defaults={
               'sequence':10,
               }