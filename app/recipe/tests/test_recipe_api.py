"""Test Recipe API Endpoints"""
from rest_framework.test import APIClient
from django.test import TestCase
from decimal import Decimal
from django.contrib.auth import get_user_model
from core.models import Recipe
from django.urls import reverse
from rest_framework import status
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer
)

RECIPE_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])


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


def create_user(**params):
    """Helper function for Create and return a new user"""
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """Tests for unauthenticated requests for recipe"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """test auth required to call API"""
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Tests for Authenticated requests for recipe"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
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

    def test_recipe_list_limited_to_user(self):
        """Test list of recipe is limited ti authenticated user"""
        other_user = create_user(
            email="otheruser@example.com",
            password="password123")

        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test retrieve a list of recipes"""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a recipe"""
        payload = {
            'title': "Sample recipe",
            'time_minutes': 30,
            'price': Decimal('5.40')

        }
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test patch request of the recipe API"""
        original_link = 'https://example.com/recipe.pdf'
        recipe = create_recipe(
            title='Sample Test recipe',
            user=self.user,
            link=original_link
        )
        payload = {'title': 'New recipe title'}
        res = self.client.patch(detail_url(recipe.id), payload)
        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test put request of the recipe API"""
        recipe = create_recipe(
            title='Sample Test recipe',
            user=self.user,
            link='https://example.com/recipe.pdf',
            description='some test desc'
        )
        payload = {
         'title': 'Mew sample recipe',
         'link': 'https://example.com/new-recipe.pdf',
         'description': 'some new test desc',
         'price': Decimal('2.43'),
         'time_minutes': 20
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        new_user = create_user(email='newUser@example.com', password='test123')
        recipe = create_recipe(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test for deleting a recipe"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_user_recipe_error(self):
        """Test for deleting another user recipe"""
        new_user = create_user(
            email='new-user@example.com',
            password='test123')
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())
