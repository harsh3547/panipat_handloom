from openerp.addons.web.http import Controller, route, request
from openerp.osv import osv
from openerp.addons.report.controllers.main import ReportController
from openerp import SUPERUSER_ID
import simplejson

class PTReportController(ReportController):
    
    @route(['/report/download'], type='http', auth="user")
    def report_download(self, data, token):
        res = super(PTReportController, self).report_download(data,token)
        try:
            requestcontent = simplejson.loads(data)
            url = requestcontent[0]
            #print url
            reportname = url.split('/report/pdf/')[1].split('?')[0]
            docids = None
            if '/' in reportname:
                reportname, docids = reportname.split('/')
            if docids:
                docids = [int(i) for i in docids.split(',')]
            print reportname,docids
            report_obj = request.registry.get('ir.actions.report.xml')
            report_id = report_obj.search(request.cr, SUPERUSER_ID,[('report_name','=',reportname)])
            model = report_obj.browse(request.cr,SUPERUSER_ID,report_id[0]).model
            names = ''
            if len(docids)<6 and len(docids)>0:
                obj = request.registry.get(model).browse(request.cr,SUPERUSER_ID,docids)
                for rec in obj:
                    try:
                        if rec.name:
                            names += rec.name+"_"
                    except:
                        pass
                    try:
                        if rec.number:
                            names += rec.number+"_"
                    except:
                        pass
            if names:
                res.headers.set('Content-Disposition', 'attachment; filename=%s.pdf;' % names)
            #print res,res.headers
            return res
        except Exception:
            return res
        
        