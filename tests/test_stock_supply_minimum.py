#!/usr/bin/env python
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import datetime
import doctest
import unittest
from dateutil.relativedelta import relativedelta
from decimal import Decimal

import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT, test_view,\
    test_depends
from trytond.transaction import Transaction


class StockSupplyMinimumTestCase(unittest.TestCase):
    'Test StockSupplyMinimum module'

    def setUp(self):
        trytond.tests.test_tryton.install_module('stock_supply_minimum')
        self.user = POOL.get('res.user')
        self.uom = POOL.get('product.uom')
        self.category = POOL.get('product.category')
        self.template = POOL.get('product.template')
        self.product = POOL.get('product.product')
        self.company = POOL.get('company.company')
        self.party = POOL.get('party.party')
        self.account = POOL.get('account.account')
        self.payment_term = POOL.get('account.invoice.payment_term')
        self.purchase = POOL.get('purchase.purchase')
        self.purchase_line = POOL.get('purchase.line')
        self.location = POOL.get('stock.location')
        self.purchase_request = POOL.get('purchase.request')
        self.create_purchase = POOL.get('purchase.request.create_purchase',
            type='wizard')

    def test0005views(self):
        'Test views'
        test_view('stock_supply_minimum')

    def test0006depends(self):
        'Test depends'
        test_depends()

    def test0010request_create_purchase(self):
        '''
        Test minimum_quantity calculation in on_change_product and
        on_change_quantity in purchase.line
        '''
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            company, = self.company.search([
                    ('rec_name', '=', 'Dunder Mifflin'),
                    ])
            self.user.write([self.user(USER)], {
                'main_company': company.id,
                'company': company.id,
                })

            product, supplier = self.create_product_with_supplier(company)

            # Prepare purchase request
            today = datetime.date.today()
            warehouse, = self.location.search([('type', '=', 'warehouse')])

            # Check create purchase from request with less quantity than
            # minimum
            req_lt_minimum, req_gt_minimum = self.purchase_request.create([{
                        'product': product.id,
                        'party': supplier.id,
                        'quantity': 3,
                        'uom': product.purchase_uom.id,
                        'computed_quantity': 3,
                        'computed_uom': product.purchase_uom.id,
                        'purchase_date': today,
                        'supply_date': today + relativedelta(days=2),
                        'stock_level': 0,
                        'company': company.id,
                        'warehouse': warehouse.id,
                        'origin': 'stock.order_point,-1',
                        }, {
                        'product': product.id,
                        'party': supplier.id,
                        'quantity': 7,
                        'uom': product.purchase_uom.id,
                        'computed_quantity': 7,
                        'computed_uom': product.purchase_uom.id,
                        'purchase_date': today,
                        'supply_date': today + relativedelta(days=2),
                        'stock_level': 0,
                        'company': company.id,
                        'warehouse': warehouse.id,
                        'origin': 'stock.order_point,-1',
                        }])

            with Transaction().set_context(active_ids=[req_lt_minimum.id,
                        req_gt_minimum.id]):
                session_id, _, _ = self.create_purchase.create()
                create_purchase = self.create_purchase(session_id)
                create_purchase.transition_start()

            self.assertIsNotNone(req_lt_minimum.purchase_line)
            self.assertEqual(req_lt_minimum.purchase_line.quantity, 5)

            self.assertIsNotNone(req_gt_minimum.purchase_line)
            self.assertEqual(req_gt_minimum.purchase_line.quantity, 7)

    def create_product_with_supplier(self, company):
        # Prepare supplier
        receivable, = self.account.search([
            ('kind', '=', 'receivable'),
            ('company', '=', company.id),
            ])
        payable, = self.account.search([
            ('kind', '=', 'payable'),
            ('company', '=', company.id),
            ])
        payment_term, = self.payment_term.create([{
                    'name': 'Payment Term',
                    'lines': [
                        ('create', [{
                                    'sequence': 0,
                                    'type': 'remainder',
                                    'months': 0,
                                    'days': 0,
                                    }])]
                    }])
        supplier, = self.party.create([{
                    'name': 'supplier',
                    'addresses': [
                        ('create', [{}]),
                        ],
                    'account_receivable': receivable.id,
                    'account_payable': payable.id,
                    'supplier_payment_term': payment_term.id,
                    }])

        # Prepare product
        uom, = self.uom.search([
                ('name', '=', 'Unit'),
                ])
        category, = self.category.create([{'name': 'ProdCategoryTest'}])
        template, = self.template.create([{
                    'name': 'ProductTest',
                    'default_uom': uom.id,
                    'category': category.id,
                    'account_category': True,
                    'list_price': Decimal(0),
                    'cost_price': Decimal(15),
                    'purchasable': True,
                    'purchase_uom': uom.id,
                    'product_suppliers': [
                        ('create', [{
                                'company': company.id,
                                'party': supplier.id,
                                'delivery_time': 2,
                                'minimum_quantity': 5,
                                'prices': [
                                    ('create', [{
                                        'quantity': 0,
                                        'unit_price': Decimal(14),
                                        }]),
                                    ],
                                }]),
                        ],
                    }])
        product, = self.product.create([{
                    'template': template.id,
                    }])
        return product, supplier


def suite():
    suite = trytond.tests.test_tryton.suite()
    from trytond.modules.company.tests import test_company
    for test in test_company.suite():
        if test not in suite:
            suite.addTest(test)
    from trytond.modules.account.tests import test_account
    for test in test_account.suite():
        if test not in suite and not isinstance(test, doctest.DocTestCase):
            suite.addTest(test)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        StockSupplyMinimumTestCase))
    return suite
