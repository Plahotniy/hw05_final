from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostsURLTest(TestCase):
    # создать тестовую группу и пост
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.not_author_user = User.objects.create_user(username='not_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый тест',
        )

    def setUp(self) -> None:
        # создаем авторизованного клиента и неавторизованного
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.authorized_not_author_client = Client()
        self.authorized_not_author_client.force_login(self.not_author_user)

    def test_general_urls(self):
        """Тестируем страницы доступные всем пользователям"""
        general_urls = (
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.author}/',
            f'/posts/{self.post.pk}/'
        )
        for address in general_urls:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_create_to_auth(self):
        """Тестируем редирект неавторизованного пользователя"""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_create(self):
        """Тестируем доступность страницы авторизованному пользователю"""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit(self):
        """Тестируем редактирование доступно только автору"""
        response = self.authorized_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_not_author(self):
        """Не автор не может редактировать пост и редиректится
        на страницу поста."""
        response = self.authorized_not_author_client.get(
            f'/posts/{self.post.pk}/edit/')
        self.assertRedirects(response, f'/posts/{self.post.pk}/')

    def test_guest_edit_post(self):
        """Не авторизованный пользователь не сможет
         редактировать пост и редиректится на страницу входа."""
        response = self.guest_client.get(
            f'/posts/{self.post.pk}/edit/'
        )
        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/{self.post.pk}/edit/')

    def test_404(self):
        """Тестируем несуществующую страницу."""
        response = self.authorized_client.get('/random_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_templates(self):
        """Тестируем соответствие шаблонов."""
        templates = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.author}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/random_page/': 'core/404.html'
        }
        for address, template in templates.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
