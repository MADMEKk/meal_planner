from django.urls import path
from . import views

app_name = 'shopping'

urlpatterns = [
    path('lists/', views.ShoppingListList.as_view(), name='shopping-list-list'),
    path('lists/<int:pk>/', views.ShoppingListDetail.as_view(), name='shopping-list-detail'),
    path('lists/generate/<int:meal_plan_id>/', views.GenerateShoppingList.as_view(), name='generate-shopping-list'),
    path('items/', views.ShoppingItemList.as_view(), name='shopping-item-list'),
    path('items/<int:pk>/', views.ShoppingItemDetail.as_view(), name='shopping-item-detail'),
    path('categories/', views.ShoppingCategoryList.as_view(), name='shopping-category-list'),
]
