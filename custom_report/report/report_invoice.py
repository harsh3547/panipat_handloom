##############################################################################

import time

from openerp.report import report_sxw
from openerp.tools.translate import _
from openerp.osv import osv
from openerp.tools.amount_to_text_en import amount_to_text
from openerp.tools.float_utils import float_round, float_compare

import string

class report_account_invoice_customer(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        print "=-=-=----------666666666666666666666666666",context
        super(report_account_invoice_customer, self).__init__(cr, uid, name, context=context)
        self.localcontext.update( {
            'time': time,
            'amount_in_word': self._amount_to_text,
            'round_off_fmt':self._round_off_fmt,
            'tax_amt':self._get_tax_value,
        })
        self.context = context

    def _get_tax_value(self,tax):
        cr=self.cr
        uid=self.uid
        invoice_id=self.context.get('active_ids',[False])[0]
        inv_obj=self.pool.get("account.invoice").browse(cr,uid,invoice_id,context=self.context)
        tax_amt={}
        local_gst=0.0
        tax_amt['CGST']=0
        tax_amt['SGST']=0
        tax_amt['IGST']=0
        for res in inv_obj.tax_line:
            if ('cgst' in res.name.lower()) or ('sgst' in res.name.lower()):
                local_gst=res.amount
            elif 'igst' in res.name.lower():
                tax_amt['IGST']=res.amount
            break
        tax_amt['CGST']=tax_amt['SGST']=local_gst/2.0
        prec=self.pool.get('decimal.precision').precision_get(self.cr, self.uid, 'Account')
        final_amt="%.{0}f".format(prec)%tax_amt[tax]
        return final_amt

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

    def _round_off_fmt(self,round_off,context=None):
        prec=self.pool.get('decimal.precision').precision_get(self.cr, self.uid, 'Account')
        round_off_fmt = "%.{0}f".format(prec)%round_off
        return round_off_fmt
        

class customer_report_invoice(osv.AbstractModel):
    _name = 'report.panipat_handloom.customer_report_invoice'
    _inherit = 'report.abstract_report'
    _template = 'panipat_handloom.customer_report_invoice'
    _wrapped_report_class = report_account_invoice_customer

