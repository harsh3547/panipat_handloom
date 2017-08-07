##############################################################################

import time

from openerp.report import report_sxw
from openerp.tools.translate import _
from openerp.osv import osv
from openerp.tools.amount_to_text_en import amount_to_text
from openerp.tools.float_utils import float_round, float_compare
import string

class report_challan(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(report_challan, self).__init__(cr, uid, name, context=context)
        self.localcontext.update( {
            'time': time,
            'amount_in_word': self._amount_to_text,
            'round_off_fmt':self._round_off_fmt,
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

    def _round_off_fmt(self,round_off,context=None):
        prec=self.pool.get('decimal.precision').precision_get(self.cr, self.uid, 'Account')
        round_off_fmt = "%.{0}f".format(prec)%round_off
        return round_off_fmt
        

class challan_report_class(osv.AbstractModel):
    _name = 'report.panipat_handloom.report_challan'
    _inherit = 'report.abstract_report'
    _template = 'panipat_handloom.report_challan'
    _wrapped_report_class = report_challan

class challan_report_class_full_page(osv.AbstractModel):
    _name = 'report.panipat_handloom.report_challan_full_page'
    _inherit = 'report.abstract_report'
    _template = 'panipat_handloom.report_challan_full_page'
    _wrapped_report_class = report_challan

