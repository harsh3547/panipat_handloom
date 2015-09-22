from openerp.osv import fields, osv

class account_voucher(osv.osv):
    _inherit = 'account.voucher'
    
    def create(self,cr,uid,vals,context=None):
        
        print "context-----------------------------",context
        vals['crm_lead_id'] = context.get('active_id',False)
        vals['type']= 'receipt'
        print "vals-----------------------------",vals
        return super(account_voucher,self).create(cr,uid,vals,context=None)
    
    _columns = {
                'crm_lead_id':fields.many2one('panipat.crm.lead',string='CRM Lead Id')
                }
    
