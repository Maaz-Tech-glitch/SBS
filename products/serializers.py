from rest_framework import serializers
from .models import Category, Product

# Category Serializer
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
        

# Product Serializer
class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name",read_only=True)
    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ['sku', 'barcode']
        
class RestockProductSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)
    
    
    
