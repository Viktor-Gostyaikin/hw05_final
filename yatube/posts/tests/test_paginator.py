from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PaginatorViewsTest(TestCase):
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.anyone = User.objects.create(username='anyone')
        cls.group_ex = Group.objects.create(
            title="Тестовая группа",
            slug="test_slug",
            description="Описание",
        )
        cls.post_ex = Post.objects.create(
            text='Тестовый текст',
            author=cls.anyone,
            group=cls.group_ex
        )

    def setUp(self):
        self.guest_client = Client()

    def test_page_contains_ten_records(self):
        # Проверка: количество постов не привышает
        post_per_page = 10
        c_test_pages = 3
        value_dic = {
            'profile': {'username': self.anyone.username},
            'index': None}

        obj = [
            Post(
                text=f'Test {num}',
                author=self.anyone,
                group=self.group_ex
            )
            for num in range(
                post_per_page + c_test_pages
            )
        ]

        self.post_gen = Post.objects.bulk_create(obj)

        for page in range(c_test_pages):
            for value, kwarg in value_dic.items():
                with self.subTest(page=page, value=value):
                    response = self.guest_client.get(
                        reverse(value, kwargs=kwarg), {'page': page})
                    self.assertEqual(
                        response.context.get('page').paginator.per_page,
                        post_per_page)
