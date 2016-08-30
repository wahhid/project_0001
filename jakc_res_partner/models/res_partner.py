from openerp import models, fields, api

class res_partner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"
    iface_ptkp = fields.Boolean('PTKP', default=False)
    
    
    