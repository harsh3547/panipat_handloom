from openerp.osv import fields, osv
from datetime import datetime

class crm_lead_allocated(osv.osv):
    _name = "crm.lead.allocated"
    _rec_name = "allocation_no"
    
    def schedule_employee(self,cr,uid,id,context=None):
        self.write(cr,uid,id,{'state':'employee'},context=None)
        employee_ids=map(int,self.browse(cr,uid,id).employee_line or [])
        self.pool.get('panipat.employee').write(cr,uid,employee_ids,{'state':'done'},context)
        return True
    
    def make_quotation(self,cr,uid,id,context=None):
        vals = {}
        values = []
        
        order_group = self.browse(cr,uid,id,context).order_group.id
        lead_id = self.pool.get('panipat.crm.lead').search(cr,uid,[('order_group','=',order_group)],context=None)
        print " ==============lead_id===",lead_id
        if lead_id:
            lead_obj = self.pool.get('panipat.crm.lead').browse(cr,uid,lead_id[0],context=None)
            if lead_obj.product_line :
                for i in lead_obj.product_line :
                    values.append((0,0,{'product_id':i.product_id.id,
                                        'name':i.description,
                                        }))
                    vals.update({'order_line':values})
                    
            if lead_obj.partner_id and lead_obj.partner_id.id:
                vals.update({'partner_id':lead_obj.partner_id.id})  
            vals['order_group'] = order_group
            quotation_id = self.pool.get('sale.order').create(cr,uid,vals,context=None)
            self.write(cr,uid,id,{'state':'quotation_made'},context)
            return True
        else:
            return {
                    'type': 'ir.actions.client',
                    'tag': 'action_warn',
                    'name': 'Warning',
                    'params': {
                               'title': 'Warning!',
                               'text': 'No Lead is attached to this Allocation.',
                               }
                    }
    
    def view_quotation(self,cr,uid,id,context=None):
        vals = {}
        order_group = self.browse(cr,uid,id,context=None).order_group.id
        sale_ids = self.pool.get('sale.order').search(cr,uid,[('order_group','=',order_group)],context=None)
        if sale_ids :
            if len(sale_ids) == 1 :
                return {
                'name': 'Sale Order Form',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window',
                'res_id': sale_ids[0],
                }
            else :
                return {
                'name': 'Sale Order Form',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window',
                'domain':[('id','in',sale_ids)],
                }
        else :
            return {
                    'type': 'ir.actions.client',
                    'tag': 'action_warn',
                    'name': 'Warning',
                    'params': {
                               'title': 'Warning!',
                               'text': 'Quotation is not available or has been deleted .',
                               }
                    }
            
    
    
    
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
        'state': fields.selection(string="State",selection=[('draft','Draft'),('employee','Employee Scheduled'),('quotation_made','Quotation Made')]),
                }
    
    _defaults = {
        'allocation_no':'/',
        'state':'draft',
    }