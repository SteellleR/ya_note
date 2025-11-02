from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note


class TestRoutes(TestCase):
    """Тесты доступности маршрутов приложения заметок."""

    @classmethod
    def setUpTestData(cls):
        """Создаёт автора, читателя и заметку для проверки маршрутов."""
        user_model = get_user_model()
        cls.author = user_model.objects.create_user(username='author')
        cls.reader = user_model.objects.create_user(username='reader')
        cls.note = Note.objects.create(
            title='Test note',
            text='Test note text',
            slug='note-slug',
            author=cls.author,
        )

    def test_public_pages_available_for_anonymous(self):
        """Публичные страницы доступны анонимному пользователю."""
        urls = (
            reverse('notes:home'),
            reverse('users:login'),
            reverse('users:signup'),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_author_has_access_to_note_pages(self):
        """Автор имеет доступ ко всем страницам своей заметки."""
        self.client.force_login(self.author)
        urls = (
            reverse('notes:list'),
            reverse('notes:add'),
            reverse('notes:success'),
            reverse('notes:detail', kwargs={'slug': self.note.slug}),
            reverse('notes:edit', kwargs={'slug': self.note.slug}),
            reverse('notes:delete', kwargs={'slug': self.note.slug}),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_reader_cannot_access_someone_else_note(self):
        """Читатель не получает доступ к чужой заметке."""
        self.client.force_login(self.reader)
        urls = (
            reverse('notes:detail', kwargs={'slug': self.note.slug}),
            reverse('notes:edit', kwargs={'slug': self.note.slug}),
            reverse('notes:delete', kwargs={'slug': self.note.slug}),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_anonymous_redirects_to_login(self):
        """Анонимный пользователь перенаправляется на страницу входа."""
        login_url = reverse('users:login')
        urls = (
            reverse('notes:list'),
            reverse('notes:add'),
            reverse('notes:success'),
            reverse('notes:detail', kwargs={'slug': self.note.slug}),
            reverse('notes:edit', kwargs={'slug': self.note.slug}),
            reverse('notes:delete', kwargs={'slug': self.note.slug}),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                expected_redirect = f'{login_url}?next={url}'
                self.assertRedirects(response, expected_redirect)
