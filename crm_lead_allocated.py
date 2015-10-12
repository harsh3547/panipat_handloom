from openerp.osv import fields, osv
from datetime import datetime

class crm_lead_allocated(osv.osv):
    _name = "crm.lead.allocated"
    _rec_name = "allocation_no"
    
    def schedule_employee(self,cr,uid,id,context=None):
        self.write(cr,uid,id,{'state':'ongoing'},context=None)
        employee_ids=map(int,self.browse(cr,uid,id).employee_line or [])
        self.pool.get('panipat.employee').write(cr,uid,employee_ids,{'state':'done'},context)
        return True
    
    def quotation(self,cr,uid,id,context=None):
        vals = {}
        values = []
        self.write(cr,uid,id,{'state':'done'},context=None)
        
        read_dict = self.read(cr,uid,id,['sequence'],context=None)[0]
        sequence = read_dict.get('sequence','/')[1]
        lead_id = self.pool.get('panipat.crm.lead').search(cr,uid,[('sequence','=',sequence)],context=None)
        if lead_id:
            lead_obj = self.pool.get('panipat.crm.lead').browse(cr,uid,lead_id,context=None)
            if  lead_obj.product_line :
                for i in lead_obj.product_line :
                    values.append((0,0,{'product_id':i.product_id.id,
                                    'name':i.description,
                                    }))
            vals.update({'order_line':values})
            if lead_obj.partner_id.id:
                    vals.update({'partner_id':lead_obj.partner_id.id})  
        quotation_id = self.pool.get('sale.order').create(cr,uid,vals,context=None)
        
        return True
    
    def create(self,cr,uid,vals,context=None):
        if vals.get('allocation_no','/')=='/':
            seq=self.pool.get('ir.sequence').get(cr,uid,'CRM.Lead.Allocation.No',context=None) or '/'
            vals['allocation_no']=seq
        return super(crm_lead_allocated, self).create(cr,uid,vals,context)
    
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'create_date': fields.datetime('Creation Date', readonly=True),
        'description': fields.text('Notes'),
        'allocation_no': fields.char(string="Allocation No."),
        'order_group':fields.many2one('panipat.order.group',string="Order Group",readonly=True),
        'employee_line': fields.one2many('panipat.employee','crm_lead_allocated_id',string="Employees"),
        'state': fields.selection(string="State",selection=[('draft','Draft'),('ongoing','Ongoing'),('done','Done')]),
                }
    
    _defaults = {
        'allocation_no':'/',
        'state':'draft',
    }