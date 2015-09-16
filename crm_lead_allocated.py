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
        print "-----------------------------",order_no
        seq_no = order_no[0].get('sequence',False)
        print "-----------------------------seq",seq_no
        crm_obj = self.pool.get('panipat.crm.lead')
        if seq_no:
            crm_id = crm_obj.search(cr,uid,[('sequence','=',seq_no)],context=None)
            crm_obj.write(cr,uid,crm_id,{'allocation_no':id[0]},context=None)
        return True
    
    def quotation(self,cr,uid,id,context=None):
        return True
    
    def unlink(self,cr,uid,ids,context):
        delete_ids = self.pool.get('panipat.employee').search(cr,uid,[('crm_lead_allocated_id','in',ids)],context=None)
        if delete_ids :
            self.pool.get('panipat.employee').unlink(cr,uid,delete_ids,context)
        return super(crm_lead_allocated,self).unlink(cr,uid,ids,context)
    
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