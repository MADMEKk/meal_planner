from rest_framework import serializers
from .models import MealPlan, MealPlanDay, MealType, Meal
from recipes.serializers import RecipeSerializer
from recipes.models import Recipe

class MealTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealType
        fields = '__all__'

class MealSerializer(serializers.ModelSerializer):
    recipe = RecipeSerializer(read_only=True)
    recipe_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        source='recipe',
        queryset=Recipe.objects.all()
    )
    meal_type = MealTypeSerializer(read_only=True)
    meal_type_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        source='meal_type',
        queryset=MealType.objects.all()
    )
    calories = serializers.SerializerMethodField()
    nutrients = serializers.SerializerMethodField()

    class Meta:
        model = Meal
        fields = '__all__'

    def get_calories(self, obj):
        return obj.get_calories()

    def get_nutrients(self, obj):
        return obj.get_nutrients()

class MealPlanDaySerializer(serializers.ModelSerializer):
    meals = MealSerializer(many=True, read_only=True)
    total_calories = serializers.SerializerMethodField()

    class Meta:
        model = MealPlanDay
        fields = '__all__'

    def get_total_calories(self, obj):
        return sum(meal.get_calories() for meal in obj.meals.all())

class MealPlanSerializer(serializers.ModelSerializer):
    days = MealPlanDaySerializer(many=True, read_only=True)
    total_days = serializers.SerializerMethodField()

    class Meta:
        model = MealPlan
        fields = '__all__'
        read_only_fields = ('user',)

    def get_total_days(self, obj):
        return obj.days.count()

    def create(self, validated_data):
        user = self.context['request'].user
        meal_plan = MealPlan.objects.create(user=user, **validated_data)
        return meal_plan
