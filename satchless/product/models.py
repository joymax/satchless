from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from localeurl.models import reverse
from mothertongue.models import MothertongueModelTranslate
from mptt.models import MPTTModel

from . import signals
from ..util.models import Subtyped

__all__ = ('ProductAbstract', 'Variant', 'Category', 'ProductAbstractTranslation', 'CategoryTranslation')

class DescribedModel(MothertongueModelTranslate):
    name = models.CharField(_('name'), max_length=128)
    description = models.TextField(_('description'), blank=True)
    meta_description = models.TextField(_('meta description'), blank=True,
            help_text=_("Description used by search and indexing engines"))
    translated_fields = ('name', 'description', 'meta_description')
    translation_set = 'translations'

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True


class DescribedModelTranslation(models.Model):
    language = models.CharField(max_length=5, choices=settings.LANGUAGES[1:])
    name = models.CharField(_('name'), max_length=128)
    description = models.TextField(_('description'), blank=True)
    meta_description = models.TextField(_('meta description'), blank=True,
            help_text=_("Description used by search and indexing engines"))

    def __unicode__(self):
        return "%s@%s" % (self.name, self.language)

    class Meta:
        abstract = True


class Category(MPTTModel, DescribedModel):
    slug = models.SlugField(max_length=50)
    parent = models.ForeignKey('self', null=True, blank=True,
                               related_name='children')

    def _parents_slug_path(self):
        parents = '/'.join(c.slug for c in self.get_ancestors())
        return '%s/' % parents if parents else ''

    @staticmethod
    def path_from_slugs(slugs):
        """
        Returns list of Category instances matchnig given slug path.
        """
        if len(slugs) == 0:
            return []
        leaves = Category.objects.filter(slug=slugs[-1])
        if not leaves:
            raise Category.DoesNotExist, "slug='%s'" % slugs[-1]
        for leaf in leaves:
            path = leaf.get_ancestors()
            if len(path) + 1 != len(slugs):
                continue
            if [c.slug for c in path] != slugs[:-1]:
                continue
            return list(path) + [leaf]
        raise Category.DoesNotExist

    @models.permalink
    def get_absolute_url(self):
        return ('satchless.product.views.category',
                (self._parents_slug_path(), self.slug))

    def get_url(self):
        """Uses reverse resolver, to force localeurl to add language code."""
        return reverse('satchless-product-category',
                args=(self._parents_slug_path(), self.slug))

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")


class CategoryTranslation(DescribedModelTranslation):
    category = models.ForeignKey(Category, related_name='translations')

    class Meta(object):
        unique_together = ('category', 'language')


class Product(Subtyped):
    """
    The base Product to rule them all. Provides slug, a powerful item to
    identify member of each tribe.
    """
    slug = models.SlugField(_('slug'), max_length=80,
            help_text=_('Slug will be used in the address of the product page. '
                        'It should be URL-friendly (letters, numbers, hyphens '
                        'and underscores only) and descriptive for the SEO '
                        'needs.'))
    categories = models.ManyToManyField(Category, related_name='products')

    def _get_url(self, category):
        if category:
            if self.categories.filter(pk=category.pk).exists():
                return ('satchless.product.views.product',
                        ('%s%s/' % (category._parents_slug_path(),
                                    category.slug),
                         self.slug))
            else:
                raise ValueError("Product %s not in category %s" % (self,
                                                                    category))
        return ('satchless-product-product', (self.slug, self.pk))

    @models.permalink
    def get_absolute_url(self):
        return self._get_url(category=None)

    def get_url(self, category=None):
        """Uses reverse resolver, to force localeurl to add language code."""
        view, args = self._get_url(category=category)
        return reverse(view, args=args)

    def sanitize_quantity(self, quantity):
        """
        Returns sanitized quantity. By default it rounds the value to the
        nearest integer.
        """
        return Decimal(quantity).quantize(1)

    def __unicode__(self):
        return self.slug


class ProductAbstract(DescribedModel, Product):
    """
    Base class for every product to inherit from.
    """
    class Meta:
        abstract = True


class ProductAbstractTranslation(DescribedModelTranslation):
    """
    Base class for product translations.
    """
    product = models.ForeignKey(Product, related_name='translations')

    class Meta:
        abstract = True


class NonConfigurableProductAbstract(ProductAbstract):
    """
    Base class for non-configurable products.
    Automatically creates a variant when created.
    """

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        super(NonConfigurableProductAbstract, self).save(*args, **kwargs)
        self.variants.get_or_create()


class Variant(Subtyped):
    """
    Base class for variants. It identifies a concrete product instance,
    which goes to a cart. Custom variants inherit from it.
    """
    sku = models.CharField(_('SKU'), max_length=128, blank=True,
                           help_text=_('ID of the product variant used '
                                       'internally in the shop.'))

    def __unicode__(self):
        return '%s' % self.sku
