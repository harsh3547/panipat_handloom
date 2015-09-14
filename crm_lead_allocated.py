from openerp.osv import fields, osv
from datetime import datetime

class crm_lead_allocated(osv.osv):
    _name = "crm.lead.allocated"
    _rec_name = "allocation_no"
    
    def schedule_employee(self,cr,uid,id,context=None):
        seq ="/"
        alloc_no = self.read(cr,uid,id,['allocation_no'],context=None)
        if alloc_no[0].get('allocation_no','/') == "/" :
            seq=self.pool.get('ir.sequence').get(cr,uid,'CRM.Lead.Allocation.No',context=None) or '/'
        self.write(cr,uid,id,{'state':'ongoing',
                              'allocation_no':seq},context=None)
        order_no = self.read(cr,uid,id,['sequence'],context=None)
        crm_obj = self.pool.get('panipat.crm.lead')
        crm_id = crm_obj.search(cr,uid,[('sequence','=',order_no[0].get('sequence')[1])],context=None)
        crm_obj.write(cr,uid,crm_id,{'allocation_no':id[0]},context=None)
        return True
    
    def quotation(self,cr,uid,id,context=None):
        return True
    
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'create_date': fields.datetime('Creation Date', readonly=True),
        'description': fields.text('Notes'),
        'allocation_no': fields.char(string="Allocation No."),
        'sequence':fields.many2one('panipat.crm.lead',string="Order No."),
        'employee_line': fields.one2many('panipat.employee','crm_lead_allocated_id',string="Employees"),
        'state': fields.selection(string="State",selection=[('draft','Draft'),('ongoing','Ongoing'),('done','Done')]),
                }
    
    _defaults = {
        'allocation_no':'/',
    }