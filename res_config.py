# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.service.server as abc
import os
        

class panipat_config_settings(osv.osv_memory):
    _name = 'panipat.config.settings'
    _inherit = 'res.config.settings'

    _columns={'update_query':fields.boolean(string="Update Query"),
    			'query':fields.text(string="Query"),
    			'result':fields.html(string="Result"),
    			'password':fields.char(string="Password")
    					}

    def execute_query(self,cr,uid,ids,context=None):
    	obj=self.browse(cr,uid,ids[0],context=None)
    	if obj.password == 'panipat_query':
    		result=''
    		cr.execute(str(obj.query))
    		if not obj.update_query:
    			res_fetchall=cr.fetchall()
    			result+=obj.query+'<br\>'
    			count=0
    			for rec in res_fetchall:
    				count+=1
    				result+='<b><u>'+str(count)+' --  </u></b>  '+str(rec)+'<br\>'
    		self.write(cr,uid,ids[0],{'result':result or 'update query'},context=context)
    	else:return True

    def restart_server(self, cr, uid, ids,context=None):
        print "-=-========server=-=-=-=-=",abc.server
        print "====os name===",os.name
        return abc.restart()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
