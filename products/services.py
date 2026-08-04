from .models import Product 


def restock_product(product_id,quantity):
    product = Product.objects.get(id=product_id)
    product.stock += quantity
    product.save()
    return product

def low_stock_products():
    return Product.objects.filter(stock__lte=5)

def out_of_stock_products():
    return Product.objects.filter(stock=0)
