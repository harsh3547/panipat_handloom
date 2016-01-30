from openerp.osv import fields, osv
from datetime import datetime
from openerp.tools.translate import _

class panipat_order_group(osv.osv):
    _name="panipat.order.group"
    _columns={
            'name':fields.char('Order Group ',readonly=True),
            'partner_id':fields.many2one('res.partner',string="Partner",ondelete='set null',readonly=True),
                                            
        }
    
    _defaults={'name':'/'}
    
    def create(self,cr,uid,vals,context=None):
        if vals.get('name','/')=='/':
            vals['name']=self.pool.get('ir.sequence').get(cr,uid,'panipat.order.group',context) or '/'
            print "=======vals panipat_order_group======",vals
        return super(panipat_order_group, self).create(cr,uid,vals,context)
