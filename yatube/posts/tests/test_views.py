from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()
POST_TEST_OFFSET = settings.POST_PER_PAGE + 1


class PostsViewsTest(TestCase):
    # создать тестовую группу, группу без постов и пост
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание', )
        cls.empty_group = Group.objects.create(
            title='Пустая группа',
            slug='empty-slug',
            description='Пустое описание', )
        cls.post = Post.objects.create(
            author=cls.author,
            text='test',
            group=cls.group
        )

    def setUp(self) -> None:
        # создаем авторизованного клиента и неавторизованного
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post.author)
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)
        cache.clear()

    # def tearDown(self) -> None:
    #     # cache.clear()

    def test_cache_index(self):
        """Тестируем работу кеша на главное странице"""
        add = self.authorized_client.get(reverse('posts:index')).content
        self.post.delete()
        delete = self.authorized_client.get(reverse('posts:index')).content
        self.assertEqual(add,
                         delete)
        self.assertIn(self.post.text, str(delete))
        cache.clear()
        clr = self.authorized_client.get(reverse('posts:index')).content
        self.assertNotEqual(clr, delete)

    def test_pages_uses_correct_template(self):
        """Открываются правильные шаблоны"""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse('posts:group_list',
                                             kwargs={'slug': self.group.slug}),
            'posts/profile.html': reverse('posts:profile',
                                          kwargs={'username': self.author}),
            'posts/post_detail.html': reverse('posts:post_detail',
                                              kwargs={
                                                  'post_id': self.post.pk}), }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_create_page_edit_page(self):
        """Страница create и edit открывается с правильным шаблоном"""
        templates_pages_names = {
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.pk}): 'posts/create_post.html', }
        for reverse_name, templates in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, templates)

    def test_home_page_show_correct_context(self):
        """В index передан корректный context"""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        # self.assertEqual(first_object.image, self.post.image)

    def test_group_page_show_correct_context(self):
        """В group_list передан корректный context"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.post.group)
        # self.assertEqual(first_object.image, self.post.image)

    def test_profile_page_show_correct_context(self):
        """В profile передан корректный context"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={
                'username': self.post.author
            })
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.post.author)
        # self.assertEqual(first_object.image, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        """В post_detail передан корректный context"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={
                'post_id': self.post.pk
            })
        )
        first_object = response.context['post']
        self.assertEqual(first_object.text, self.post.text)
        # self.assertEqual(first_object.image, self.post.image)

    def test_post_create_page_show_correct_context(self):
        """В create передан корректный context"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.CharField,
            'group': forms.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """В post_edit передан корректный context"""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.pk
            }))
        form_fields = {
            'text': forms.CharField,
            'group': forms.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_new_post_on_main_group_profile(self):
        """Новые посты отображаются в index, profile, group_list"""
        urls = (
            reverse('posts:index'),
            reverse('posts:profile', kwargs={
                'username': self.post.author
            }),
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug
            })
        )
        for url in urls:
            response = self.authorized_client.get(url)
            self.assertEqual(len(response.context['page_obj'].object_list), 1)

    def test_empty_group(self):
        """Пост не попал в группу которую ему не указывали"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={
                'slug': self.empty_group.slug
            }))
        self.assertEqual(len(response.context['page_obj'].object_list), 0)


class FollowIndex(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.user_1 = User.objects.create_user(username='user_1')
        cls.user_2 = User.objects.create_user(username='user_2')
        cls.post = Post.objects.create(
            text='test',
            author=cls.author,
        )

    def setUp(self) -> None:
        self.authorized_author = Client()
        self.authorized_user_1 = Client()
        self.authorized_user_2 = Client()
        self.authorized_author.force_login(self.author)
        self.authorized_user_1.force_login(self.user_1)
        self.authorized_user_2.force_login(self.user_2)
        cache.clear()

    def test_follow_index(self):
        """Новый пост появляется только у подписчиков.
        У не подписанных не появляется.
        """
        Post.objects.create(
            text='User 1 text',
            author=self.user_1,
        )
        Post.objects.create(
            text='author text',
            author=self.author,
        )
        self.authorized_user_1.get(reverse('posts:profile_follow',
                                           kwargs={
                                               'username': self.author
                                           }))
        res_1 = self.authorized_user_1.get(reverse('posts:follow_index'))
        first_object = res_1.context['page_obj'][1]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.image, self.post.image)
        self.authorized_user_2.get(reverse('posts:profile_follow',
                                           kwargs={
                                               'username': self.user_1
                                           }))
        res_2 = self.authorized_user_2.get(reverse('posts:follow_index'))
        first_object_res_2 = res_2.context['page_obj'][0]
        print(first_object_res_2.text)
        self.assertNotEqual(first_object_res_2.text, self.post.text)

    def test_user_can_follow_and_unfollow(self):
        """Пользователь может подписаться и отписаться от автора"""
        self.authorized_user_1.get(reverse('posts:profile_follow',
                                           kwargs={
                                               'username': self.author
                                           }))
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_1,
                author=self.author,
            ).exists()
        )
        follow_count = Follow.objects.count()
        Follow.objects.filter(user=self.user_1, author=self.author).delete()
        self.assertEqual(follow_count - 1, Follow.objects.count())


class PaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        # создаем тестового пользователя, группу и посты
        super().setUpClass()
        # cache.clear()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = []
        for i in range(POST_TEST_OFFSET):
            cls.post.append(Post.objects.create(
                text=f'Тестовый пост {i}',
                author=cls.author,
                group=cls.group,
            )
            )

    def setUp(self) -> None:
        # создаем неавторизованного клиента
        self.guest_client = Client()
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """На первой странице 10 постов"""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']),
                         settings.POST_PER_PAGE)

    def test_second_page_contains_other_records(self):
        """На второй странице оставшиеся посты"""
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        count_posts = len(response.context['page_obj'])
        self.assertEqual(
            count_posts, POST_TEST_OFFSET - settings.POST_PER_PAGE)
