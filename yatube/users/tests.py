from http import HTTPStatus

from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UsersURLTest(TestCase):
    def setUp(self) -> None:
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_signup(self):
        response = self.guest_client.get(reverse('users:signup'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_login(self):
        response = self.authorized_client.get(reverse('users:login'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_logout(self):
        response = self.authorized_client.get(reverse('users:logout'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_password_change(self):
        response = self.authorized_client.get(reverse('users:password_change'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_password_change_done(self):
        response = self.authorized_client.get(
            reverse('users:password_change_done')
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_password_reset(self):
        response = self.authorized_client.get(reverse('users:password_reset'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_password_reset_done(self):
        response = self.authorized_client.get(
            reverse('users:password_reset_done')
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_reset_done(self):
        response = self.authorized_client.get(
            reverse('users:password_reset_complete')
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_signup_page_show_correct_context(self):
        """В signup передан корректный context"""
        response = self.authorized_client.get(reverse('users:signup'))
        form_fields = {
            'first_name': forms.CharField,
            'last_name': forms.CharField,
            'username': forms.CharField,
            'email': forms.EmailField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
