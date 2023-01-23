"""Test Recipe API Endpoints"""
from rest_framework.test import APIClient
from django.test import TestCase
from decimal import Decimal
from django.contrib.auth import get_user_model
from core.models import Recipe
from django.urls import reverse
from rest_framework import status
from recipe.serializers import RecipeSerializer


RECIPE_URL = reverse('recipe:recipe-list')


def create_recipe(user, **params):
    """Helper function for Create and return a sample Recipe"""

    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 13,
        'price': Decimal('15.3'),
        'description': "Sample desc",
        'link': 'https://example.com/recipe.pdf'
    }

    defaults.update(params)
    recipe = Recipe.objects.create(
        user=user, **defaults
    )

    return recipe

class PublicRecipeAPITests(TestCase):
    """Tests for unauthenticated requests for recipe"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """test auth required to call API"""
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateRecipeAPITests(TestCase):
    """Tests for Authenticated requests for recipe""""

    def setUp(self):
        self.client = APIClient
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test Name'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieve a list of recipes"""

        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


