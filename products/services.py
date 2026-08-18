from .repositories import ProductRepository


def restock_product(product_id, quantity):
    product = ProductRepository.get_by_id(product_id)
    product.stock += quantity
    product.save()
    return product


def low_stock_products():
    return ProductRepository.get_low_stock()


def out_of_stock_products():
    return ProductRepository.get_out_of_stock()