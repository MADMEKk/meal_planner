from django.db import models
from django.contrib.auth.models import User

class Recipe(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    ingredients = models.JSONField()  # List of ingredients with quantities and categories
    instructions = models.TextField()
    prep_time = models.PositiveIntegerField(help_text="Preparation time in minutes")
    cook_time = models.PositiveIntegerField(help_text="Cooking time in minutes")
    servings = models.PositiveIntegerField()
    calories_per_serving = models.PositiveIntegerField()
    protein = models.FloatField()
    carbs = models.FloatField()
    fat = models.FloatField()
    dietary_tags = models.JSONField(default=list)  # ['vegan', 'keto', etc.]
    image = models.ImageField(upload_to='recipe_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_public = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

class RecipeRating(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['recipe', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s rating for {self.recipe.title}"
