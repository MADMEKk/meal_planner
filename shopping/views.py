from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import IngredientCategory, ShoppingList, ShoppingListItem, PantryItem
from .serializers import (
    IngredientCategorySerializer, ShoppingListSerializer,
    ShoppingListItemSerializer, PantryItemSerializer
)

class IngredientCategoryViewSet(viewsets.ModelViewSet):
    queryset = IngredientCategory.objects.all()
    serializer_class = IngredientCategorySerializer
    permission_classes = [IsAuthenticated]

class ShoppingListViewSet(viewsets.ModelViewSet):
    serializer_class = ShoppingListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ShoppingList.objects.filter(user=self.request.user)

    @action(detail=True, methods=['POST'])
    def generate_from_meal_plan(self, request, pk=None):
        """Generate shopping list items from a meal plan"""
        shopping_list = self.get_object()
        meal_plan = shopping_list.meal_plan
        
        # Get all meals in the plan
        meals = []
        for day in meal_plan.days.all():
            meals.extend(day.meals.all())

        # Create a dictionary to track ingredients
        ingredients_dict = {}

        # Process each meal
        for meal in meals:
            recipe = meal.recipe
            servings_multiplier = meal.servings / recipe.servings

            for ingredient in recipe.ingredients:
                key = (ingredient['name'], ingredient.get('unit'), ingredient.get('category'))
                current_amount = ingredients_dict.get(key, 0)
                ingredients_dict[key] = current_amount + (ingredient['amount'] * servings_multiplier)

        # Check pantry items and adjust quantities
        pantry_items = PantryItem.objects.filter(user=request.user)
        for pantry_item in pantry_items:
            key = (pantry_item.name, pantry_item.unit, pantry_item.category_id)
            if key in ingredients_dict:
                if pantry_item.quantity >= ingredients_dict[key]:
                    del ingredients_dict[key]
                else:
                    ingredients_dict[key] -= pantry_item.quantity

        # Create shopping list items
        for (name, unit, category_id), amount in ingredients_dict.items():
            ShoppingListItem.objects.create(
                shopping_list=shopping_list,
                category_id=category_id,
                name=name,
                quantity=amount,
                unit=unit
            )

        serializer = self.get_serializer(shopping_list)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'])
    def mark_all_purchased(self, request, pk=None):
        """Mark all items in the shopping list as purchased"""
        shopping_list = self.get_object()
        shopping_list.items.update(is_purchased=True)
        shopping_list.is_completed = True
        shopping_list.save()
        
        serializer = self.get_serializer(shopping_list)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'])
    def add_to_pantry(self, request, pk=None):
        """Add purchased items to pantry"""
        shopping_list = self.get_object()
        added_items = []

        for item in shopping_list.items.filter(is_purchased=True):
            # Check if item already exists in pantry
            pantry_item, created = PantryItem.objects.get_or_create(
                user=request.user,
                name=item.name,
                unit=item.unit,
                category=item.category,
                defaults={
                    'quantity': item.quantity
                }
            )
            
            if not created:
                # Update existing pantry item quantity
                pantry_item.quantity += item.quantity
                pantry_item.save()

            added_items.append(PantryItemSerializer(pantry_item).data)

        return Response(added_items)

class ShoppingListItemViewSet(viewsets.ModelViewSet):
    serializer_class = ShoppingListItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ShoppingListItem.objects.filter(shopping_list__user=self.request.user)

    @action(detail=True, methods=['POST'])
    def toggle_purchased(self, request, pk=None):
        """Toggle the purchased status of an item"""
        item = self.get_object()
        item.is_purchased = not item.is_purchased
        item.save()
        
        # Check if all items are purchased and update shopping list
        if item.is_purchased:
            shopping_list = item.shopping_list
            if not shopping_list.items.filter(is_purchased=False).exists():
                shopping_list.is_completed = True
                shopping_list.save()
        
        serializer = self.get_serializer(item)
        return Response(serializer.data)

class PantryItemViewSet(viewsets.ModelViewSet):
    serializer_class = PantryItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PantryItem.objects.filter(user=self.request.user)

    @action(detail=False, methods=['GET'])
    def expiring_soon(self, request):
        """Get items that are expiring within 7 days"""
        today = timezone.now().date()
        expiry_threshold = today + timezone.timedelta(days=7)
        
        items = self.get_queryset().filter(
            expiry_date__isnull=False,
            expiry_date__lte=expiry_threshold,
            expiry_date__gte=today
        ).order_by('expiry_date')
        
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def low_stock(self, request):
        """Get items that are running low (less than 20% of typical quantity)"""
        # This is a simple implementation. You might want to define "low stock"
        # differently based on your needs
        items = []
        for item in self.get_queryset():
            if item.quantity < 0.2:  # Assuming 1 is a typical quantity
                items.append(item)
        
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)
