from rest_framework import serializers
from .models import IngredientCategory, ShoppingList, ShoppingListItem, PantryItem

class IngredientCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = IngredientCategory
        fields = '__all__'

class ShoppingListItemSerializer(serializers.ModelSerializer):
    category = IngredientCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        source='category',
        queryset=IngredientCategory.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = ShoppingListItem
        fields = '__all__'

class ShoppingListSerializer(serializers.ModelSerializer):
    items = ShoppingListItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_purchased = serializers.SerializerMethodField()
    estimated_total_cost = serializers.SerializerMethodField()

    class Meta:
        model = ShoppingList
        fields = '__all__'
        read_only_fields = ('user',)

    def get_total_items(self, obj):
        return obj.items.count()

    def get_total_purchased(self, obj):
        return obj.items.filter(is_purchased=True).count()

    def get_estimated_total_cost(self, obj):
        total = sum(
            item.estimated_price or 0 
            for item in obj.items.all()
        )
        return round(total, 2)

    def create(self, validated_data):
        user = self.context['request'].user
        shopping_list = ShoppingList.objects.create(user=user, **validated_data)
        return shopping_list

class PantryItemSerializer(serializers.ModelSerializer):
    category = IngredientCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        source='category',
        queryset=IngredientCategory.objects.all(),
        required=False,
        allow_null=True
    )
    days_until_expiry = serializers.SerializerMethodField()

    class Meta:
        model = PantryItem
        fields = '__all__'
        read_only_fields = ('user',)

    def get_days_until_expiry(self, obj):
        if not obj.expiry_date:
            return None
        from django.utils import timezone
        import datetime
        today = timezone.now().date()
        delta = obj.expiry_date - today
        return delta.days

    def create(self, validated_data):
        user = self.context['request'].user
        pantry_item = PantryItem.objects.create(user=user, **validated_data)
        return pantry_item
