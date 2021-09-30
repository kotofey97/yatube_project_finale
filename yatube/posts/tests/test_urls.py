from django.test import Client, TestCase
from posts.models import Group, Post, User


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание',
        )
        Post.objects.create(
            author=cls.user,
            text='Тестовый текст поста',
        )

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user)
        self.user_1 = User.objects.create_user(username='NeAuthor')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_1)

    def test_pages_exists_at_desired_location(self):
        """Страницы доступны любому пользователю"""
        pages_status_code = {
            '/': 200,
            '/group/test-slug/': 200,
            '/profile/HasNoName/': 200,
            '/posts/1/': 200,
            '/unexisting_page/': 404,
        }
        for page, code in pages_status_code.items():
            with self.subTest(page=page, code=code):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, code)

    def test_post_create_exists_at_desired_location_authorized(self):
        """Страница /create/ доступна авторизованому."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)

    def test_post_edit_url_exists_at_desired_location(self):
        """Страница /posts/<int:post_id>/edit/ доступна автору."""
        response = self.author_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, 200)

    def test_post_create_redirect_anonymous_on_login(self):
        """Страница /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_post_edit_redirect_client_on_post_page(self):
        """Страница /posts/<int:post_id>/edit/ перенаправит неавтора поста
        на страницу поста.
        """
        response = self.authorized_client.get('/posts/1/edit/', follow=True)
        self.assertRedirects(response, '/posts/1/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/HasNoName/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/unexisting_page/': 'core/404.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress, template=template):
                response = self.author_client.get(adress)
                self.assertTemplateUsed(response, template)
