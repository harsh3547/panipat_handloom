from openerp import fields, api,models

class panipat_crm_product(models.Model):
    _name = "panipat.crm.product"

    product_id = fields.Many2one('product.product',string="product",required=True)
    crm_lead_id = fields.Many2one('panipat.crm.lead')
    description = fields.Text(string="Description")
    sequence = fields.Integer(default=10)
    
    _order='sequence'

    @api.onchange("product_id")
    def _onchange_product_id(self):
        description = self.product_id and self.product_id.name_get()[0][1] or ""
        print "------description=====",description
        if self.product_id and self.product_id.description_sale:
            description += '\n'+self.product_id.description_sale
        self.description = description
    
