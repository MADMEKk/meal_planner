from django.urls import path
from . import views

app_name = 'recipes'

urlpatterns = [
    path('', views.RecipeList.as_view(), name='recipe-list'),
    path('<int:pk>/', views.RecipeDetail.as_view(), name='recipe-detail'),
    path('categories/', views.CategoryList.as_view(), name='category-list'),
    path('categories/<int:pk>/', views.CategoryDetail.as_view(), name='category-detail'),
    path('ingredients/', views.IngredientList.as_view(), name='ingredient-list'),
    path('ingredients/<int:pk>/', views.IngredientDetail.as_view(), name='ingredient-detail'),
    path('search/', views.RecipeSearch.as_view(), name='recipe-search'),
]
