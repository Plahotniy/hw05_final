from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase

from ..models import Comment, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый тест',
        )
        cls.comment = Comment.objects.create(
            author=cls.author,
            text='Тестовый комментарий',
            post_id=cls.post.pk
        )

    def setUp(self) -> None:
        cache.clear()

    def test_models_have_correct_objects_name(self):
        """Проверяем что у моделей корректно работает __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        comment = PostModelTest.comment
        expected_names = {
            post: post.text[:15],
            group: group.title,
            comment: comment.text,
        }
        for model, name in expected_names.items():
            with self.subTest(model=model):
                self.assertEqual(str(model), name)
