from openerp.osv import fields, osv
from datetime import datetime

class crm_lead_allocated(osv.osv):
    _name = "crm.lead.allocated"
    
    def write(self,cr,uid,ids,vals,context=None):
        print "^^^^^^^^^^^^^^^^^^^^^^^^^^^",id,vals
        return super(panipat_crm_lead_allocation,self).write(cr,uid,ids,vals,context=None)
    
    def schedule_employee(self,cr,uid,id,context=None):
        return True
    
    def quotation(self,cr,uid,id,context=None):
        return True
     
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'create_date': fields.datetime('Creation Date', readonly=True),
        'scheduled_time': fields.datetime(string='Scheduled Time'),
        'scheduled_hours': fields.float(string='Scheduled Hours'),
        'description': fields.text('Notes'),
        'allocation_no': fields.char(string="Allocation No."),
        'sequence':fields.many2one('panipat.crm.lead',string="Order No."),
        'employee_line': fields.one2many('panipat.employee','crm_lead_allocated_id',string="Employees"),
        'state': fields.selection(string="State",selection=[('draft','Draft'),('ongoing','Ongoing'),('done','Done')]),
        
                }