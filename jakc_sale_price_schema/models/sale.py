from datetime import datetime, timedelta
import time
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
from openerp import workflow

class sale_order_line(osv.Model):
    _inherit = 'sale.order.line'
    
    _columns = {
        'iface_allow_return': fields.boolean("Allow Return"),
    }    
    
    def price_schema_product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, 
            fiscal_position=False, flag=False, context=None):
        
        context = context or {}
        lang = lang or context.get('lang', False)
        if not partner_id:
            raise osv.except_osv(_('No Customer Defined!'), _('Before choosing a product,\n select a customer in the sales form.'))
        warning = False
        
        product_uom_obj = self.pool.get('product.uom')
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        sale_price_schema_obj = self.pool.get('sale.price.schema')
        sale_price_schema_line_obj = self.pool.get('sale.price.schema.line')
        
        sale_config_settings = self.pool.get('sale.config.settings')
        #sale_config_ids = sale_config_settings.search(cr, uid, [], order='id desc', limit=1)
        #sale_config = sale_config_settings.browse(cr,uid,sale_config_ids[0])
        
        
        partner = partner_obj.browse(cr, uid, partner_id)
        lang = partner.lang
        context_partner = context.copy()
        context_partner.update({'lang': lang, 'partner_id': partner_id})

        if not product:
            return {'value': {'th_weight': 0,
                'product_uos_qty': qty}, 'domain': {'product_uom': [],
                   'product_uos': []}}
        if not date_order:
            date_order = time.strftime(DEFAULT_SERVER_DATE_FORMAT)

        result = {}
        warning_msgs = ''
        product_obj = product_obj.browse(cr, uid, product, context=context_partner)

        uom2 = False
        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom)
            if product_obj.uom_id.category_id.id != uom2.category_id.id:
                uom = False
        if uos:
            if product_obj.uos_id:
                uos2 = product_uom_obj.browse(cr, uid, uos)
                if product_obj.uos_id.category_id.id != uos2.category_id.id:
                    uos = False
            else:
                uos = False

        fpos = False
        if not fiscal_position:
            fpos = partner.property_account_position or False
        else:
            fpos = self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position)

        #Product Price from Price Schema
        iface_price_schemas = True
        
        if not iface_price_schemas:
            if uid == SUPERUSER_ID and context.get('company_id'):
                taxes = product_obj.taxes_id.filtered(lambda r: r.company_id.id == context['company_id'])
            else:
                taxes = product_obj.taxes_id
            
            result['tax_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, taxes, context=context)
        else:
            merk_id = product_obj.merk_id.id
            args = [('merk_id','=',merk_id),('start_date','<=', datetime.now()),('state','=','open')]
            sale_price_schema_ids = sale_price_schema_obj.search(cr, uid, args, context=context)
            if sale_price_schema_ids and partner.iface_ptkp == True:
                sale_price_schema_id = sale_price_schema_obj.browse(cr, uid, sale_price_schema_ids[0], context=context)
                taxes = sale_price_schema_id.tax_id
            else:
                taxes = None
            
            result['tax_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, taxes, context=context)
            
        if not flag:
            result['name'] = self.pool.get('product.product').name_get(cr, uid, [product_obj.id], context=context_partner)[0][1]
            if product_obj.description_sale:
                result['name'] += '\n'+product_obj.description_sale
        domain = {}
        if (not uom) and (not uos):
            result['product_uom'] = product_obj.uom_id.id
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
                uos_category_id = product_obj.uos_id.category_id.id
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                uos_category_id = False
            result['th_weight'] = qty * product_obj.weight
            domain = {'product_uom':
                        [('category_id', '=', product_obj.uom_id.category_id.id)],
                        'product_uos':
                        [('category_id', '=', uos_category_id)]}
        elif uos and not uom: # only happens if uom is False
            result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id
            result['product_uom_qty'] = qty_uos / product_obj.uos_coeff
            result['th_weight'] = result['product_uom_qty'] * product_obj.weight
        elif uom: # whether uos is set or not
            default_uom = product_obj.uom_id and product_obj.uom_id.id
            q = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
            result['th_weight'] = q * product_obj.weight        # Round the quantity up

        if not uom2:
            uom2 = product_obj.uom_id
        # get unit price

        if not pricelist:
            warn_msg = _('You have to select a pricelist or a customer in the sales form !\n'
                    'Please set one before choosing a product.')
            warning_msgs += _("No Pricelist ! : ") + warn_msg +"\n\n"
        else:
            ctx = dict(
                context,
                uom=uom or result.get('product_uom'),
                date=date_order,
            )
            
            if not iface_price_schemas:
                price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                        product, qty or 1.0, partner_id, ctx)[pricelist]
                        
                if price is False:
                    warn_msg = _("Cannot find a pricelist line matching this product and quantity.\n"
                            "You have to change either the product, the quantity or the pricelist.")
    
                    warning_msgs += _("No valid pricelist line found ! :") + warn_msg +"\n\n"
                else:
                    price = self.pool['account.tax']._fix_tax_included_price(cr, uid, price, taxes, result['tax_id'])
                    result.update({'price_unit': price})
                    if context.get('uom_qty_change', False):
                        values = {'price_unit': price}
                        if result.get('product_uos_qty'):
                            values['product_uos_qty'] = result['product_uos_qty']
                        return {'value': values, 'domain': {}, 'warning': False}
            else:
                sale_price_schema_ids = sale_price_schema_obj.search(cr, uid, [('merk_id','=',merk_id)], context=context)
                if not sale_price_schema_ids:
                    raise osv.except_osv(_('No Price Schema Defined!'), _('Before choosing a product,\n make sure price schema defined for this product.'))
                
                product_category_id = product_obj.categ_id.id
                
                if not product_category_id:
                    raise osv.except_osv(_('No Price Schema Defined!'), _('Before choosing a product,\n make sure internal category defined for this product.'))
                
                
                partner_category_id = partner.category_id[0].id or False
                if not partner_category_id:
                    raise osv.except_osv(_('No Price Schema Defined!'), _('Before choosing a product,\n make sure customer tags defined for the customer.'))
                
                
                args = [('sale_price_schema_id','=', sale_price_schema_ids[0]),('product_category_id','=',product_category_id),('partner_category_id','=',partner_category_id),('state','=','open')]
                sale_price_schema_line_ids  = sale_price_schema_line_obj.search(cr, uid, args, context=context)
                if not sale_price_schema_line_ids:
                    raise osv.except_osv(_('No Price Schema Defined!'), _('Before choosing a product,\n make sure price schema already defined'))

                sale_price_schema_line_id = sale_price_schema_line_obj.browse(cr, uid, sale_price_schema_line_ids[0],context=context)
                if context.get('allow_return') == True:
                    price = sale_price_schema_line_id.price_allow_return
                else:    
                    price = sale_price_schema_line_id.price_after_tax
                
                result.update({'price_unit': price})
                
                if context.get('uom_qty_change', False):
                    values = {'price_unit': price}
                    if result.get('product_uos_qty'):
                        values['product_uos_qty'] = result['product_uos_qty']
                    return {'value': values, 'domain': {}, 'warning': False}
                
                
        if warning_msgs:
            warning = {
                       'title': _('Configuration Error!'),
                       'message' : warning_msgs
                    }
        return {'value': result, 'domain': domain, 'warning': warning}
