from openerp import models, fields


AVAILABLE_PRODUCT_STATE = [
    ('draft','In Development'),
    ('sellable','Normal'),
    ('end','End of Lifecyle'),
    ('obsolete','Obsolete'),
    ('non_active','Non Active'),
]
class Product_merk(models.Model):
    _name = 'product.merk'
    name = fields.Char('Merk', size=50, required=True)
    
    
class Product_template(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'
    merk_id = fields.Many2one('product.merk','Merk')
    state = fields.Selection(AVAILABLE_PRODUCT_STATE,'Status')
    
    
