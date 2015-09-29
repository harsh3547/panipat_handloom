from openerp.osv import fields, osv
from datetime import datetime
from openerp.tools.translate import _

AVAILABLE_PRIORITIES = [
    ('0', 'Very Low'),
    ('1', 'Low'),
    ('2', 'Normal'),
    ('3', 'High'),
    ('4', 'Very High'),
]

class panipat_crm_lead(osv.osv):
    _name = "panipat.crm.lead"
    _rec_name = 'sequence'
    
    def _get_amount_paid(self,cr,uid,ids,name, arg,context=None):
        
        res = {}
        amount_paid = 0.0
        voucher_obj = self.pool.get('account.voucher')
        for id in ids:
            voucher_ids = voucher_obj.search(cr,uid,[('crm_lead_id','=',id)],context=None)
            print "voucher_ids-----------------------------",voucher_ids
            for obj in voucher_obj.browse(cr,uid,voucher_ids,context=None) :
                amount_paid += obj.amount
            res[id] = amount_paid
        print "===============res===",res
        return res
    
    def lead_amount_paid_records(self,cr,uid,id,context=None):
        obj = self.browse(cr,uid,id,context=None)
        voucher_ids = self.pool.get('account.voucher').search(cr,uid,[('crm_lead_id','=',id[0])])
        return {
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.voucher',
                'type': 'ir.actions.act_window',
                'domain':[('id','in',voucher_ids)],
                'context': {
                            'tree_view_ref':'account_voucher.view_voucher_tree',
                            'form_view_ref':'account_voucher.view_vendor_receipt_form',
                            'default_partner_id': obj.partner_id.id ,
                            'crm_lead_id':obj.id,
                            'search_disable_custom_filters': False
                            }
                }
    
    def create(self,cr,uid,vals,context=None):
        if vals.get('sequence','/')=='/':
            print "in sequnece"
            vals['sequence']=self.pool.get('ir.sequence').get(cr,uid,'CRM.Lead.Order.No',context=None) or '/'
        return super(panipat_crm_lead,self).create(cr,uid,vals,context=None)
    
    def confirm_and_allocate(self,cr,uid,id,context=None):
        self.write(cr,uid,id,{'state':'done'},context=None)
        carry_fields = self.read(cr,uid,id,['sequence','partner_id'],context=None)
        crm_id = carry_fields[0].pop('id')
        vals=carry_fields[0]
        if vals.get('partner_id',False) :
            vals['partner_id'] = vals.get('partner_id')[0]
        vals['sequence'] = crm_id
        vals.update({'state':'draft'})
        allocated_id=self.pool.get('crm.lead.allocated').create(cr,uid,vals,context=None)
        print "------------------------------",allocated_id
        return True
    
    def view_allocation_order(self,cr,uid,id,context=None):
        sequence=self.read(cr,uid,id,['sequence'],context=None)[0].get('sequence')
        allocated_ids=self.pool.get('crm.lead.allocated').search(cr,uid,[('sequence','=',sequence)],context=None)
        if allocated_ids :
            if len(allocated_ids) == 1 :
                return {
                'name': 'CRM - Leads Allocated Form',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'crm.lead.allocated',
                'type': 'ir.actions.act_window',
                'res_id': allocated_ids[0],
                }
            else :
                return {
                'name': 'CRM - Leads Allocated Form',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'crm.lead.allocated',
                'type': 'ir.actions.act_window',
                'domain':[('id','in',allocated_ids)],
                }
        else :
            return {
                    'type': 'ir.actions.client',
                    'tag': 'action_warn',
                    'name': 'Warning',
                    'params': {
                               'title': 'Warning!',
                               'text': 'Allocated Lead is not available .',
                               }
                    }
        
                                                  
    def on_change_partner_id(self, cr, uid, ids, partner_id, context=None):
        values = {}
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
            values = {
                'partner_name': partner.parent_id.name if partner.parent_id else partner.name,
                'contact_name': partner.name if partner.parent_id else False,
                'title': partner.title and partner.title.id or False,
                'street': partner.street,
                'street2': partner.street2,
                'city': partner.city,
                'state_id': partner.state_id and partner.state_id.id or False,
                'country_id': partner.country_id and partner.country_id.id or False,
                'email_from': partner.email,
                'phone': partner.phone,
                'mobile': partner.mobile,
                'fax': partner.fax,
                'zip': partner.zip,
            }
        return {'value': values}

    def onchange_state(self, cr, uid, ids, state_id, context=None):
        if state_id:
            country_id=self.pool.get('res.country.state').browse(cr, uid, state_id, context).country_id.id
            return {'value':{'country_id':country_id}}
        return {}
    
    _columns = {
        'partner_name': fields.char(string="Company Name"),
        'partner_id': fields.many2one('res.partner', 'Partner', ondelete='set null', track_visibility='onchange',
            select=True, help="Linked partner (optional). Usually created when converting the lead.",required=True),
        'name': fields.char('Subject', required=True, select=1),
        'email_from': fields.char('Email', size=128, help="Email address of the contact", select=1),
        'create_date': fields.datetime('Creation Date', readonly=True),
        'description': fields.text('Notes'),
        'contact_name': fields.char('Contact Name', size=64),
        'priority': fields.selection(AVAILABLE_PRIORITIES, 'Priority', select=True),
        'user_id': fields.many2one('res.users', 'Salesperson', select=True, track_visibility='onchange'),
        'current_date': fields.datetime('Date',Readonly=True),
        'product_line': fields.one2many('panipat.crm.product','crm_lead_id',string="Products"),
        'street': fields.char('Street'),
        'street2': fields.char('Street2'),
        'zip': fields.char('Zip', change_default=True, size=24),
        'city': fields.char('City'),
        'state_id': fields.many2one("res.country.state", 'State'),
        'country_id': fields.many2one('res.country', 'Country'),
        'phone': fields.char('Phone'),
        'fax': fields.char('Fax'),
        'mobile': fields.char('Mobile'),
        'title': fields.many2one('res.partner.title', 'Title'),
        'sequence': fields.char(string="Order No.",copy=False),
        'state': fields.selection(string="State",selection=[('draft','Draft'),('done','Done')],copy=False),
        'total_paid_amount':fields.function(_get_amount_paid,type='float',string="Payment"),
    }

    _defaults = {
        'create_date': fields.datetime.now,
        'sequence':'/',
        'state': 'draft',
        'total_paid_amount':00.00,
    }
