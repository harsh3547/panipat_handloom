# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm
from datetime import datetime

class stock_picking(models.Model):
    _inherit="stock.picking"
    
    installation_job=fields.Many2one(comodel_name='panipat.install', string='Installation Job')
    
    @api.multi
    def button_install_job(self):
        if self.picking_type_id.id != self.env.ref('stock.warehouse0').out_type_id.id:
            raise except_orm(('Warning'),('Installation Job only for Delivery Orders'))
        product_lines=[]
        for line in self.move_lines:
            line_id = {
                'name':line.product_id.name_get()[0][1],
                'product_uom_qty':line.product_uom_qty,
                'product_id': line.product_id.id,
                'product_uom': line.product_uom.id,
                    }
            product_lines.append((0,0,line_id))
            
        vals={'origin':self.origin+":"+self.name if self.origin else self.name,
              'schedule_date':self.min_date,
              'order_group':self.group_id.id,
              'customer':self.partner_id.id,
              'product_lines':product_lines,
              }
        self.installation_job=self.env['panipat.install'].create(vals)
        return True
    
    @api.multi
    def view_install_job(self):
        if self.installation_job:
            return {
                'name': 'Installation Works Invoice',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'panipat.install',
                'type': 'ir.actions.act_window',
                'res_id': self.installation_job.id,
                }
        else:
            return {
                    'type': 'ir.actions.client',
                    'tag': 'action_warn',
                    'name': 'Warning',
                    'params': {
                               'title': 'Warning!',
                               'text': 'No Installation Job attached to this Delivery Order.',
                               }
                    }
    
    
    