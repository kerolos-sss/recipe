"""
Test the recipe API.
"""

from decimal import Decimal

from django.test import TestCase

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse("recipe:recipe-list")


user_details = {
    "email": "test@example.com",
    "password": "testpass",
    "name": "Test Name",
}

user_details2 = {
    "email": "other@example.com",
    "password": "testpass",
    "name": "Other Name",
}


def create_user(**params):
    """Helper function to create a user."""
    return get_user_model().objects.create_user(**params)


def detail_url(recipe_id):
    """Return recipe detail URL."""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def create_recipe(user, **params):
    """Helper function to create a recipe."""
    defaults = {
        "title": "Sample Recipe",
        "time_minutes": 10,
        "price": Decimal("5.00"),
        "description": "Sample Recipe Description",
        "link": "https://www.sample.com",
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """Test the recipe API (public)."""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to access the endpoint."""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test the recipe API (private)."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email=user_details["email"],
            password=user_details["password"],
            name=user_details["name"],
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test retrieving recipes for user."""
        user2 = get_user_model().objects.create_user(
            email="other@example.com",
            password="testpass",
            name="Other Name",
        )
        create_recipe(user=user2)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test viewing a recipe detail."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating recipe."""
        payload = {
            "title": "Chocolate Cheesecake",
            "time_minutes": 30,
            "price": Decimal("5.00"),
            # "link": "https://www.sample.com",
            # "description": "Sample Recipe Description",
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data["id"])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_partial_update_recipe(self):
        """Test updating a recipe with patch."""

        original_link = "https://www.sample.com"

        recipe = create_recipe(
            user=self.user,
            link=original_link,
            description="Sample Recipe Description",
            title="Sample Recipe",
            time_minutes=10,
            price=Decimal("5.00"),
        )

        payload = {"title": "Chicken Tikka"}

        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.link, original_link)

    def test_full_update_recipe(self):
        """Test updating a recipe with put."""
        recipe = create_recipe(
            user=self.user,
            title="Sample Recipe",
            time_minutes=10,
            price=Decimal("5.00"),
            description="Sample Recipe Description",
        )

        payload = {
            "title": "Spaghetti Carbonara",
            "time_minutes": 25,
            "price": Decimal("7.00"),
            "link": "https://www.sample.com",
            "description": "",
        }

        url = detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()

        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_update_user_returns_error(self):
        """Test that a user cannot update another user's recipe."""
        user2 = get_user_model().objects.create_user(
            email="other@example.com",
            password="testpass",
            name="Other Name",
        )

        recipe = create_recipe(user=self.user)

        payload = {
            "user": user2.id,
        }

        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_recipe(self):
        """Test deleting a recipe."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_reciepe_other_user_recipe_error(self):
        """Test that a user cannot delete another user's recipe."""
        user2 = get_user_model().objects.create_user(
            email=user_details2["email"],
            password=user_details2["password"],
            name=user_details2["name"],
        )
        recipe = create_recipe(user=user2)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_reciepe_with_tags(self):
        """Test creating a recipe with new tags."""

        payload = {
            "title": "Avocado Lime Cheesecake",
            "time_minutes": 60,
            "price": Decimal("20.00"),
            "tags": [{"name": "Vegan"}, {"name": "Dessert"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)

        for tag in payload["tags"]:

            self.assertIn(
                Tag.objects.get(name=tag["name"], user=self.user), recipe.tags.all()
            )

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tags."""

        tag1_name = "Vegan"
        tag2 = Tag.objects.create(user=self.user, name="Dessert")

        payload = {
            "title": "Avocado Lime Cheesecake",
            "time_minutes": 60,
            "price": Decimal("20.00"),
            "tags": [{"name": tag1_name}, {"name": tag2.name}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)

        self.assertIn(tag2, recipe.tags.all())

        for tag in payload["tags"]:
            exists = Tag.objects.filter(name=tag["name"], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating a tag on update."""
        recipe = create_recipe(user=self.user)

        payload = {
            "tags": [{"name": "Vegan"}, {"name": "Dessert"}],
        }

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(name="Vegan", user=self.user)
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tags(self):
        """Test assigning an existing tag when updating a reciepe."""
        tag_breakfast = Tag.objects.create(user=self.user, name="Breakfast")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name="Lunch")
        payload = {
            "tags": [
                {"name": tag_lunch.name},
            ],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe = Recipe.objects.get(id=recipe.id)

        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing all tags on a recipe."""
        tag_breakfast = Tag.objects.create(user=self.user, name="Breakfast")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        payload = {
            "tags": [],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
        self.assertFalse(recipe.tags.exists())
