from openerp import models,fields, api
from datetime import datetime,timedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.exceptions import except_orm

class panipat_employee(models.Model):

    
    _name = "panipat.employee"
    _rec_name = "employee_id"
    _order="start_time desc,state"
    
    employee_id = fields.Many2one(comodel_name='hr.employee',string="Employee Name",required=True,readonly=True,states={'draft':[('readonly',False)]})
    start_time = fields.Datetime(string='Start Time',required=True,default=fields.Datetime.now(),states={'done':[('readonly',True)],'cancel':[('readonly',True)]})
    delay_hours = fields.Float(string='Hours (hh:mm)',required=True,default=0.0,states={'done':[('readonly',True)],'cancel':[('readonly',True)]})
    end_time = fields.Datetime(compute="_onchanges_time_hour",inverse="_inverse_time_hour",string="End Time",store=True,readonly=True)
    crm_lead_id = fields.Many2one(comodel_name='panipat.crm.lead',string="CRM Lead ",ondelete='cascade',copy=False,readonly=True)
    notes = fields.Text("Internal Notes")
    description = fields.Char('Description')
    state = fields.Selection(string="State",selection=[('draft','Draft'),('confirm','Pending'),('done','Done'),('cancel','Cancelled')],default='draft')
    install_id = fields.Many2one(comodel_name='panipat.install', string="Installation Work",ondelete='cascade',copy=False,readonly=True)
    origin = fields.Char("Source Document",copy=False,states={'done':[('readonly',True)],'cancel':[('readonly',True)]})
    schedule_employee_link=fields.Many2one(comodel_name='panipat.employee.schedule',copy=False,ondelete='cascade')
    # ondelete cascade because if panipat.employee.schedule (front face of employee scheduling) is deleted then this panipat.employee should also be deleted
    
    @api.multi
    def button_confirm(self):
        vals={'state':'confirm'}
        self.write(vals)
        return True
    
    @api.multi
    def button_done(self):
        vals={'state':'done'}
        self.write(vals)
        return True
    
    @api.multi
    def button_cancel(self):
        vals={'state':'cancel'}
        self.write(vals)
        return True
    
    @api.multi
    def button_to_draft(self):
        vals={'state':'draft'}
        self.write(vals)
        return True
    
    @api.multi
    def write(self, vals):
        if self.schedule_employee_link:
            self.schedule_employee_link.write(vals)
        return super(panipat_employee, self).write(vals)
    
    @api.one            
    @api.depends('start_time','delay_hours')
    def _onchanges_time_hour(self):
        #print "-----in depends -_onchanges_time_hour----1"
        if self.start_time and self.delay_hours:
            #print "-=-=-=-=-=-=-=-=-=-",self.delay_hours,self.start_time
            self.end_time = (datetime.strptime(self.start_time, DEFAULT_SERVER_DATETIME_FORMAT)+timedelta(hours=self.delay_hours)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            #print "=-=-=-=-=-=",self.end_time
            
   
    def _inverse_time_hour(self):
        a=datetime.strptime(self.start_time, DEFAULT_SERVER_DATETIME_FORMAT)
        if self.end_time:
            b=datetime.strptime(self.end_time, DEFAULT_SERVER_DATETIME_FORMAT)
            self.delay_hours=(b-a).total_seconds()/3600.0
        else:
            self.delay_hours=0.0
        