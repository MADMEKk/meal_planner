import json
from typing import List, Dict, Any
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from django.conf import settings
import os
from pathlib import Path
from recipes.models import Recipe
from meal_plans.models import MealPlan, MealPlanDay, MealType, Meal
from django.utils import timezone

class LocalAIMealPlannerService:
    def __init__(self):
        # Using FLAN-T5-small, a lightweight but capable model
        self.model_name = "google/flan-t5-small"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Initialize tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True
        ).to(self.device)

        # Load predefined meal templates
        self.meal_templates = self._load_meal_templates()

    def _load_meal_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load predefined meal templates from JSON file"""
        template_path = Path(__file__).parent / 'data' / 'meal_templates.json'
        if not template_path.exists():
            self._create_default_templates(template_path)
        
        with open(template_path, 'r') as f:
            return json.load(f)

    def _create_default_templates(self, template_path: Path):
        """Create default meal templates if none exist"""
        default_templates = {
            "vegetarian": [
                {
                    "meal_type": "breakfast",
                    "recipe": {
                        "title": "Overnight Oats with Berries",
                        "description": "Healthy and filling breakfast with oats and fresh berries",
                        "ingredients": [
                            {"name": "rolled oats", "amount": 50, "unit": "g"},
                            {"name": "almond milk", "amount": 120, "unit": "ml"},
                            {"name": "mixed berries", "amount": 100, "unit": "g"},
                            {"name": "honey", "amount": 15, "unit": "ml"}
                        ],
                        "instructions": [
                            "Mix oats and almond milk in a jar",
                            "Leave overnight in refrigerator",
                            "Top with berries and honey before serving"
                        ],
                        "calories_per_serving": 350,
                        "protein": 8,
                        "carbs": 65,
                        "fat": 7
                    }
                }
                # Add more templates...
            ],
            "keto": [
                # Add keto meal templates...
            ],
            "balanced": [
                # Add balanced meal templates...
            ]
        }
        
        template_path.parent.mkdir(exist_ok=True)
        with open(template_path, 'w') as f:
            json.dump(default_templates, f, indent=4)

    def _adapt_template_to_preferences(self, template: Dict[str, Any], preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt a meal template to match user preferences"""
        adapted = template.copy()
        recipe = adapted['recipe']

        # Adjust calories
        target_calories = preferences.get('target_calories', 2000)
        current_calories = recipe['calories_per_serving']
        multiplier = target_calories / (current_calories * 3)  # Assuming 3 meals per day

        # Adjust quantities and nutrients
        for ingredient in recipe['ingredients']:
            ingredient['amount'] *= multiplier
        
        recipe['calories_per_serving'] = int(current_calories * multiplier)
        recipe['protein'] = int(recipe['protein'] * multiplier)
        recipe['carbs'] = int(recipe['carbs'] * multiplier)
        recipe['fat'] = int(recipe['fat'] * multiplier)

        return adapted

    def _select_meal_template(self, meal_type: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Select an appropriate meal template based on preferences"""
        diet_type = preferences.get('dietary_preferences', ['balanced'])[0]
        templates = self.meal_templates.get(diet_type, self.meal_templates['balanced'])
        
        # Filter templates by meal type
        suitable_templates = [t for t in templates if t['meal_type'] == meal_type]
        if not suitable_templates:
            suitable_templates = templates  # Fallback to any template if no specific meal type found
        
        # Select a template (could be randomized or based on more criteria)
        template = suitable_templates[0]
        return self._adapt_template_to_preferences(template, preferences)

    def generate_meal_plan(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a meal plan based on user preferences"""
        try:
            days = preferences.get('days', 7)
            meals_per_day = preferences.get('meals_per_day', 3)
            meal_types = ['breakfast', 'lunch', 'dinner'][:meals_per_day]

            meal_plan_data = {
                "days": []
            }

            for day in range(days):
                day_meals = []
                for meal_type in meal_types:
                    meal = self._select_meal_template(meal_type, preferences)
                    day_meals.append(meal)

                meal_plan_data["days"].append({
                    "day": day + 1,
                    "meals": day_meals
                })

            return meal_plan_data

        except Exception as e:
            raise Exception(f"Failed to generate meal plan: {str(e)}")

    def create_meal_plan_from_ai_response(self, user, meal_plan_data: Dict[str, Any], preferences: Dict[str, Any]) -> MealPlan:
        """Create a MealPlan instance from generated data"""
        try:
            # Create the meal plan
            meal_plan = MealPlan.objects.create(
                user=user,
                name=f"AI Generated Plan - {preferences.get('dietary_preferences', ['Custom'])[0]}",
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

                    Meal.objects.create(
                        day=day,
                        meal_type=meal_types[meal_data['meal_type']],
                        recipe=recipe,
                        servings=1
                    )

            return meal_plan

        except Exception as e:
            if 'meal_plan' in locals():
                meal_plan.delete()
            raise Exception(f"Failed to create meal plan: {str(e)}")

    def suggest_recipe_alternatives(self, recipe: Recipe, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest alternative recipes based on user preferences"""
        try:
            diet_type = preferences.get('dietary_preferences', ['balanced'])[0]
            templates = self.meal_templates.get(diet_type, self.meal_templates['balanced'])
            
            # Find similar recipes based on calories and macros
            alternatives = []
            for template in templates:
                recipe_data = template['recipe']
                if abs(recipe_data['calories_per_serving'] - recipe.calories_per_serving) <= 100:
                    alternatives.append(recipe_data)
                if len(alternatives) >= 3:
                    break

            return alternatives[:3]

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
                'protein': int(recipe.protein * multiplier),
                'carbs': int(recipe.carbs * multiplier),
                'fat': int(recipe.fat * multiplier)
            }

            return adjusted_recipe

        except Exception as e:
            raise Exception(f"Failed to adjust recipe portions: {str(e)}")
