from decimal import Decimal
from django.conf import settings
from django.test import TestCase
from satchless.cart.models import Cart
from satchless.contrib.pricing.simpleqty.models import ProductPrice
from satchless.product.tests import DeadParrot, DeadParrotVariant
from satchless.pricing import Price, handler

from . import models

class ParrotTaxTest(TestCase):
    def setUp(self):
        self.macaw = DeadParrot.objects.create(slug='macaw',
                species="Hyacinth Macaw")
        self.cockatoo = DeadParrot.objects.create(slug='cockatoo',
                species="White Cockatoo")
        self.macaw_blue_a = self.macaw.variants.create(color='blue', looks_alive=True)
        self.macaw_blue_d = self.macaw.variants.create(color='blue', looks_alive=False)
        self.cockatoo_white_a = self.cockatoo.variants.create(color='white', looks_alive=True)
        self.cockatoo_green_a = self.cockatoo.variants.create(color='green', looks_alive=True)
        macaw_price = ProductPrice.objects.create(product=self.macaw, price=Decimal('10.0'))
        macaw_price.offsets.create(variant=self.macaw_blue_a, price_offset=Decimal('2.0'))
        cockatoo_price = ProductPrice.objects.create(product=self.cockatoo, price=Decimal('20.0'))
        cockatoo_price.offsets.create(variant=self.cockatoo_green_a, price_offset=Decimal('5.0'))
        # create tax groups
        self.vat8 = models.TaxGroup.objects.create(name="VAT 8%", rate=8, rate_name="8%")
        self.vat23 = models.TaxGroup.objects.create(name="VAT 23%", rate=23, rate_name="23%")
        self.vat8.products.add(self.macaw)
        # set the pricing pipeline
        settings.SATCHLESS_PRICING_HANDLERS = [
            'satchless.contrib.pricing.simpleqty.handler',
            'satchless.contrib.tax.flatgroups.handler',
            ]

    def test_nodefault(self):
        # these have 8% VAT
        self.assertEqual(handler.get_variant_price(self.macaw_blue_d, currency='PLN'),
                         Price(10, Decimal('10.80'), currency='PLN'))
        self.assertEqual(handler.get_variant_price(self.macaw_blue_a, currency='PLN'),
                         Price(12, Decimal('12.96'), currency='PLN'))
        # while these have no tax group, hence the tax is zero
        self.assertEqual(handler.get_variant_price(self.cockatoo_white_a, currency='PLN'),
                         Price(20, 20, currency='PLN'))
        self.assertEqual(handler.get_variant_price(self.cockatoo_green_a, currency='PLN'),
                         Price(25, 25, currency='PLN'))
        # same in cart
        cart = Cart.objects.create(typ='test')
        cart.set_quantity(self.macaw_blue_a, 3)
        cart.set_quantity(self.macaw_blue_d, 5)
        item_macaw_blue_a = cart.items.get(variant=self.macaw_blue_a)
        item_macaw_blue_d = cart.items.get(variant=self.macaw_blue_d)
        self.assertEqual(
                handler.get_cartitem_unit_price(item_macaw_blue_a, currency='PLN'),
                Price(12, Decimal('12.96'), currency='PLN'))
        self.assertEqual(
                handler.get_cartitem_unit_price(item_macaw_blue_d, currency='PLN'),
                Price(10, Decimal('10.80'), currency='PLN'))
        cart.set_quantity(self.cockatoo_white_a, 3)
        cart.set_quantity(self.cockatoo_green_a, 5)
        item_cockatoo_white_a = cart.items.get(variant=self.cockatoo_white_a)
        item_cockatoo_green_a = cart.items.get(variant=self.cockatoo_green_a)
        self.assertEqual(
                handler.get_cartitem_unit_price(item_cockatoo_white_a, currency='PLN'),
                Price(20, 20, currency='PLN'))
        self.assertEqual(
                handler.get_cartitem_unit_price(item_cockatoo_green_a, currency='PLN'),
                Price(25, 25, currency='PLN'))

    def test_default(self):
        self.vat23.default = True
        self.vat23.save()
        # these have 8% VAT
        self.assertEqual(handler.get_variant_price(self.macaw_blue_d, currency='PLN'),
                         Price(10, Decimal('10.80'), currency='PLN'))
        self.assertEqual(handler.get_variant_price(self.macaw_blue_a, currency='PLN'),
                         Price(12, Decimal('12.96'), currency='PLN'))
        # while these have default 23% VAT
        self.assertEqual(handler.get_variant_price(self.cockatoo_white_a, currency='PLN'),
                         Price(20, Decimal('24.60'), currency='PLN'))
        self.assertEqual(handler.get_variant_price(self.cockatoo_green_a, currency='PLN'),
                         Price(25, Decimal('30.75'), currency='PLN'))
        # same in cart
        cart = Cart.objects.create(typ='test')
        cart.set_quantity(self.macaw_blue_a, 3)
        cart.set_quantity(self.macaw_blue_d, 5)
        item_macaw_blue_a = cart.items.get(variant=self.macaw_blue_a)
        item_macaw_blue_d = cart.items.get(variant=self.macaw_blue_d)
        self.assertEqual(
                handler.get_cartitem_unit_price(item_macaw_blue_a, currency='PLN'),
                Price(12, Decimal('12.96'), currency='PLN'))
        self.assertEqual(
                handler.get_cartitem_unit_price(item_macaw_blue_d, currency='PLN'),
                Price(10, Decimal('10.80'), currency='PLN'))
        cart.set_quantity(self.cockatoo_white_a, 3)
        cart.set_quantity(self.cockatoo_green_a, 5)
        item_cockatoo_white_a = cart.items.get(variant=self.cockatoo_white_a)
        item_cockatoo_green_a = cart.items.get(variant=self.cockatoo_green_a)
        self.assertEqual(
                handler.get_cartitem_unit_price(item_cockatoo_white_a, currency='PLN'),
                Price(20, Decimal('24.60'), currency='PLN'))
        self.assertEqual(
                handler.get_cartitem_unit_price(item_cockatoo_green_a, currency='PLN'),
                Price(25, Decimal('30.75'), currency='PLN'))
