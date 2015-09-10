from openerp.osv import fields, osv
from datetime import datetime
import crm


class crm_lead(osv.osv):
    _name = "crm.lead"

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

    def on_change_user(self, cr, uid, ids, user_id, context=None):
        """ When changing the user, also set a section_id or restrict section id
            to the ones user_id is member of. """
        section_id = self._get_default_section_id(cr, uid, user_id=user_id, context=context) or False
        if user_id and self.pool['res.users'].has_group(cr, uid, 'base.group_multi_salesteams') and not section_id:
            section_ids = self.pool.get('crm.case.section').search(cr, uid, ['|', ('user_id', '=', user_id), ('member_ids', '=', user_id)], context=context)
            if section_ids:
                section_id = section_ids[0]
        return {'value': {'section_id': section_id}}
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner', ondelete='set null', track_visibility='onchange',
            select=True, help="Linked partner (optional). Usually created when converting the lead."),

        'id': fields.integer('ID', readonly=True),
        'name': fields.char('Subject', required=True, select=1),
        'date_action_last': fields.datetime('Last Action', readonly=1),
        'date_action_next': fields.datetime('Next Action', readonly=1),
        'email_from': fields.char('Email', size=128, help="Email address of the contact", select=1),
        'section_id': fields.many2one('crm.case.section', 'Sales Team',
                        select=True, track_visibility='onchange', help='When sending mails, the default email address is taken from the sales team.'),
        'create_date': fields.datetime('Creation Date', readonly=True),
        'email_cc': fields.text('Global CC', help="These email addresses will be added to the CC field of all inbound and outbound emails for this record before being sent. Separate multiple email addresses with a comma"),
        'description': fields.text('Notes'),
        'write_date': fields.datetime('Update Date', readonly=True),
        'contact_name': fields.char('Contact Name', size=64),
        'partner_name': fields.char("Customer Name", size=64,help='The name of the future partner company that will be created while converting the lead into opportunity', select=1),
        'type': fields.selection([ ('lead','Lead'), ('opportunity','Opportunity'), ],'Type', select=True, help="Type is used to separate Leads and Opportunities"),
        'priority': fields.selection(crm.AVAILABLE_PRIORITIES, 'Priority', select=True),
        'user_id': fields.many2one('res.users', 'Salesperson', select=True, track_visibility='onchange'),
        'current_date': fields.datetime('Date',Readonly=True),
        'product_line': fields.one2many('product.template','crm_lead_id',string="Products"),

        # Fields for address, due to separation from crm and res.partner
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
        'company_id': fields.many2one('res.company', 'Company', select=1),
        'payment_mode': fields.many2one('crm.payment.mode', 'Payment Mode', \
                            domain="[('section_id','=',section_id)]"),
        'planned_cost': fields.float('Planned Costs'),
        'meeting_count': fields.function(_meeting_count, string='# Meetings', type='integer'),
    }

    _defaults = {
        'active': 1,
        'type': 'lead',
        'current_date': fields.datetime.now
    }
