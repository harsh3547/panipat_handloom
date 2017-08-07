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
    'depends': ['base','web_m2x_options','sale','purchase','stock','sale_stock',
                'hr','account','account_accountant','account_voucher','account_cancel',],
    'data': ['security/ir.model.access.csv',
             'res_config.xml',
             'res_partner.xml',
             'panipat_sequences.xml',
             'panipat_crm_lead_view.xml',
             'panipat_employee_view.xml',
             'order_group.xml',
             'sale_view.xml',
             'account_invoice_view.xml',
             'account_voucher.xml',
             'sample_file.xml',
             'data.xml',
             'brand_name.xml',
             'product_view.xml',
             'purchase_view.xml',
             'supplier_return.xml',
             'installation.xml',
             'template_label_report/product_tmpl_label_report.xml',
             'wizard/warning_wizard.xml',
             'invoice_delete/invoice_delete_view.xml',
             'challan_report/challan_report.xml',
             'challan_report/views/report_challan.xml',
             'account_voucher_qweb/views/layouts.xml',
             'account_voucher_qweb/views/report_account_voucher.xml',
             'account_voucher_qweb/views/report_menu.xml',
             'account_voucher_qweb/views/report_stockpicking.xml',
             'custom_report/views/report_invoice_inherit.xml',
             'custom_report/account_report.xml',
             'custom_report/multi_company/account_journal.xml',
             'custom_report/res_company_view.xml',
             'image_works/image_works_conf.xml',
             'web_sheet_full_width/view/qweb.xml',
             'account_invoice_rounding/res_config_view.xml',
             'account_invoice_rounding/account_view.xml',
             'order_group_report/order_group_report.xml',
             'order_group_report/order_group_report_view.xml',
             'sale_order_report.xml',
             'sample_file_report/sample_file_report.xml',
             'sample_file_report/views/report_file.xml',

             ],
    'demo': [],
    'test': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: