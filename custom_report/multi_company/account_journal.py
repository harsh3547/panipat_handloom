from openerp import models, fields, api, exceptions ,_ 

class account_invoice(models.Model):
    _inherit = "account.journal"

    def _get_custom_company_default(self):
    	value= self.env.user.company_id
    	#print value
    	return value

    custom_company=fields.Many2one("res.company","Company",default=_get_custom_company_default)