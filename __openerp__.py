# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

{
    'name': 'Panipat Handloom',
    'version': '0.1',
    'category': 'CRM',
    'sequence':1,
    'summary': 'Panipat Handloom',
    'description': """
    Panipat Handloom Management
    """,
    'author': 'J & G Infosystems',
    'website': 'www.jginfosystems.com',
    'depends': ['base','sale','account_voucher','web_m2x_options',
                'account_cancel','stock','purchase',],
    'data': [
             'panipat_sequences.xml',
             'panipat_crm_lead_view.xml',
             'panipat_employee_view.xml',
             'crm_lead_allocated_view.xml',
             'panipat_quotation_view.xml',
             'panipat_account_voucher_view.xml',
             'order_group.xml',
             'sale_view.xml',
             'account_invoice_view.xml',
             'sample_file.xml',
             'data.xml',
             'brand_name.xml',
             'product_view.xml',
             'supplier_return.xml',
             'product_label_mod.xml',
             'installation.xml',
             ],
    'demo': [],
    'test': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: