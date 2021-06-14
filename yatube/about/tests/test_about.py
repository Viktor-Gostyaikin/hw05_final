from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class AboutTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user')
        cls.url_tech = '/about/tech/'
        cls.url_author = '/about/author/'

    def setUp(self):
        self.guest_client = Client()

    def test_guest_access(self):
        '''Проверка доступности About страниц сайта'''
        response = [self.url_author, self.url_tech]
        for value in response:
            with self.subTest(value=value):
                self.assertEqual(self.guest_client.get(
                    value).status_code, HTTPStatus.OK)

    def test_template_used(self):
        """URL-адрес использует соответствующий шаблон About."""
        templates_page_names = {
            'about/author.html': self.url_author,
            'about/tech.html': self.url_tech
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_views(self):
        '''
        Для страниц /about/author/ и /about/tech/
        используются верные view-функции
        '''
        self.assertEqual(reverse('about:author'), self.url_author)
        self.assertEqual(reverse('about:tech'), self.url_tech)
