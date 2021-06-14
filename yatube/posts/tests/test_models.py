from django.test import TestCase

from ..models import Group, Post, User


class PostsModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Название',
            slug='Ссылка',
            description='Описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=User.objects.create(username='Anon'),
        )

    def test_verbose_name(self):
        '''verbose_name выводит нужное значение'''
        post = PostsModelTest.post
        field_verboses = {
            'text': 'Текст публикации',
            'group': 'Сообщество',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected
                )

    def test_help_text(self):
        '''help_text содержит нужное значение'''
        post = PostsModelTest.post
        field_help_texts = {
            'group': 'Выберите сообщество',
            'text': 'Введите текст публикации'
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected
                )

    def test_str_method(self):
        '''Метод __str__ выводит нужное значение'''
        tests_items = {
            str(self.post): self.post.text[:15],
            str(self.group): self.group.title
        }
        for value, expected in tests_items.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)
