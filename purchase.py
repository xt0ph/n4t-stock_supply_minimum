# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Bool, Eval

__all__ = ['ProductSupplier', 'PurchaseRequest', 'CreatePurchase',
    'PurchaseLine']
__metaclass__ = PoolMeta


class ProductSupplier:
    __name__ = 'purchase.product_supplier'
    minimum_quantity = fields.Float('Minimum Quantity')


class PurchaseRequest:
    __name__ = 'purchase.request'
    minimum_quantity = fields.Function(fields.Float('Minimum Quantity'),
        'on_change_with_minimum_quantity')

    @fields.depends('supplier', 'product', 'uom')
    def on_change_with_minimum_quantity(self, name):
        Uom = Pool().get('product.uom')
        if not self.product:
            return
        for product_supplier in self.product.product_suppliers:
            if product_supplier.party == self.party:
                return Uom.compute_qty(self.product.purchase_uom,
                    product_supplier.minimum_quantity, self.uom)


class CreatePurchase:
    __name__ = 'purchase.request.create_purchase'

    @classmethod
    def compute_purchase_line(cls, request):
        line = super(CreatePurchase, cls).compute_purchase_line(request)
        line.quantity = max(line.quantity, request.minimum_quantity)
        return line


class PurchaseLine:
    __name__ = 'purchase.line'

    minimum_quantity = fields.Float('Minimum Quantity', readonly=True, states={
            'invisible': ~Bool(Eval('minimum_quantity')),
            },
        help='The quantity must be greater or equal than minimum quantity')

    @fields.depends('minimum_quantity')
    def on_change_product(self):
        minimum_quantity = self._get_minimum_quantity()
        if minimum_quantity and (not self.quantity or
                self.quantity < minimum_quantity):
            self.quantity = minimum_quantity
        else:
            minimum_quantity = None

        res = super(PurchaseLine, self).on_change_product()
        if minimum_quantity:
            res['minimum_quantity'] = minimum_quantity
            res['quantity'] = minimum_quantity
        else:
            res['minimum_quantity'] = None
        return res

    @fields.depends('minimum_quantity')
    def on_change_quantity(self):
        minimum_quantity = self._get_minimum_quantity()
        if (self.quantity and minimum_quantity and
                self.quantity < minimum_quantity):
            self.quantity = minimum_quantity
        else:
            minimum_quantity = None

        res = super(PurchaseLine, self).on_change_quantity()
        if minimum_quantity:
            res['minimum_quantity'] = minimum_quantity
            res['quantity'] = minimum_quantity
        else:
            res['minimum_quantity'] = None
        return res

    @fields.depends('product', '_parent_purchase.party', 'quantity', 'unit',
        'minimum_quantity')
    def _get_minimum_quantity(self):
        Uom = Pool().get('product.uom')
        if not self.product or not self.purchase.party:
            return
        for product_supplier in self.product.product_suppliers:
            if product_supplier.party == self.purchase.party:
                minimum_quantity = product_supplier.minimum_quantity
                uom_category = self.product.purchase_uom.category
                if (minimum_quantity and self.unit and
                        self.unit in uom_category.uoms):
                    return Uom.compute_qty(self.product.purchase_uom,
                        minimum_quantity, self.unit)
                return minimum_quantity
