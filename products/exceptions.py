from users.exceptions import AppException

class ProductException(AppException):
    status_code = 400
    message = "Product error"
class ProductNotFoundException(ProductException):
    status_code = 404
    message = "Product not found"
class CategoryNotFoundException(ProductException):
    status_code = 404
    message = "Category not found"
    
