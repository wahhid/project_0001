from openerp.osv import fields, osv
import logging
_logger = logging.getLogger(__name__)


class sale_configuration(osv.TransientModel):
    _name = 'sale.config.settings'
    _inherit = 'sale.config.settings'
    _columns = {
        'price_schema': fields.boolean('Using Price Schema to get Product Price')
    }
    
    

    

    
    

    