from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Recipe, RecipeRating

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')

class RecipeRatingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = RecipeRating
        fields = '__all__'
        read_only_fields = ('user',)

class RecipeSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    ratings = RecipeRatingSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ('created_by',)

    def get_average_rating(self, obj):
        ratings = obj.ratings.all()
        if not ratings:
            return None
        return sum(r.rating for r in ratings) / len(ratings)

    def create(self, validated_data):
        user = self.context['request'].user
        recipe = Recipe.objects.create(created_by=user, **validated_data)
        return recipe
