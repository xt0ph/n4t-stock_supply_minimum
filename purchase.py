#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['ProductSupplier', 'PurchaseRequest', 'CreatePurchase']
__metaclass__ = PoolMeta


class ProductSupplier:
    __name__ = 'purchase.product_supplier'
    minimum_quantity = fields.Float('Minimum Quantity')


class PurchaseRequest:
    __name__ = 'purchase.request'
    minimum_quantity = fields.Function(fields.Float('Minimum Quantity',
            on_change_with=['supplier', 'product']),
        'on_change_with_minimum_quantity')

    def on_change_with_minimum_quantity(self, name):
        if not self.product:
            return
        for product_supplier in self.product.product_suppliers:
            if product_supplier.party == self.party:
                return product_supplier.minimum_quantity


class CreatePurchase:
    __name__ = 'purchase.request.create_purchase'

    @classmethod
    def compute_purchase_line(cls, request):
        line = super(CreatePurchase, cls).compute_purchase_line(request)
        line.quantity = max(line.quantity, request.minimum_quantity)
        return line
