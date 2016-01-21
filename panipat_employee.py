from openerp import models,fields, api
from datetime import datetime,timedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class panipat_employee(models.Model):
    _name = "panipat.employee"
    _rec_name = "employee_id"
    
    employee_id = fields.Many2one(comodel_name='hr.employee',string="Employee Name",ondelete='cascade',required=True)
    start_time = fields.Datetime(string='Start Time',required=True,default=fields.Datetime.now())
    delay_hours = fields.Float(string='Hours (hh:mm)',required=True,default=0.0)
    end_time = fields.Datetime(compute="_onchanges_time_hour",string="End Time",store=True)
    crm_lead_allocated_id = fields.Many2one(comodel_name='crm.lead.allocated',string="CRM Lead Allocated",ondelete='cascade',copy=False)
    notes = fields.Text("Internal Notes")
    state = fields.Selection(string="State",selection=[('draft','Draft'),('confirm','Confirmed')],default='draft')
    install_id = fields.Many2one(comodel_name='panipat.install', string="Installation Work",ondelete='cascade',copy=False)
    origin = fields.Char("Source Document",copy=False)
    
    @api.one
    def schedule_employee(self,origin=False):
        print self
        vals={'state':'confirm'}
        if origin:vals['origin']=origin
        self.write(vals)
        return True
    
    
    @api.depends('start_time','delay_hours')
    def _onchanges_time_hour(self):
        #print "-----in depends -_onchanges_time_hour----1"
        if self.start_time and self.delay_hours:
            #print "-=-=-=-=-=-=-=-=-=-",self.delay_hours,self.start_time
            self.end_time = (datetime.strptime(self.start_time, DEFAULT_SERVER_DATETIME_FORMAT)+timedelta(hours=self.delay_hours)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            #print "=-=-=-=-=-=",self.end_time
            
   