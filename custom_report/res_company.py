# -*- coding: utf-8 -*-

from openerp import models, fields, api, _

class res_company(models.Model):
    _inherit = "res.company"

    company_vat_tin = fields.Char("Company's VAT TIN")
    company_cst_no = fields.Char("Company's CST No.")
    company_pan_no = fields.Char("Company's PAN")
    
    
class res_partner(models.Model):
    _inherit = "res.partner"

    buyer_vat_tin = fields.Char("VAT TIN")
    
class account_invoice(models.Model):
    _inherit = "account.invoice"
    
    @api.multi
    def invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        self.sent = True
        if self.type == 'out_invoice':
            return self.env['report'].get_action(self, 'custom_report.customer_report_invoice')
        return self.env['report'].get_action(self, 'account.report_invoice')
