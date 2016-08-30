from openerp import models, fields, api
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

AVAILABLE_STATES = [
    ('draft','New'),
    ('open','Open'),
    ('done','Close'),
    ('delete','Deleted'),
]

class sale_price_schema(models.Model):
    _name = "sale.price.schema"
    
    #@api.multi
    #def name_get(self):
    #    res = []
    #    merk_obj = self.env['product.merk']
    #    for sale_price_schema in self:
    #        merk = merk_obj.browse(sale_price_schema.merk_id)
    #        name = merk.name + " > " + sale_price_schema.start_date + " - " + sale_price_schema.end_date
    #        res.append(sale_price_schema.id, name)
    #    return res
    
    @api.multi
    def trans_generate(self):
        product_category_obj = self.env['product.category']
        partner_category_obj = self.env['res.partner.category']
        
        generated = self.iface_generated
        
        if not generated:
            vals = {}
            vals.update({'iface_generated':True})
            self.write(vals)
        
       
             
        product_categories = product_category_obj.search_read([],[])
        partner_categories = partner_category_obj.search_read([],[])
         
        for product_category in product_categories:
            for partner_category in partner_categories:
                vals = {}   
                vals.update({'sale_price_schema_id': self.id})
                vals.update({'product_category_id': product_category.get('id')})
                vals.update({'partner_category_id': partner_category.get('id')})
                vals.update({'price_after_tax': 0.0})
                self.env['sale.price.schema.line'].create(vals)
        
        return True
    
    @api.multi
    def trans_close(self):
        vals = {}
        vals.update({'state': 'done'})
        self.write(vals)
        return True
            
    name = fields.Char("Name", size=50, readonly=True)
    start_date = fields.Date("Start Date", required=True, index=True)
    end_date = fields.Date("End Date", required=True, index=True)
    merk_id = fields.Many2one("product.merk","Merk", required=True)
    tax_id = fields.Many2one("account.tax","Tax", required=True)
    iface_generated = fields.Boolean("Generated", default=False)
    sale_price_schema_line_ids = fields.One2many("sale.price.schema.line","sale_price_schema_id", "Price Schemas")
    state = fields.Selection(AVAILABLE_STATES,'Status',size=16, default='open', readonly=True)
    
    @api.model
    @api.returns('self', lambda value:value.id)
    def create(self, vals):
        start_date = vals.get('start_date')
        end_date = vals.get('end_date')
        merk = self.env['product.merk'].browse(vals.get('merk_id'))
        name  = merk.name + " - " + start_date + " - " + end_date
        vals.update({'name': name})
        return super(sale_price_schema, self).create(vals)
        
             
class sale_price_schema_line(models.Model):
    _name = "sale.price.schema.line"
    sale_price_schema_id = fields.Many2one("sale.price.schema", "Price Schema")
    product_category_id = fields.Many2one("product.category","Product Category", required=True)
    partner_category_id = fields.Many2one("res.partner.category", "Partner Category", required=True)
    price_after_tax = fields.Float("Price", required=True, default=0.0)
    price_allow_return = fields.Float("Price Allow Return", required=True, default=0.0)
    state = fields.Selection(AVAILABLE_STATES, 'Status', default='draft', required=True)
    
    
    