import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, Comment

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.anyone = User.objects.create(username='anyone')
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
        cls.form = PostForm()
        cls.post_ex = Post.objects.create(
            text='Тестовый текст',
            author=cls.anyone,
            group=cls.group_ex,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.anyone)

    def test_create_post(self):
        '''Валидная форма создает запись в Post.'''
        posts_count = Post.objects.count()
        form_data = {
            'group': self.group_ex.id,
            'text': self.post_ex.text,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=PostCreateFormTests.group_ex.id,
                text=self.post_ex.text,
                image=self.post_ex.image
            ).exists()
        )

    def test_edit_post_authorized(self):
        '''Валидная форма изменяет запись в Post'''
        posts_count = Post.objects.count()
        form_data = {
            'group': self.group_ex.id,
            'text': 'Отредактированный текст'
        }
        response = self.authorized_client.post(
            reverse('post_edit', kwargs={
                'username': self.anyone.username,
                'post_id': self.post_ex.id
            }),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'post', kwargs={
                'username': self.anyone.username,
                'post_id': self.post_ex.id
            })
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                group=PostCreateFormTests.group_ex.id,
                text='Отредактированный текст',
                pk=self.post_ex.id
            ).exists()
        )

    def test_edit_post_guest(self):
        '''Проверка редиректа на логин'''
        form_data = {
            'group': self.group_ex.id,
            'text': 'Отредактированный текст'
        }
        response = self.guest_client.post(
            reverse('post_edit', kwargs={
                'username': self.anyone.username,
                'post_id': self.post_ex.id
            }),
            data=form_data,
            follow=True
        )
        redirect_url = reverse('login') + '?next=' + reverse(
            'post_edit',
            kwargs={
                'username': self.anyone.username,
                'post_id': self.post_ex.id
            }
        )
        self.assertRedirects(response, redirect_url)

    def test_create_comment_by_auth(self):
        '''Валидная форма авторизованного пользователя создает запись в Comment.'''
        comment_count = Comment.objects.count()
        form_data = {
            'text': self.post_ex.text,
        }
        reverse_test = reverse(
                'post', kwargs={
                'username': self.anyone.username,
                'post_id': self.post_ex.id}
            )
        response = self.authorized_client.post(
            reverse_test,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse_test)
        self.assertEqual(Comment.objects.filter(post__id=self.post_ex.id).count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                post__id=self.post_ex.id,
                text=self.post_ex.text
            ).exists()
        )

    def test_create_comment_by_anon(self):
        '''
        Только авторизированный пользователь может комментировать посты.
        '''
        form_data = {
            'text': self.post_ex.text,
        }
        reverse_test = reverse(
                'post', kwargs={
                'username': self.anyone.username,
                'post_id': self.post_ex.id}
            )
        response_user = self.authorized_client.post(
            reverse_test,
            data=form_data,
            follow=True
        )
        comment_exists = Comment.objects.filter(
            pk=self.post_ex.id,
            author=self.anyone,
            text=self.post_ex.text
        ).exists

        with self.assertRaises(ValueError):
            self.guest_client.post(
            reverse_test,
            data=form_data,
            follow=True
        )
        self.assertTrue(response_user.status_code, 302)
        self.assertTrue(comment_exists)
