from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, User


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст поста',
            group=cls.group
        )
        cls.form = PostForm()

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user)

    def test_create_form(self):
        """Валидная форма создает новый пост."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый пост2',
            'group': self.group.pk,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(response, reverse('posts:profile', kwargs={'username': self.user.username}))
        self.assertTrue(Post.objects.filter(text='Новый пост2', group__slug='test-slug').exists())

    def test_edit_form(self):
        """происходит изменение поста."""
        test_post = Post.objects.create(
            text='Новый пост3',
            author=self.user,
        )
        form_data_edit = {
            'text': 'Редактированный пост',
            'group': self.group.pk,
        }
        posts_count = Post.objects.count()
        response = self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': test_post.pk}),
            data=form_data_edit)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, reverse('posts:post_detail', kwargs={'post_id': test_post.pk}))
        self.assertTrue(Post.objects.filter(text='Редактированный пост', group__slug='test-slug').exists())
