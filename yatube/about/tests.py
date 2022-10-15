from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class AboutURLTest(TestCase):
    def setUp(self) -> None:
        self.guest_client = Client()

    def test_about(self):
        response = self.guest_client.get(reverse('about:author'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'about/author.html')

    def test_tech(self):
        response = self.guest_client.get(reverse('about:tech'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'about/tech.html')
