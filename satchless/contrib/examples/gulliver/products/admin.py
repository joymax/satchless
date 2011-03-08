# -*- coding:utf-8 -*-
from django.contrib import admin
from django.db.models.query import EmptyQuerySet
import django.db.models

from satchless.contrib.pricing import simpleqty
import satchless.product.models
import satchless.product.admin
import sale.models

from . import models
from . import widgets

class ImageInline(admin.TabularInline):
    formfield_overrides = {
        django.db.models.ImageField: { 'widget': widgets.AdminImageWidget },
    }
    class Media:
        css = {
            'all': ['css/admin.css']
        }

class ProductForm(satchless.product.admin.ProductForm):
    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            self.fields['main_image'].queryset = models.ProductImage.objects.filter(product=self.instance)
        else:
            self.fields['main_image'].queryset = EmptyQuerySet(model=models.ProductImage)

class ProductAdmin(satchless.product.admin.ProductAdmin):
    form = ProductForm

class ProductImageInline(ImageInline):
    extra = 4
    max_num = 4
    model = models.ProductImage
    sortable_field_name = "order"

class PriceInline(admin.TabularInline):
    model = simpleqty.models.ProductPrice

class DiscountInline(admin.TabularInline):
    model = sale.models.DiscountGroup.products.through
    max_num = 1

class CardiganVariantInline(admin.TabularInline):
    model = models.CardiganVariant

class CardiganAdmin(ProductAdmin):
    inlines = [ CardiganVariantInline, ProductImageInline ]

class DressVariantInline(admin.TabularInline):
    model = models.DressVariant

class DressAdmin(ProductAdmin):
    inlines = [ PriceInline, DiscountInline, DressVariantInline, ProductImageInline ]

class HatAdmin(ProductAdmin):
    inlines = [ PriceInline, DiscountInline, ProductImageInline ]

class JacketVariantInline(admin.TabularInline):
    model = models.JacketVariant

class JacketAdmin(ProductAdmin):
    inlines = [ PriceInline, DiscountInline, JacketVariantInline, ProductImageInline ]

class ShirtVariantInline(admin.TabularInline):
    model = models.ShirtVariant

class ShirtAdmin(ProductAdmin):
    inlines = [ ShirtVariantInline, ProductImageInline ]

class TrousersVariantInline(admin.TabularInline):
    model = models.TrousersVariant

class TrousersAdmin(ProductAdmin):
    inlines = [ TrousersVariantInline, ProductImageInline ]

class TShirtVariantInline(admin.TabularInline):
    model = models.TShirtVariant

class TShirtAdmin(ProductAdmin):
    inlines = [ TShirtVariantInline, ProductImageInline ]

class CategoryImageInline(ImageInline):
    model = models.CategoryImage

class CategoryWithImageAdmin(satchless.product.admin.CategoryAdmin):
   inlines = [ CategoryImageInline ]

admin.site.register(models.Cardigan, CardiganAdmin)
admin.site.register(models.Dress, DressAdmin)
admin.site.register(models.Hat, HatAdmin)
admin.site.register(models.Jacket, JacketAdmin)
admin.site.register(models.Shirt, ShirtAdmin)
admin.site.register(models.Trousers, TrousersAdmin)
admin.site.register(models.TShirt, TShirtAdmin)

admin.site.unregister(satchless.product.models.Category)
admin.site.register(satchless.product.models.Category, CategoryWithImageAdmin)
