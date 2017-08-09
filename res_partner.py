from openerp import models, fields, api, _
import datetime

class res_partner(models.Model):
    _inherit='res.partner'
    
    @api.one
    @api.depends()
    def _get_unreconciled_balance(self):
        ids=[]
        partner_id = self.id
        journal = self.env['account.journal'].search([('type','in',('cash','bank'))],limit=1)
        journal_id=False
        if journal:journal_id=journal.id
        amount=0.0
        currency_id = self.env['res.company'].search([],limit=1).currency_id.id
        ttype = 'receipt'
        date = datetime.datetime.today().strftime("%Y-%m-%d")
        ctx=self._context.copy()
        ctx.update({'date': date,'type': 'receipt', 'search_default_customer': 1})

        #print "---------recompute_voucher_lines(self._cr, self._uid,partner_id, journal_id,currency_id, ttype, date_var, context=ctx)--------------------",self._cr, self._uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, ctx

        res = self.pool.get('account.voucher').recompute_voucher_lines(self._cr, self._uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=ctx)
        balance=0.0
        if res.get('value',0) and res.get('value',0).get('line_dr_ids',0):
            for pay in res['value']['line_dr_ids']:
                if pay:balance += pay.get('amount_unreconciled',0.0)
        self.unreconciled_balance=balance

    unreconciled_balance =fields.Float(compute='_get_unreconciled_balance',string="Unreconciled Balance")

    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        #args = args or []
        res = super(res_partner,self).name_search(name=name, args=args, operator=operator, limit=limit)
        print "---in name_search  res_partner---",res
        recs=[]
        if not recs:
            rec_objs = self.search([('mobile', '=', name)] + args, limit=limit)
            recs += [rec_obj.id for rec_obj in rec_objs]
        if not recs:
            rec_objs = self.search([('mobile', operator, name)] + args, limit=limit)
            recs += [rec_obj.id for rec_obj in rec_objs]
        if not recs:
            rec_objs = self.search([('phone', '=', name)] + args, limit=limit)
            recs += [rec_obj.id for rec_obj in rec_objs]
        if not recs:
            rec_objs = self.search([('phone', operator, name)] + args, limit=limit)
            recs += [rec_obj.id for rec_obj in rec_objs]
        if not recs:
            rec_objs = self.search([('email', '=', name)] + args, limit=limit)
            recs += [rec_obj.id for rec_obj in rec_objs]
        if not recs:
            rec_objs = self.search([('email', operator, name)] + args, limit=limit)
            recs += [rec_obj.id for rec_obj in rec_objs]
        for res_ids in res:
            recs.append(res_ids[0])
        recs=list(set(recs))
        rec_objs=self.browse(recs)   
        return rec_objs.name_get()


    @api.multi
    def name_get(self):
        #print " ----------in name _get in res_partner------------------",self
        res=super(res_partner,self).name_get()
        result=[]
        for partner in res:
            #print "----in loop res---",partner
            partner_obj=self.browse(partner[0])
            if partner_obj.mobile:
                result.append((partner[0],partner[1]+' ('+str(partner_obj.mobile)+')'))
            elif partner_obj.phone:
                result.append((partner[0],partner[1]+' ('+str(partner_obj.phone)+')'))
            elif partner_obj.email:
                result.append((partner[0],partner[1]+' ('+str(partner_obj.email)+')'))
            else:
                result.append((partner[0],partner[1]))
        
        
        #print " ----------in name _get in res_partner---------resresrsresres---------",res
        #print " ----------in name _get in res_partner---------resresrsresresultultult---------",result
        return result
        