from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from recipes.models import Recipe

from .models import MealPlan, MealPlanDay, MealType, Meal
from .serializers import (
    MealPlanSerializer, MealPlanDaySerializer,
    MealTypeSerializer, MealSerializer
)
from .local_ai_service import LocalAIMealPlannerService

class MealTypeViewSet(viewsets.ModelViewSet):
    queryset = MealType.objects.all()
    serializer_class = MealTypeSerializer
    permission_classes = [IsAuthenticated]

class MealPlanViewSet(viewsets.ModelViewSet):
    serializer_class = MealPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MealPlan.objects.filter(user=self.request.user)

    @action(detail=False, methods=['POST'])
    def create_weekly(self, request):
        """Create a meal plan for the next week"""
        start_date = request.data.get('start_date') or timezone.now().date()
        name = request.data.get('name') or f'Weekly Plan - {start_date}'
        
        # Create meal plan
        meal_plan = MealPlan.objects.create(
            user=request.user,
            name=name,
            start_date=start_date,
            end_date=start_date + timedelta(days=6),
            caloric_target=request.data.get('caloric_target')
        )

        # Create days
        for i in range(7):
            day_date = start_date + timedelta(days=i)
            MealPlanDay.objects.create(
                meal_plan=meal_plan,
                date=day_date
            )

        serializer = self.get_serializer(meal_plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['POST'])
    def generate_ai_meal_plan(self, request):
        """Generate a meal plan using local AI based on user preferences"""
        try:
            # Validate user preferences
            preferences = {
                'dietary_preferences': request.data.get('dietary_preferences', ['balanced']),
                'restrictions': request.data.get('restrictions', []),
                'target_calories': request.data.get('target_calories', 2000),
                'meals_per_day': request.data.get('meals_per_day', 3),
                'days': request.data.get('days', 7)
            }

            # Initialize local AI service
            ai_service = LocalAIMealPlannerService()

            # Generate meal plan data
            meal_plan_data = ai_service.generate_meal_plan(preferences)

            # Create meal plan in database
            meal_plan = ai_service.create_meal_plan_from_ai_response(
                user=request.user,
                meal_plan_data=meal_plan_data,
                preferences=preferences
            )

            serializer = self.get_serializer(meal_plan)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['POST'])
    def suggest_alternatives(self, request, pk=None):
        """Suggest alternative recipes for a meal in the plan"""
        try:
            meal_id = request.data.get('meal_id')
            if not meal_id:
                return Response(
                    {'error': 'meal_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            meal = Meal.objects.get(
                id=meal_id,
                day__meal_plan_id=pk,
                day__meal_plan__user=request.user
            )

            preferences = {
                'dietary_preferences': request.data.get('dietary_preferences', []),
                'restrictions': request.data.get('restrictions', [])
            }

            ai_service = LocalAIMealPlannerService()
            alternatives = ai_service.suggest_recipe_alternatives(
                meal.recipe,
                preferences
            )

            return Response(alternatives)

        except Meal.DoesNotExist:
            return Response(
                {'error': 'Meal not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['POST'])
    def adjust_portions(self, request, pk=None):
        """Adjust recipe portions to match desired calories"""
        try:
            meal_id = request.data.get('meal_id')
            desired_calories = request.data.get('desired_calories')

            if not meal_id or not desired_calories:
                return Response(
                    {'error': 'meal_id and desired_calories are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            meal = Meal.objects.get(
                id=meal_id,
                day__meal_plan_id=pk,
                day__meal_plan__user=request.user
            )

            ai_service = LocalAIMealPlannerService()
            adjusted_recipe = ai_service.adjust_recipe_portions(
                meal.recipe,
                desired_calories
            )

            return Response(adjusted_recipe)

        except Meal.DoesNotExist:
            return Response(
                {'error': 'Meal not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['GET'])
    def nutritional_summary(self, request, pk=None):
        """Get nutritional summary for the meal plan"""
        meal_plan = self.get_object()
        summary = {
            'total_calories': 0,
            'total_protein': 0,
            'total_carbs': 0,
            'total_fat': 0,
            'daily_averages': {},
            'meals_per_day': {}
        }

        for day in meal_plan.days.all():
            day_calories = 0
            day_protein = 0
            day_carbs = 0
            day_fat = 0
            day_meals = 0

            for meal in day.meals.all():
                calories = meal.get_calories()
                nutrients = meal.get_nutrients()
                
                day_calories += calories
                day_protein += nutrients['protein']
                day_carbs += nutrients['carbs']
                day_fat += nutrients['fat']
                day_meals += 1

            date_str = day.date.strftime('%Y-%m-%d')
            summary['daily_averages'][date_str] = {
                'calories': day_calories,
                'protein': day_protein,
                'carbs': day_carbs,
                'fat': day_fat
            }
            summary['meals_per_day'][date_str] = day_meals

            summary['total_calories'] += day_calories
            summary['total_protein'] += day_protein
            summary['total_carbs'] += day_carbs
            summary['total_fat'] += day_fat

        days_count = meal_plan.days.count()
        if days_count > 0:
            summary['average_daily_calories'] = summary['total_calories'] / days_count
            summary['average_daily_protein'] = summary['total_protein'] / days_count
            summary['average_daily_carbs'] = summary['total_carbs'] / days_count
            summary['average_daily_fat'] = summary['total_fat'] / days_count

        return Response(summary)

class MealPlanDayViewSet(viewsets.ModelViewSet):
    serializer_class = MealPlanDaySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MealPlanDay.objects.filter(meal_plan__user=self.request.user)

class MealViewSet(viewsets.ModelViewSet):
    serializer_class = MealSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Meal.objects.filter(day__meal_plan__user=self.request.user)

    def perform_create(self, serializer):
        # Ensure the meal plan belongs to the user
        day = serializer.validated_data['day']
        if day.meal_plan.user != self.request.user:
            raise PermissionError("You don't have permission to add meals to this plan")
        serializer.save()
