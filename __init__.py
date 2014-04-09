#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.
from trytond.pool import Pool
from .purchase import *


def register():
    Pool.register(
        ProductSupplier,
        PurchaseRequest,
        module='stock_supply_minimum', type_='model')
    Pool.register(
        CreatePurchase,
        module='stock_supply_minimum', type_='wizard')
