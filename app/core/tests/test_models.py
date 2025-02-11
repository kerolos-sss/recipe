"""
Tests for models.
"""

from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model


from core import models

user_details = {
    "email": "test@example.com",
    "password": "testpass",
    "name": "Test Name",
}


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test creating a new user with an email is successful."""
        email = "test@example.com"
        password = "TestPass123"
        user = get_user_model().objects.create_user(email=email, password=password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email for a new user is normalized."""
        sample_email_pairs = [
            ("test1@EXAMPLE.com", "test1@example.com"),
            ("Test2@Example.COM", "Test2@example.com"),
            ("TEST3@EXAMPLE.COM", "TEST3@example.com"),
            ("test4@Example.com", "test4@example.com"),
        ]
        for email, expected in sample_email_pairs:
            user = get_user_model().objects.create_user(email, "test123")
            self.assertEqual(user.email, expected)

    def test_new_user_without_raises_error(self):
        """Test creating user without email raises error."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, "test123")

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "test123")

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(" ", "test123")

    def test_create_new_superuser(self):
        """Test creating a new superuser."""
        user = get_user_model().objects.create_superuser("test@example.com", "test123")

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_active)

    def test_create_recipe(self):
        """Test creating a new recipe."""
        user = get_user_model().objects.create_user(
            email=user_details["email"],
            password=user_details["password"],
            name=user_details["name"],
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title="Sample Recipe Title",
            time_minutes=5,
            price=Decimal(5.00),
            description="Sample Recipe Description",
        )

        self.assertEqual(recipe.title, "Sample Recipe Title")
