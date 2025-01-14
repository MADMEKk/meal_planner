from django.db import models
from django.contrib.auth.models import User
from recipes.models import Recipe

# Create your models here.

class MealPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_template = models.BooleanField(default=False)
    caloric_target = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"

    class Meta:
        ordering = ['-start_date']

class MealPlanDay(models.Model):
    meal_plan = models.ForeignKey(MealPlan, on_delete=models.CASCADE, related_name='days')
    date = models.DateField()
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Day {self.date} of {self.meal_plan.name}"

    class Meta:
        ordering = ['date']
        unique_together = ['meal_plan', 'date']

class MealType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['display_order']

class Meal(models.Model):
    day = models.ForeignKey(MealPlanDay, on_delete=models.CASCADE, related_name='meals')
    meal_type = models.ForeignKey(MealType, on_delete=models.PROTECT)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    servings = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.meal_type.name} - {self.recipe.title}"

    class Meta:
        ordering = ['meal_type__display_order']
        unique_together = ['day', 'meal_type']

    def get_calories(self):
        return self.recipe.calories_per_serving * self.servings

    def get_nutrients(self):
        return {
            'protein': self.recipe.protein * self.servings,
            'carbs': self.recipe.carbs * self.servings,
            'fat': self.recipe.fat * self.servings
        }
