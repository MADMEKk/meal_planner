from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Recipe, RecipeRating
from .serializers import RecipeSerializer

class RecipeModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.recipe = Recipe.objects.create(
            title='Test Recipe',
            description='Test Description',
            ingredients=[
                {'name': 'ingredient1', 'amount': 100, 'unit': 'g'},
                {'name': 'ingredient2', 'amount': 200, 'unit': 'ml'}
            ],
            instructions=['Step 1', 'Step 2'],
            calories_per_serving=300,
            protein=20,
            carbs=30,
            fat=10,
            created_by=self.user
        )

    def test_recipe_creation(self):
        self.assertEqual(self.recipe.title, 'Test Recipe')
        self.assertEqual(len(self.recipe.ingredients), 2)
        self.assertEqual(len(self.recipe.instructions), 2)

    def test_recipe_str(self):
        self.assertEqual(str(self.recipe), 'Test Recipe')

class RecipeAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.recipe_data = {
            'title': 'API Test Recipe',
            'description': 'API Test Description',
            'ingredients': [
                {'name': 'ingredient1', 'amount': 100, 'unit': 'g'}
            ],
            'instructions': ['Step 1'],
            'calories_per_serving': 300,
            'protein': 20,
            'carbs': 30,
            'fat': 10
        }
        
        self.recipe = Recipe.objects.create(
            **self.recipe_data,
            created_by=self.user
        )

    def test_get_recipes(self):
        url = reverse('recipe-list')
        response = self.client.get(url)
        recipes = Recipe.objects.all()
        serializer = RecipeSerializer(recipes, many=True)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_recipe(self):
        url = reverse('recipe-list')
        response = self.client.post(url, self.recipe_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Recipe.objects.count(), 2)
        self.assertEqual(Recipe.objects.latest('id').title, 'API Test Recipe')

    def test_filter_recipes_by_calories(self):
        url = reverse('recipe-list')
        response = self.client.get(url, {'max_calories': 400})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_rate_recipe(self):
        url = reverse('recipe-rate', kwargs={'pk': self.recipe.id})
        rating_data = {
            'rating': 5,
            'comment': 'Great recipe!'
        }
        response = self.client.post(url, rating_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(RecipeRating.objects.count(), 1)
        self.assertEqual(RecipeRating.objects.first().rating, 5)
