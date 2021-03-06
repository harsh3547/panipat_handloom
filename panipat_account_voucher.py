from openerp.osv import fields, osv

class account_voucher(osv.osv):
    _inherit = 'account.voucher'
    
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
    
