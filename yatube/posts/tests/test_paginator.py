from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание',
        )
        posts = [Post(author=cls.user, group=cls.group,
                      text='Тестовый текст' + str(i)) for i in range(15)]
        Post.objects.bulk_create(posts)

    def setUp(self):
        self.guest_client = Client()

    def test_pages_contains_ten_and_five_records(self):
        """Проверяем, что на первой и второй странице
        количество постов 10 и 5 записей соответсвенно.
        """
        reverses_name = {
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        }
        for page in reverses_name:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(len(response.context['page_obj']), 10)
                response = self.guest_client.get(page + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 5)
