# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class account_voucher(osv.osv):
    _inherit='account.voucher'
    
    #_columns={
    #          }
    
    def _get_journal(self, cr, uid, context=None):
        if context is None: context = {}
        invoice_pool = self.pool.get('account.invoice')
        journal_pool = self.pool.get('account.journal')
        if context.get('invoice_id', False):
            invoice = invoice_pool.browse(cr, uid, context['invoice_id'], context=context)
            journal_id = journal_pool.search(cr, uid, [
                ('currency', '=', invoice.currency_id.id), ('company_id', '=', invoice.company_id.id)
            ], limit=1, context=context)
            return journal_id and journal_id[0] or False
        if context.get('journal_id', False):
            return context.get('journal_id')
        if not context.get('journal_id', False) and context.get('search_default_journal_id', False):
            return context.get('search_default_journal_id')

        ttype = context.get('type', 'bank')
        if ttype in ('payment', 'receipt'):
            ttype = 'cash'
        res = self._make_journal_search(cr, uid, ttype, context=context)
        print "-in _get journal -new09090909090909--------res ===",res
        return res and res[0] or False
    
    def create(self,cr,uid,vals,context=None):
        
        print "context-----------------------------",context,vals
        if context.get('order_group',False):
            vals['order_group'] = context.get('order_group',False)
            vals['type'] = 'receipt'
            vals['partner_id'] = context.get('default_partner_id',False)
            # so that even if user changes the partner it'll still record payment of partner 
            # of corresponding order from panipat.crm.lead
        print "vals-----------------------------",vals
        return super(account_voucher,self).create(cr,uid,vals,context=None)
    
    _columns = {
                'order_group':fields.many2one('panipat.order.group',string='Order Group')
                }

    _defaults = {
        'journal_id':_get_journal,
        }
    