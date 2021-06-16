import os
import shutil
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

User = get_user_model()


@override_settings(MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'temp_views'))
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user')
        cls.user_2 = User.objects.create(username='user_2')
        cls.group_ex = Group.objects.create(
            title="Тестовая группа",
            slug="test_slug",
            description="Описание",
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post_ex = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group_ex,
            image=cls.uploaded
        )
        cls.comment = Comment.objects.create(
            text='comment',
            author=cls.user,
            post=cls.post_ex
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)
        cache.clear()

    def test_template_used(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            'index.html': reverse('index'),
            'new.html': reverse('new_post'),
            'group.html': (
                reverse('group', kwargs={'slug': self.group_ex.slug}))}

        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template, reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def check_post_fields(self, post):
        self.assertEqual(
            post.text,
            self.post_ex.text
        )
        self.assertEqual(
            post.author,
            self.post_ex.author
        )
        self.assertEqual(
            post.group,
            self.post_ex.group
        )
        self.assertEqual(
            post.pub_date,
            self.post_ex.pub_date
        )
        self.assertEqual(
            post.image, self.post_ex.image)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        url = reverse('index')
        response_context = self.guest_client.get(url).context
        index_comment = response_context['page'].object_list.index(
            self.post_ex
        )

        post = response_context['page'].object_list[index_comment]

        self.assertIn('page', response_context)
        self.assertIn(self.post_ex, response_context['page'])
        self.check_post_fields(post)

    def test_group_page_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        url = reverse('group', kwargs={'slug': self.group_ex.slug})

        response_context = self.guest_client.get(url).context
        index_post = response_context['page'].object_list.index(
            self.post_ex
        )
        post = response_context['page'].object_list[index_post]

        self.assertIn('group', response_context)
        self.assertIsInstance(response_context['group'], Group)
        self.assertEqual(response_context['group'].slug, self.group_ex.slug)
        self.assertEqual(
            response_context['group'].description, self.group_ex.description)
        self.assertEqual(response_context['group'].title, self.group_ex.title)
        self.assertIn('page', response_context)
        self.assertIn(self.post_ex, response_context['page'])
        self.check_post_fields(post)

    def test_new_post_page_show_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField}

        get_context = self.authorized_client.get(reverse('new_post')).context
        response = self.authorized_client.get(reverse('new_post'))

        self.assertIn('form', get_context)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_context(self):
        '''Страница post_edit сформирована с правильным контекстом.'''
        reverse_name = reverse(
            'post_edit', kwargs={
                'username': self.user.username,
                'post_id': self.post_ex.id
            }
        )
        form_context = {
            'post': self.post_ex
        }
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField
        }

        response = self.authorized_client.get(reverse_name)

        for value, expected in form_context.items():
            with self.subTest(value=value):
                self.assertEqual(response.context[value], expected)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_profile_context(self):
        '''Шаблон profile сформирован с правильным контекстом.'''
        url = reverse('profile', kwargs={'username': self.user.username})
        count_of_posts = Post.objects.filter(author=self.user).count()
        expected = {'author': self.user, 'count_of_posts': count_of_posts}

        response_context = self.guest_client.get(url).context
        response_auth = self.authorized_client.get(url).context
        index_comment = response_context['page'].object_list.index(
            self.post_ex
        )
        post = response_context['page'].object_list[index_comment]

        for item_context, expect in expected.items():
            with self.subTest(item_context=item_context):
                self.assertIn(item_context, response_context)
                self.assertEqual(response_context[item_context], expect)
        self.assertIn('user', response_context)
        self.assertEqual(response_context['user'].username, '')
        self.assertEqual(response_auth['user'].username, self.user.username)
        self.assertIn('page', response_context)
        self.check_post_fields(post)

    def test_post_page_context(self):
        '''Страница post сформирована с правильным контекстом'''
        url = reverse(
            'post', kwargs={
                'username': self.user.username,
                'post_id': self.post_ex.id
            }
        )
        expected = {'author': self.user, 'post': self.post_ex}

        response_context = self.guest_client.get(url).context
        response_auth = self.authorized_client.get(url).context
        post = response_context['post']
        index_comment = response_context['page'].object_list.index(
            self.comment
        )

        for item_context, expect in expected.items():
            with self.subTest(item_context=item_context):
                self.assertIn(item_context, response_context.keys())
                self.assertEqual(response_context[item_context], expect)
        self.assertIn('user', response_context.keys())
        self.assertEqual(response_context['user'].username, '')
        self.assertEqual(response_auth['user'].username, self.user.username)
        self.assertIn('page', response_context.keys())
        self.check_post_fields(post)
        self.assertEqual(
            response_context['page'].object_list[index_comment].text,
            self.comment.text
        )
        self.assertEqual(
            response_context['page'].object_list[index_comment].author,
            self.comment.author
        )
        self.assertEqual(
            response_context['page'].object_list[index_comment].post,
            self.post_ex
        )

    def test_index_cache(self):
        '''К странице  подключена система кэширования'''
        url = reverse('index')
        response_content = self.guest_client.get(url).content
        Post.objects.create(
            text='Тестовый текст2',
            author=self.user
        )
        response_content_2 = self.guest_client.get(url).content
        self.assertEqual(response_content, response_content_2)
        cache.clear()
        response_content_3 = self.guest_client.get(url).content
        self.assertNotEqual(response_content, response_content_3)

    def test_follow_auth(self):
        '''
        Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок.
        '''
        url_follow = reverse(
            'profile_follow',
            kwargs={'username': self.user_2.username}
        )
        url_unfollow = reverse(
            'profile_unfollow',
            kwargs={'username': self.user_2.username}
        )

        response_follow = self.authorized_client.get(url_follow)

        self.assertEqual(response_follow.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response_follow, reverse(
            'profile',
            kwargs={'username': self.user_2.username})
        )
        self.assertTrue(Follow.objects.filter(
            user=self.user,
            author=self.user_2).exists()
        )

        response_unfollow = self.authorized_client.get(url_unfollow)

        self.assertEqual(response_unfollow.status_code, HTTPStatus.FOUND)
        self.assertFalse(Follow.objects.filter(
            user=self.user,
            author=self.user_2).exists()
        )

    def test_follow_anon(self):
        '''
        Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех,
        кто не подписан на него.
        '''
        url_follow = reverse(
            'profile_follow',
            kwargs={'username': self.user_2.username}
        )
        response_follow = self.authorized_client.get(url_follow)

        self.assertEqual(response_follow.status_code, HTTPStatus.FOUND)

        follower = Follow.objects.get(user=self.user)
        posts_count = Post.objects.filter(author__following=follower).count()
        form_data = {'text': self.post_ex.text}

        response = self.authorized_client_2.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        posts_count_2 = Post.objects.filter(author__following=follower).count()

        self.assertEqual(posts_count_2, posts_count + 1)
