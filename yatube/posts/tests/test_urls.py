from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls.base import reverse

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        '''Создание тестовых пользователей, группы, постов.'''
        super().setUpClass()
        cls.anyone = User.objects.create(username='anyone')
        cls.anytwo = User.objects.create(username='anytwo')
        cls.group_ex = Group.objects.create(
            title="Тестовая группа",
            slug="test_slug",
            description="Описание",
        )
        cls.post_ex = Post.objects.create(
            text='Тестовый текст 1',
            author=cls.anyone,
            group=cls.group_ex
        )
        cls.post_ex2 = Post.objects.create(
            text='Тестовый текст 2',
            author=cls.anytwo,
            group=cls.group_ex
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.anyone)
        cache.clear()

    def test_guest_access(self):
        '''Проверка доступности страниц сайта для гостя'''
        dir = {
            '/': HTTPStatus.OK,
            f'/group/{self.group_ex.slug}/': HTTPStatus.OK,
            '/new/': HTTPStatus.FOUND,
            f'/{self.anyone.username}/': HTTPStatus.OK,
            f'/{self.anyone.username}/{self.post_ex.id}/': HTTPStatus.OK,
            f'/{self.anyone.username}/{self.post_ex.id}/edit/':
                HTTPStatus.FOUND,
            'test_page_12345': HTTPStatus.NOT_FOUND
        }
        for value, response in dir.items():
            with self.subTest(value=value, status_code=response):
                request = self.guest_client.get(value)
                self.assertEqual(request.status_code, response)

    def test_authorized_access(self):
        dir = {
            '/': HTTPStatus.OK,
            f'/group/{self.group_ex.slug}/': HTTPStatus.OK,
            '/new/': HTTPStatus.OK,
            f'/{self.anyone.username}/{self.post_ex.id}/edit/':
                HTTPStatus.OK,
            f'/{self.anytwo.username}/{self.post_ex2.id}/edit/':
                HTTPStatus.FOUND,
        }
        for value, response in dir.items():
            with self.subTest(value=value):
                request = self.authorized_client.get(value)
                self.assertEqual(request.status_code, response)

    def test_task_list_url_redirect_anonymous_on_admin_login(self):
        """Страница /new/ перенаправит анонимного пользователя
        на страницу логина.
        """
        login = reverse('login')
        new = reverse('new_post')
        response = self.guest_client.get(new, follow=True)
        self.assertRedirects(
            response, (login + '?next=' + new)
        )

    def test_urls_uses_correct_template(self):
        '''URL-адрес использует соответствующий шаблон.'''
        templates_url_names = {
            '/': 'index.html',
            '/new/': 'new.html',
            f'/{self.anyone.username}/{self.post_ex.id}/edit/': 'new.html',
            '/group/test_slug/': 'group.html'
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
