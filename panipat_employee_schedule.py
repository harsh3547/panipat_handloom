from openerp import models,fields, api
from datetime import datetime,timedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class panipat_employee_schedule(models.Model):

    
    _name = "panipat.employee.schedule"
    _rec_name = "employee_id"
    _order="start_time desc,state"
    
    employee_id = fields.Many2one(comodel_name='hr.employee',string="Employee Name",required=True)
    start_time = fields.Datetime(string='Start Time',required=True,default=fields.Datetime.now())
    delay_hours = fields.Float(string='Hours (hh:mm)',required=True,default=0.0)
    end_time = fields.Datetime(compute="_onchanges_time_hour",string="End Time",store=True)
    crm_lead_id = fields.Many2one(comodel_name='panipat.crm.lead',string="Panipat CRM Lead",ondelete='cascade',readonly=True)
    notes = fields.Text("Internal Notes")
    state = fields.Selection(string="State",selection=[('draft','Draft'),('confirm','Confirmed'),('done','Done'),('cancel','Cancelled')],default='draft')
    install_id = fields.Many2one(comodel_name='panipat.install', string="Installation Work",ondelete='cascade',readonly=True)
    origin = fields.Char("Source Document",copy=False)
    panipat_employee_link=fields.Many2one(comodel_name='panipat.employee')
    description = fields.Char('Description')
        
    @api.one
    def create_employee_from_schedule(self,override_vals=None):
        print self
        if override_vals==None:override_vals={}
        vals={"employee_id":self.employee_id.id,
            "start_time":self.start_time,
            "delay_hours":self.delay_hours,
            "end_time":self.end_time,
            "crm_lead_id":self.crm_lead_id.id,
            "notes":self.notes,
            "state":self.state,
            "install_id":self.install_id.id,
            "origin":self.origin,
            'description':self.description,
            "schedule_employee_link":self.id,
              }
        for rec in override_vals:
            vals[rec]=override_vals[rec]
        self.panipat_employee_link=self.env['panipat.employee'].create(vals).id
        self.write({'state':'confirm'})
        return True
    
    @api.one
    def done_employee_from_schedule(self):
        self.write({'state':'done'})
        if self.panipat_employee_link:self.panipat_employee_link.write({'state':'done'})
        return True
    
        
    @api.one
    def cancel_employee_from_schedule(self):
        self.write({'state':'cancel'})
        if self.panipat_employee_link:
            print "-0-----------000000000000000"
            self.panipat_employee_link.write({'state':'cancel'})
        return True
    
    @api.one
    def delete_employee_from_schedule(self):
        if self.panipat_employee_link:self.panipat_employee_link.unlink()
        return True
    
    @api.one
    @api.depends('start_time','delay_hours')
    def _onchanges_time_hour(self):
        #print "-----in depends -_onchanges_time_hour----1"
        if self.start_time and self.delay_hours:
            #print "-=-=-=-=-=-=-=-=-=-",self.delay_hours,self.start_time
            self.end_time = (datetime.strptime(self.start_time, DEFAULT_SERVER_DATETIME_FORMAT)+timedelta(hours=self.delay_hours)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            #print "=-=-=-=-=-=",self.end_time
            
   