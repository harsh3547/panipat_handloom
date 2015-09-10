from openerp.osv import fields, osv

class product_product(osv.osv):
    _inherit='product.template'
    
    _columns = {
        'crm_lead_id': fields.many2one('crm.lead'),
                }