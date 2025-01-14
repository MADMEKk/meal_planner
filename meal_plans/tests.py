from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import timedelta
from .models import MealPlan, MealPlanDay, MealType, Meal
from recipes.models import Recipe
from .serializers import MealPlanSerializer
from .local_ai_service import LocalAIMealPlannerService

class MealPlanModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.meal_plan = MealPlan.objects.create(
            user=self.user,
            name='Test Plan',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=6),
            caloric_target=2000
        )
        self.meal_type = MealType.objects.create(name='Breakfast')
        self.day = MealPlanDay.objects.create(
            meal_plan=self.meal_plan,
            date=timezone.now().date()
        )

    def test_meal_plan_creation(self):
        self.assertEqual(self.meal_plan.name, 'Test Plan')
        self.assertEqual(self.meal_plan.caloric_target, 2000)
        self.assertEqual(self.meal_plan.user, self.user)

    def test_meal_plan_duration(self):
        duration = (self.meal_plan.end_date - self.meal_plan.start_date).days
        self.assertEqual(duration, 6)

class MealPlanAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create a recipe for meal plans
        self.recipe = Recipe.objects.create(
            title='Test Recipe',
            description='Test Description',
            ingredients=[{'name': 'ingredient1', 'amount': 100, 'unit': 'g'}],
            instructions=['Step 1'],
            calories_per_serving=300,
            protein=20,
            carbs=30,
            fat=10,
            created_by=self.user
        )
        
        # Create meal plan
        self.meal_plan = MealPlan.objects.create(
            user=self.user,
            name='Test Plan',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=6),
            caloric_target=2000
        )

    def test_create_weekly_plan(self):
        url = reverse('mealplan-create-weekly')
        data = {
            'name': 'New Weekly Plan',
            'caloric_target': 2000
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MealPlan.objects.count(), 2)
        new_plan = MealPlan.objects.latest('id')
        self.assertEqual(new_plan.name, 'New Weekly Plan')
        self.assertEqual(new_plan.days.count(), 7)

    def test_generate_ai_meal_plan(self):
        url = reverse('mealplan-generate-ai-meal-plan')
        data = {
            'dietary_preferences': ['balanced'],
            'target_calories': 2000,
            'meals_per_day': 3,
            'days': 7
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(MealPlan.objects.filter(name__contains='AI Generated Plan').exists())

    def test_nutritional_summary(self):
        # Create a day and meal for the test
        day = MealPlanDay.objects.create(
            meal_plan=self.meal_plan,
            date=timezone.now().date()
        )
        meal_type = MealType.objects.create(name='Breakfast')
        Meal.objects.create(
            day=day,
            meal_type=meal_type,
            recipe=self.recipe,
            servings=1
        )

        url = reverse('mealplan-nutritional-summary', kwargs={'pk': self.meal_plan.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_calories', response.data)
        self.assertIn('daily_averages', response.data)

class LocalAIServiceTests(TestCase):
    def setUp(self):
        self.ai_service = LocalAIMealPlannerService()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.preferences = {
            'dietary_preferences': ['balanced'],
            'target_calories': 2000,
            'meals_per_day': 3,
            'days': 7
        }

    def test_generate_meal_plan(self):
        meal_plan_data = self.ai_service.generate_meal_plan(self.preferences)
        
        self.assertIn('days', meal_plan_data)
        self.assertEqual(len(meal_plan_data['days']), 7)
        
        # Check first day's meals
        first_day = meal_plan_data['days'][0]
        self.assertIn('meals', first_day)
        self.assertEqual(len(first_day['meals']), 3)

    def test_adjust_recipe_portions(self):
        recipe = Recipe.objects.create(
            title='Test Recipe',
            calories_per_serving=500,
            protein=25,
            carbs=50,
            fat=20,
            created_by=self.user
        )
        
        adjusted = self.ai_service.adjust_recipe_portions(recipe, 750)
        
        self.assertEqual(adjusted['calories_per_serving'], 750)
        self.assertEqual(adjusted['protein'], 37)  # 25 * 1.5
        self.assertEqual(adjusted['carbs'], 75)    # 50 * 1.5
        self.assertEqual(adjusted['fat'], 30)      # 20 * 1.5
