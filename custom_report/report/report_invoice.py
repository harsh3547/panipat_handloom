##############################################################################

import time

from openerp.report import report_sxw
from openerp.tools.translate import _
from openerp.osv import osv
from openerp.tools.amount_to_text_en import amount_to_text
import string

class report_account_invoice_customer(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        print "=-=-=----------666666666666666666666666666"
        super(report_account_invoice_customer, self).__init__(cr, uid, name, context=context)
        self.localcontext.update( {
            'time': time,
            'amount_in_word': self._amount_to_text
        })
        self.context = context

    def _amount_to_text(self, amount, currency_id, context=None):
        # Currency complete name is not available in res.currency model
        # Exceptions done here (EUR, USD, BRL) cover 75% of cases
        # For other currencies, display the currency code
        currency = self.pool['res.currency'].browse(self.cr, self.uid, currency_id, context=context)
        if currency.name.upper() == 'EUR':
            currency_name = 'Euro'
        elif currency.name.upper() == 'USD':
            currency_name = 'Dollars'
        elif currency.name.upper() == 'BRL':
            currency_name = 'reais'
        elif currency.name.upper() == 'INR':
            currency_name = 'Rupees'
        else:
            currency_name = currency.name
        amout_str = amount_to_text(amount, currency=currency_name)
        if currency.name.upper() == 'INR':
            amout_str = string.replace(amout_str, 'Cents', 'Paisa')
            amout_str = string.replace(amout_str, 'Cent', 'Paisa')
        return amout_str

class customer_report_invoice(osv.AbstractModel):
    _name = 'report.panipat_handloom.customer_report_invoice'
    _inherit = 'report.abstract_report'
    _template = 'panipat_handloom.customer_report_invoice'
    _wrapped_report_class = report_account_invoice_customer

