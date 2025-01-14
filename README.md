# AI Meal Planner

An intelligent meal planning application that helps users create personalized meal plans, manage recipes, and generate shopping lists.

## Features

- Recipe management with nutritional information
- AI-powered meal plan generation
- Shopping list creation and management
- Pantry tracking system
- Support for different dietary preferences
- Nutritional tracking and analysis

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd ai_meal_planner
```

2. Run the setup script:
```bash
python setup.py
```
This will:
- Create and activate a virtual environment
- Install required packages
- Set up the database
- Create an admin user

3. Run the application:
```bash
python run.py
```
This will:
- Start the development server
- Open the admin interface in your browser
- Display available API endpoints

## Default Admin Credentials

- Username: admin
- Password: admin123

## API Endpoints

### Recipes
- GET /api/recipes/ - List all recipes
- POST /api/recipes/ - Create a new recipe
- GET /api/recipes/{id}/ - Get recipe details
- POST /api/recipes/{id}/rate/ - Rate a recipe

### Meal Plans
- GET /api/meal-plans/ - List all meal plans
- POST /api/meal-plans/generate-ai-meal-plan/ - Generate an AI meal plan
- GET /api/meal-plans/{id}/nutritional-summary/ - Get nutritional summary
- POST /api/meal-plans/{id}/suggest-alternatives/ - Get meal alternatives

### Shopping
- GET /api/shopping/lists/ - List shopping lists
- POST /api/shopping/lists/{id}/generate-from-meal-plan/ - Generate shopping list
- GET /api/shopping/pantry/ - List pantry items
- GET /api/shopping/pantry/expiring-soon/ - Get soon-to-expire items

## Testing

Run the test suite:
```bash
python run_tests.py
```

## Development

1. Make your changes
2. Run tests to ensure nothing is broken
3. Update documentation if needed

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
