from django.urls import path
from . import views

app_name = 'meal_plans'

urlpatterns = [
    path('', views.MealPlanList.as_view(), name='meal-plan-list'),
    path('<int:pk>/', views.MealPlanDetail.as_view(), name='meal-plan-detail'),
    path('generate/', views.GenerateMealPlan.as_view(), name='generate-meal-plan'),
    path('<int:plan_id>/meals/', views.PlanMealList.as_view(), name='plan-meal-list'),
    path('<int:plan_id>/meals/<int:pk>/', views.PlanMealDetail.as_view(), name='plan-meal-detail'),
]
