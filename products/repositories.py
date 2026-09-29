from .models import Product, Category
from .exceptions import ProductNotFoundException, CategoryNotFoundException


class ProductRepository:
    @staticmethod
    def get_by_id(product_id, tenant):
        try:
            return Product.objects.get(id=product_id, tenant=tenant)
        except Product.DoesNotExist:
            raise ProductNotFoundException()

    @staticmethod
    def get_low_stock(tenant, threshold=5):
        return Product.objects.filter(tenant=tenant, stock__lte=threshold)

    @staticmethod
    def get_out_of_stock(tenant):
        return Product.objects.filter(tenant=tenant, stock=0)


class ProductStockRepository:
    @staticmethod
    def get_locked_by_id(product_id, tenant):
        try:
            return Product.objects.select_for_update().get(id=product_id, tenant=tenant)
        except Product.DoesNotExist:
            raise ProductNotFoundException()


class CategoryRepository:
    @staticmethod
    def get_by_id(category_id, tenant):
        try:
            return Category.objects.get(id=category_id, tenant=tenant)
        except Category.DoesNotExist:
            raise CategoryNotFoundException()