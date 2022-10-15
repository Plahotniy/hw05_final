import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import CommentForm, PostForm
from ..models import Comment, Group, Post

User = get_user_model()
# временная папка для хранения изображений
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
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
            text='Тестовый текст_1',
            group=cls.group,
            image=None
        )
        cls.form = PostForm()
        cls.comment = CommentForm()

    @classmethod
    def tearDownClass(cls):
        # После тестов временную папку удалим
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        # создаем авторизованного клиента и неавторизованного
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_non_author = Client()
        self.authorized_client.force_login(self.author)
        self.authorized_client_non_author = Client()
        self.authorized_client_non_author.force_login(self.not_author_user)

    def test_new_post(self):
        """При создании поста авторизованным юзером, пост добавляется в БД."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст 2',
            'author': self.author,
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertRedirects(
            response, reverse('posts:profile',
                              kwargs={'username': self.post.author})
        )

    def test_post_with_img(self):
        """Тестируем создание поста с картинкой."""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст 2',
            'author': self.author,
            'group': self.group.pk,
            'image': uploaded,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.post.refresh_from_db()
        post = Post.objects.latest('id')
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(str(post.image), 'posts/small.gif')

    def test_edit_post(self):
        """После редактирования поста автором, пост в БД изменяется"""
        form_data = {
            'text': 'Новый текст',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[self.post.pk]),
            data=form_data,
            follow=True
        )
        post = Post.objects.get(pk=self.post.pk)
        self.assertEqual(post.text, form_data['text'])
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={
                    'post_id': self.post.pk,
                }))

    def test_add_comment_authorized(self):
        """Тестируем, что комментарий добавляется."""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              args=[self.post.pk])
        )

    def test_add_comment_non_authorized(self):
        """Тестируем, что гость не может комментировать"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
            'author': self.author,
        }
        response = self.guest_client.post(
            reverse(
                'posts:add_comment',
                args=[self.post.pk]),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertRedirects(
            response, '/auth/login/?next=%2Fposts%2F1%2Fcomment%2F'
        )
