from http import HTTPStatus

from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_pages_exists_at_desired_location(self):
        """Страницы автор и технологии доступны любому пользователю"""
        pages_status_code = {
            '/about/tech/': HTTPStatus.OK,
            '/about/author/': HTTPStatus.OK,
        }
        for page, code in pages_status_code.items():
            with self.subTest(page=page, code=code):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, code.value)

    def test_urls_about_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/about/tech/': 'about/tech.html',
            '/about/author/': 'about/author.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress, template=template):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)
