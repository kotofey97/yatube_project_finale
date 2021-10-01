import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст поста',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.user2 = User.objects.create_user(username='TestttUser')
        cls.group2 = Group.objects.create(
            title='Тестовое название группы2',
            slug='test-slug2',
            description='Тестовое описание2',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user)
        self.user_1 = User.objects.create_user(username='NeAuthor')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """view-функция использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template, reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_show_correct_context(self):
        """Шаблоны index, group_list, profile
        сформированы с правильным контекстом.
        """
        templates_pages_names = {
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        }
        for reverse_name in templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                first_object = response.context.get('page_obj')[0]
                post_author_0 = first_object.author
                post_id_0 = first_object.pk
                post_text_0 = first_object.text
                post_group_0 = first_object.group.slug
                post_image_0 = first_object.image
                # print(response.context.get('page_obj').object_list)
                self.assertEqual(post_author_0, self.post.author)
                self.assertEqual(post_id_0, self.post.pk)
                self.assertEqual(post_text_0, self.post.text)
                self.assertEqual(post_group_0, self.group.slug)
                self.assertEqual(post_image_0, self.post.image)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        rev = reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        response = self.author_client.get(rev)
        first_object = response.context.get('post')
        post_author_0 = first_object.author
        post_id_0 = first_object.pk
        post_text_0 = first_object.text
        post_group_0 = first_object.group.slug
        post_image_0 = first_object.image
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_id_0, self.post.pk)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_group_0, self.group.slug)
        self.assertEqual(post_image_0, self.post.image)

    def test_post_create_or_edit_correct_context(self):
        """Шаблоны создания и редактирования поста
        сформированы с правильным контекстом.
        """
        reverses_name = {
            reverse('posts:post_create'): None,
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}): True,
        }
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for name, flag in reverses_name.items():
            with self.subTest(name=name, flag=flag):
                response = self.author_client.get(name)
                edit_flag = response.context.get('is_edit')
                self.assertEqual(edit_flag, flag)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get(
                            'form').fields.get(value)
                        self.assertIsInstance(form_field, expected)

    def test_new_post_correct_context(self):
        """При создании пост появляется в index, group_list, profile."""
        templates_pages_names = {
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': self.group2.slug}),
            reverse('posts:profile', kwargs={'username': self.user2.username}),
        }
        post2 = Post.objects.create(
            author=self.user2,
            text='Тестовый текст поста',
            group=self.group2
        )
        for reverse_name in templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                first_object = response.context.get('page_obj')[0]
                post_author_0 = first_object.author
                post_text_0 = first_object.text
                post_group_0 = first_object.group.slug
                self.assertEqual(post_author_0, post2.author)
                self.assertEqual(post_text_0, post2.text)
                self.assertEqual(post_group_0, self.group2.slug)

    def test_cache_index_page(self):
        page = reverse('posts:index')
        response_0 = self.authorized_client.get(page)
        post_0 = Post.objects.create(text="Test",
                                     author=self.user,
                                     group=self.group)
        response_1 = self.authorized_client.get(page)
        Post.objects.filter(pk=post_0.pk).delete()
        response_2 = self.authorized_client.get(page)
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.authorized_client.get(page)
        self.assertEqual(response_0.content, response_3.content)

    def test_follow_another_user(self):
        """Follow на другого пользователя работает корректно"""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user2.username}))
        follow_exist = Follow.objects.filter(user=self.user,
                                             author=self.user2).exists()
        self.assertTrue(follow_exist)

    def test_unfollow_another_user(self):
        """Unfollow от другого пользователя работает корректно"""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user2.username}))
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user2.username}))
        follow_exist = Follow.objects.filter(user=self.user,
                                             author=self.user2).exists()
        self.assertFalse(follow_exist)

    def test_new_post_follow_index_show_correct_context(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан
        """
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user2.username}))
        follow_exist = Follow.objects.filter(user=self.user,
                                             author=self.user2).exists()
        self.assertTrue(follow_exist)
        post2 = Post.objects.create(
            author=self.user2,
            text='Тестовый текст поста',
            group=self.group2
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        count0 = len(response.context.get('page_obj'))
        first_object = response.context.get('page_obj').object_list[0]
        post_author_0 = first_object.author
        post_text_0 = first_object.text
        post_group_0 = first_object.group.slug
        self.assertEqual(post_author_0, post2.author)
        self.assertEqual(post_text_0, post2.text)
        self.assertEqual(post_group_0, self.group2.slug)

        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user2.username}))
        follow_exist = Follow.objects.filter(user=self.user,
                                             author=self.user2).exists()
        self.assertFalse(follow_exist)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        count1 = len(response.context.get('page_obj'))
        self.assertEqual(count0 - 1, count1)
