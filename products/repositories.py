from .models import Product, Category
from .exceptions import ProductNotFoundException, CategoryNotFoundException


class ProductRepository:
    @staticmethod
    def get_by_id(product_id):
        try:
            return Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise ProductNotFoundException()

    @staticmethod
    def get_low_stock(threshold=5):
        return Product.objects.filter(stock__lte=threshold)

    @staticmethod
    def get_out_of_stock():
        return Product.objects.filter(stock=0)


class CategoryRepository:
    @staticmethod
    def get_by_id(category_id):
        try:
            return Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            raise CategoryNotFoundException()