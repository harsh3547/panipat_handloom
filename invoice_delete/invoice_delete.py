# -*- coding: utf-8 -*-
#/#############################################################################
#
#    InnoTERE GmbH
#    Copyright (C) 2011-today InnoTERE GmbH (<http://www.innotere.de>)
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
#/#############################################################################
from openerp import models, fields, api, _
from openerp.exceptions import Warning
import datetime
import base64

class res_company(models.Model):
	_inherit = 'res.company'

	write_off_income_ac_id = fields.Many2one('account.account', string='Write Off Income Account')
	write_off_expense_ac_id = fields.Many2one('account.account', string='Write Off Expense Account')
	write_off_journal_id = fields.Many2one('account.journal', string="Write off Journal")
	
class account_invoice(models.Model):
	_inherit = 'account.invoice'
	_description = "Invoice"
	
	@api.multi
	def delete_paid_invoice(self):
		self.edit_paid_invoice()
		for invoice in self:
			invoice.write({'internal_number':False})

	@api.multi
	def edit_paid_invoice(self):
		report_name = self.env['report'].get_pdf(self, 'panipat_handloom.customer_report_invoice')
		result = base64.b64encode(report_name)
		
		vou = self.env['account.voucher'].search([('number','in',[v.move_id.name for v in self.payment_ids])])
		voucher_report_name = self.env['report'].get_pdf(vou, 'panipat_handloom.report_account_voucher')
		voucher_result = base64.b64encode(voucher_report_name)
		vou_number=",".join([v.number for v in vou])
		#print report_name
		#print voucher_report_name
		self.env['account.invoice.deleted'].create({'invoice_no':self.number+".pdf", 'invoice_pdf': result, 'vouchar_no':vou_number+".pdf", 'vouchar_pdf':voucher_result})
		for invoice in self:
			moves = self.env['account.move'].search([('name','=',invoice.number)])
			print "-=-moves=-=-",moves
			for mm in moves.line_id:
				print "-=-=mm-=-=",mm
				if mm.reconcile_ref:
					print "-=-mm.reconcile_ref=-=-",mm.reconcile_ref
					m = self.env['account.move.line'].search([('reconcile_ref','=',mm.reconcile_ref)])
					if m:
						print "=-=-=moves_to_reconcile=-=-=",m.ids
						moves_to_reconcile = m.ids
						moves_to_reconcile.remove(mm.id)
						print "=-=-=moves_to_reconcile=-=-=",moves_to_reconcile
			if moves:
				print "-=-moves=-=-",moves
				new_move = moves.copy(default={'ref':invoice.number+'write_off','name':invoice.number+'write_off'})
				print new_move
				#####account voucher lines missing move_line_id after invoice delete
				voucher_move_account_lines=[]
				for l in moves:
					for line in l.line_id:
						v_line=self.env['account.voucher.line'].search([('move_line_id','=',line.id)])
						if v_line:
							for vline in v_line:
								voucher_move_account_lines.append([vline,line.name,line.account_id.id,line.credit,line.debit])
				#####account voucher lines missing move_line_id after invoice delete
				moves.button_cancel()
				new_move_lines = self.env['account.move.line'].search([('move_id','=',new_move.id)])
				print "-=-new_move_lines=-=",new_move_lines
				move_lines = self.env['account.move.line'].search([('move_id','=',moves.id)])
				print "=-=-move_lines=-=-",move_lines
				obj_move_line = self.env['account.move.line']
				obj_move_line._remove_move_reconcile(move_lines.ids)
				for m in new_move_lines:
					print "0-0--0-m-0-0-",m
					move_c = m.copy()
					print "0-0--0-m copy-0-0-",move_c
					move_c.tax_code_id = False
					#####account voucher lines missing move_line_id after invoice delete
					for vcl in voucher_move_account_lines:
						if vcl[1]==move_c.name and vcl[2]==move_c.account_id.id and vcl[3]==move_c.credit and vcl[4]==move_c.debit:
							vcl[0].move_line_id=move_c.id
					#####
					m.unlink()
					if not invoice.company_id.write_off_journal_id:
						raise Warning(_('please configure write of journal on company.'))
					move_c.journal_id = invoice.company_id.write_off_journal_id.id
					partner = move_c.partner_id
					print "-=-=partner=--=",partner
					print "-=-move_c.account_id-=-",move_c.account_id
					print "=-=-move_c.partner_id.property_account_receivable-=-=",move_c.partner_id.property_account_receivable
					if invoice.type in ('out_invoice','out_refund') and move_c.account_id != move_c.partner_id.property_account_receivable:
						
						if not invoice.company_id.write_off_income_ac_id:
							raise Warning(_('please configure write off income account on company.'))
						
						move_c.account_id = invoice.company_id.write_off_income_ac_id.id
					
					if invoice.type in ('in_invoice','in_refund') and move_c.account_id != move_c.partner_id.property_account_payable:
						
						if not invoice.company_id.write_off_expense_ac_id:
							raise Warning(_('please configure write off expense account on company.'))
						
						move_c.account_id = invoice.company_id.write_off_expense_ac_id.id
					moves_to_reconcile.append(move_c.id)
					print "-=-=moves_to_reconcile-=-",moves_to_reconcile
					move_c.ref = ''
				#rec_move_lines1 = self.env['account.move.line'].search([('reconcile_ref','=',False),('ref','!=',invoice.number),('account_id','=',partner.property_account_receivable.id)])
				if invoice.type in ('out_invoice','out_refund'):
					print "property_account_receivable",partner.property_account_receivable.id,moves_to_reconcile
					rec_move_lines1 = self.env['account.move.line'].search([('id','in',moves_to_reconcile),('account_id','=',partner.property_account_receivable.id)])
				if invoice.type in ('in_invoice','in_refund'):
					rec_move_lines1 = self.env['account.move.line'].search([('id','in',moves_to_reconcile),('account_id','=',partner.property_account_payable.id)])
				print "=-=rec_move_lines1=-=",rec_move_lines1
				#voucher_lines_new_move_line_ids=list(set(map(int,rec_move_lines1 or []).difference(set(reconcile_pmt_move_lines)))
				print "check0000000000000000"
				rec_move_lines1.reconcile()
				print "check11111111111"
				new_move.button_validate()
				print "check22222222222222"
			invoice.action_cancel()
			print "check333333333333333333"
			#invoice.write({'internal_number':False})
		return True
		
class account_invoice_deleted(models.Model):
	_name = "account.invoice.deleted"
	_description = "Invoice Deleted"
	
	invoice_no = fields.Char(string="Invoice No")
	invoice_pdf = fields.Binary(string="Invoice PDF")
	vouchar_no = fields.Char(string="Vouchar No")
	vouchar_pdf = fields.Binary(string="Vouchar PDF")
	
	@api.multi
	def name_get(self):
		result = []
		for inv in self:
			if self.invoice_no:
				result.append((inv.id, "%s" % (self.invoice_no)))
			else:
				result.append((inv.id, "%s" % (self.vouchar_no)))
		return result

