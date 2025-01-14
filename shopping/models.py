from django.db import models
from django.contrib.auth.models import User
from meal_plans.models import MealPlan

class IngredientCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['display_order']
        verbose_name_plural = 'Ingredient Categories'

class ShoppingList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meal_plan = models.ForeignKey(MealPlan, on_delete=models.CASCADE, related_name='shopping_lists')
    name = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} for {self.meal_plan.name}"

    class Meta:
        ordering = ['-created_at']

class ShoppingListItem(models.Model):
    UNIT_CHOICES = [
        ('g', 'Grams'),
        ('kg', 'Kilograms'),
        ('ml', 'Milliliters'),
        ('l', 'Liters'),
        ('pcs', 'Pieces'),
        ('tbsp', 'Tablespoons'),
        ('tsp', 'Teaspoons'),
        ('cup', 'Cups'),
    ]

    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name='items')
    category = models.ForeignKey(IngredientCategory, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    quantity = models.FloatField()
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    is_purchased = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    estimated_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.quantity} {self.unit} of {self.name}"

    class Meta:
        ordering = ['category__display_order', 'name']

class PantryItem(models.Model):
    """Track ingredients the user already has"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(IngredientCategory, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    quantity = models.FloatField()
    unit = models.CharField(max_length=10, choices=ShoppingListItem.UNIT_CHOICES)
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.quantity} {self.unit} of {self.name}"

    class Meta:
        ordering = ['category__display_order', 'name']
        verbose_name_plural = 'Pantry Items'
