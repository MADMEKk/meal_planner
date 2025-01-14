from django.test import TestCase

# Create your tests here.

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import timedelta
from .models import IngredientCategory, ShoppingList, ShoppingListItem, PantryItem
from meal_plans.models import MealPlan
from recipes.models import Recipe
from .serializers import ShoppingListSerializer, PantryItemSerializer

class ShoppingModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = IngredientCategory.objects.create(
            name='Produce'
        )
        self.meal_plan = MealPlan.objects.create(
            user=self.user,
            name='Test Plan',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=6)
        )
        self.shopping_list = ShoppingList.objects.create(
            user=self.user,
            name='Test Shopping List',
            meal_plan=self.meal_plan
        )
        self.shopping_item = ShoppingListItem.objects.create(
            shopping_list=self.shopping_list,
            category=self.category,
            name='Apples',
            quantity=5,
            unit='pieces'
        )
        self.pantry_item = PantryItem.objects.create(
            user=self.user,
            category=self.category,
            name='Oranges',
            quantity=3,
            unit='pieces'
        )

    def test_shopping_list_creation(self):
        self.assertEqual(self.shopping_list.name, 'Test Shopping List')
        self.assertEqual(self.shopping_list.user, self.user)
        self.assertEqual(self.shopping_list.meal_plan, self.meal_plan)

    def test_shopping_item_creation(self):
        self.assertEqual(self.shopping_item.name, 'Apples')
        self.assertEqual(self.shopping_item.quantity, 5)
        self.assertEqual(self.shopping_item.category, self.category)

    def test_pantry_item_creation(self):
        self.assertEqual(self.pantry_item.name, 'Oranges')
        self.assertEqual(self.pantry_item.quantity, 3)
        self.assertEqual(self.pantry_item.category, self.category)

class ShoppingAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create necessary objects
        self.category = IngredientCategory.objects.create(name='Produce')
        self.meal_plan = MealPlan.objects.create(
            user=self.user,
            name='Test Plan',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=6)
        )
        self.recipe = Recipe.objects.create(
            title='Test Recipe',
            ingredients=[
                {'name': 'Apples', 'amount': 2, 'unit': 'pieces', 'category': self.category.id}
            ],
            created_by=self.user
        )
        self.shopping_list = ShoppingList.objects.create(
            user=self.user,
            name='Test Shopping List',
            meal_plan=self.meal_plan
        )

    def test_create_shopping_list(self):
        url = reverse('shoppinglist-list')
        data = {
            'name': 'New Shopping List',
            'meal_plan': self.meal_plan.id
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ShoppingList.objects.count(), 2)

    def test_generate_from_meal_plan(self):
        url = reverse('shoppinglist-generate-from-meal-plan', kwargs={'pk': self.shopping_list.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(ShoppingListItem.objects.exists())

    def test_mark_item_purchased(self):
        item = ShoppingListItem.objects.create(
            shopping_list=self.shopping_list,
            category=self.category,
            name='Apples',
            quantity=5,
            unit='pieces'
        )
        
        url = reverse('shoppinglistitem-toggle-purchased', kwargs={'pk': item.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertTrue(item.is_purchased)

    def test_add_to_pantry(self):
        # Create a purchased item
        item = ShoppingListItem.objects.create(
            shopping_list=self.shopping_list,
            category=self.category,
            name='Apples',
            quantity=5,
            unit='pieces',
            is_purchased=True
        )
        
        url = reverse('shoppinglist-add-to-pantry', kwargs={'pk': self.shopping_list.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PantryItem.objects.filter(name='Apples').exists())

class PantryAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.category = IngredientCategory.objects.create(name='Produce')
        self.pantry_item = PantryItem.objects.create(
            user=self.user,
            category=self.category,
            name='Apples',
            quantity=5,
            unit='pieces',
            expiry_date=timezone.now().date() + timedelta(days=5)
        )

    def test_get_expiring_soon(self):
        url = reverse('pantryitem-expiring-soon')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_low_stock(self):
        # Create an item with low quantity
        PantryItem.objects.create(
            user=self.user,
            category=self.category,
            name='Oranges',
            quantity=0.1,  # Low stock
            unit='pieces'
        )
        
        url = reverse('pantryitem-low-stock')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only the low stock item
