import os
import json
from typing import List, Dict, Any
import openai
from django.conf import settings
from recipes.models import Recipe
from meal_plans.models import MealPlan, MealPlanDay, MealType, Meal

class AIMealPlannerService:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.system_prompt = """You are a professional nutritionist and meal planner. Your task is to create 
        personalized meal plans based on user preferences, dietary restrictions, and nutritional goals. 
        Consider factors like calorie targets, macronutrient ratios, allergies, and food preferences."""

    def _generate_meal_plan_prompt(self, preferences: Dict[str, Any]) -> str:
        """Generate a detailed prompt for the AI based on user preferences"""
        prompt = f"""Create a meal plan with the following requirements:
        - Dietary preferences: {preferences.get('dietary_preferences', 'None')}
        - Allergies/restrictions: {preferences.get('restrictions', 'None')}
        - Target calories per day: {preferences.get('target_calories', 2000)}
        - Number of meals per day: {preferences.get('meals_per_day', 3)}
        - Days to plan: {preferences.get('days', 7)}
        
        For each meal, provide:
        1. Meal name
        2. Brief description
        3. Main ingredients
        4. Approximate calories
        5. Macronutrients (protein, carbs, fat)
        
        Format the response as a JSON object with the following structure:
        {
            "days": [
                {
                    "day": 1,
                    "meals": [
                        {
                            "meal_type": "breakfast/lunch/dinner",
                            "recipe": {
                                "title": "",
                                "description": "",
                                "ingredients": [
                                    {"name": "", "amount": 0, "unit": ""}
                                ],
                                "instructions": [],
                                "calories_per_serving": 0,
                                "protein": 0,
                                "carbs": 0,
                                "fat": 0
                            }
                        }
                    ]
                }
            ]
        }"""
        return prompt

    def generate_meal_plan(self, user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a meal plan using OpenAI's API"""
        try:
            prompt = self._generate_meal_plan_prompt(user_preferences)
            
            response = openai.ChatCompletion.create(
                model="gpt-4",  # or another appropriate model
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse the AI response
            meal_plan_data = json.loads(response.choices[0].message.content)
            return meal_plan_data
            
        except Exception as e:
            raise Exception(f"Failed to generate meal plan: {str(e)}")

    def create_meal_plan_from_ai_response(self, user, meal_plan_data: Dict[str, Any], preferences: Dict[str, Any]) -> MealPlan:
        """Create a MealPlan instance from AI-generated data"""
        try:
            # Create the meal plan
            meal_plan = MealPlan.objects.create(
                user=user,
                name=f"AI Generated Plan - {preferences.get('dietary_preferences', 'Custom')}",
                caloric_target=preferences.get('target_calories', 2000)
            )

            # Get or create meal types
            meal_types = {
                'breakfast': MealType.objects.get_or_create(name='Breakfast')[0],
                'lunch': MealType.objects.get_or_create(name='Lunch')[0],
                'dinner': MealType.objects.get_or_create(name='Dinner')[0]
            }

            # Create days and meals
            for day_data in meal_plan_data['days']:
                day = MealPlanDay.objects.create(
                    meal_plan=meal_plan,
                    date=meal_plan.start_date + timezone.timedelta(days=day_data['day'] - 1)
                )

                for meal_data in day_data['meals']:
                    # Create or get recipe
                    recipe_data = meal_data['recipe']
                    recipe = Recipe.objects.create(
                        title=recipe_data['title'],
                        description=recipe_data['description'],
                        ingredients=recipe_data['ingredients'],
                        instructions=recipe_data['instructions'],
                        calories_per_serving=recipe_data['calories_per_serving'],
                        protein=recipe_data['protein'],
                        carbs=recipe_data['carbs'],
                        fat=recipe_data['fat'],
                        created_by=user
                    )

                    # Create meal
                    Meal.objects.create(
                        day=day,
                        meal_type=meal_types[meal_data['meal_type'].lower()],
                        recipe=recipe,
                        servings=1  # Default to 1 serving, can be adjusted
                    )

            return meal_plan

        except Exception as e:
            # Clean up if something goes wrong
            if 'meal_plan' in locals():
                meal_plan.delete()
            raise Exception(f"Failed to create meal plan: {str(e)}")

    def suggest_recipe_alternatives(self, recipe: Recipe, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest alternative recipes based on user preferences"""
        try:
            prompt = f"""Suggest 3 alternative recipes for '{recipe.title}' that match these preferences:
            - Dietary preferences: {preferences.get('dietary_preferences', 'None')}
            - Allergies/restrictions: {preferences.get('restrictions', 'None')}
            - Target calories: {recipe.calories_per_serving} (±100 calories)
            
            Format each recipe as a JSON object with the same structure as the original recipe."""

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            alternatives = json.loads(response.choices[0].message.content)
            return alternatives

        except Exception as e:
            raise Exception(f"Failed to generate recipe alternatives: {str(e)}")

    def adjust_recipe_portions(self, recipe: Recipe, desired_calories: int) -> Dict[str, Any]:
        """Adjust recipe portions to match desired calories"""
        try:
            current_calories = recipe.calories_per_serving
            multiplier = desired_calories / current_calories

            adjusted_recipe = {
                'title': recipe.title,
                'description': recipe.description,
                'ingredients': [
                    {
                        'name': ingredient['name'],
                        'amount': ingredient['amount'] * multiplier,
                        'unit': ingredient['unit']
                    }
                    for ingredient in recipe.ingredients
                ],
                'instructions': recipe.instructions,
                'calories_per_serving': desired_calories,
                'protein': recipe.protein * multiplier,
                'carbs': recipe.carbs * multiplier,
                'fat': recipe.fat * multiplier
            }

            return adjusted_recipe

        except Exception as e:
            raise Exception(f"Failed to adjust recipe portions: {str(e)}")
