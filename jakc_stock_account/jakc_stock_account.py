from datetime import date
from openerp.osv import fields, osv
from openerp.tools.translate import _

class stock_invoice_onshipping(osv.osv_memory):
    _inherit = "stock.invoice.onshipping"
    
    _defaults = {
        'invoice_date' :  date.today().strftime('%Y-%m-%d'),
    }
    
