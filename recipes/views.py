from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg
from .models import Recipe, RecipeRating
from .serializers import RecipeSerializer, RecipeRatingSerializer

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Recipe.objects.all()
        
        # Filter by dietary tags
        dietary_tags = self.request.query_params.getlist('dietary_tags')
        if dietary_tags:
            queryset = queryset.filter(dietary_tags__contains=dietary_tags)
        
        # Filter by max calories
        max_calories = self.request.query_params.get('max_calories')
        if max_calories:
            queryset = queryset.filter(calories_per_serving__lte=max_calories)
        
        # Filter by preparation time
        max_prep_time = self.request.query_params.get('max_prep_time')
        if max_prep_time:
            queryset = queryset.filter(prep_time__lte=max_prep_time)
        
        return queryset

    @action(detail=True, methods=['POST'])
    def rate(self, request, pk=None):
        recipe = self.get_object()
        rating_value = request.data.get('rating')
        comment = request.data.get('comment', '')

        if not rating_value:
            return Response(
                {'error': 'Rating is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        rating, created = RecipeRating.objects.update_or_create(
            recipe=recipe,
            user=request.user,
            defaults={'rating': rating_value, 'comment': comment}
        )

        serializer = RecipeRatingSerializer(rating)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def top_rated(self, request):
        top_recipes = Recipe.objects.annotate(
            avg_rating=Avg('ratings__rating')
        ).filter(
            avg_rating__isnull=False
        ).order_by('-avg_rating')[:10]

        serializer = self.get_serializer(top_recipes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def my_recipes(self, request):
        recipes = Recipe.objects.filter(created_by=request.user)
        serializer = self.get_serializer(recipes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'])
    def adjust_servings(self, request, pk=None):
        recipe = self.get_object()
        desired_servings = request.data.get('servings')

        if not desired_servings:
            return Response(
                {'error': 'Number of servings is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate multiplier
        multiplier = desired_servings / recipe.servings

        # Adjust recipe quantities
        adjusted_recipe = {
            'title': recipe.title,
            'description': recipe.description,
            'ingredients': [
                {
                    **ingredient,
                    'amount': ingredient['amount'] * multiplier
                }
                for ingredient in recipe.ingredients
            ],
            'instructions': recipe.instructions,
            'servings': desired_servings,
            'calories_per_serving': recipe.calories_per_serving,
            'protein': recipe.protein,
            'carbs': recipe.carbs,
            'fat': recipe.fat
        }

        return Response(adjusted_recipe)
