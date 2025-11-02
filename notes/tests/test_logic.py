from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note


class TestNoteLogic(TestCase):
    """Тесты бизнес-логики заметок."""

    @classmethod
    def setUpTestData(cls):
        """Создаёт автора, читателя и исходную заметку."""
        user_model = get_user_model()
        cls.author = user_model.objects.create_user(username='author')
        cls.not_author = user_model.objects.create_user(username='not-author')
        cls.note = Note.objects.create(
            title='Исходная заметка',
            text='Исходный текст',
            slug='initial-slug',
            author=cls.author,
        )

    def test_auth_user_can_create_note(self):
        """Авторизованный пользователь может создать заметку."""
        self.client.force_login(self.author)
        url = reverse('notes:add')
        form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug',
        }
        response = self.client.post(url, data=form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)
        new_note = Note.objects.get(slug='new-slug')
        self.assertEqual(new_note.title, form_data['title'])
        self.assertEqual(new_note.text, form_data['text'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_cant_create_note(self):
        """Неавторизованный пользователь перенаправляется при создании."""
        url = reverse('notes:add')
        form_data = {
            'title': 'Анонимная заметка',
            'text': 'Текст',
            'slug': 'anon-slug',
        }
        response = self.client.post(url, data=form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), 1)

    def test_cant_create_note_with_existing_slug(self):
        """Нельзя создать заметку с уже занятым слагом."""
        self.client.force_login(self.author)
        url = reverse('notes:add')
        form_data = {
            'title': 'Дубликат',
            'text': 'Текст',
            'slug': self.note.slug,
        }
        response = self.client.post(url, data=form_data)
        form = response.context['form']
        self.assertFormError(
            form,
            'slug',
            self.note.slug + WARNING,
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug_autofilled(self):
        """Пустой слаг автоматически заполняется из заголовка."""
        self.client.force_login(self.author)
        url = reverse('notes:add')
        title = 'Заметка без слага'
        form_data = {
            'title': title,
            'text': 'Какой-то текст',
            'slug': '',
        }
        response = self.client.post(url, data=form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)
        created_note = Note.objects.exclude(id=self.note.id).get()
        expected_slug = slugify(title)[:100]
        self.assertEqual(created_note.slug, expected_slug)

    def test_author_can_edit_note(self):
        """Автор может отредактировать свою заметку."""
        self.client.force_login(self.author)
        url = reverse('notes:edit', args=(self.note.slug,))
        form_data = {
            'title': 'Обновлённый заголовок',
            'text': 'Обновлённый текст',
            'slug': 'updated-slug',
        }
        response = self.client.post(url, data=form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, form_data['title'])
        self.assertEqual(self.note.text, form_data['text'])
        self.assertEqual(self.note.slug, form_data['slug'])

    def test_not_author_cant_edit_note(self):
        """Другой пользователь не может редактировать чужую заметку."""
        self.client.force_login(self.not_author)
        url = reverse('notes:edit', args=(self.note.slug,))
        form_data = {
            'title': 'Попытка изменить',
            'text': 'Попытка изменить текст',
            'slug': 'hack-slug',
        }
        response = self.client.post(url, data=form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(note_from_db.title, self.note.title)
        self.assertEqual(note_from_db.text, self.note.text)
        self.assertEqual(note_from_db.slug, self.note.slug)

    def test_author_can_delete_note(self):
        """Автор может удалить свою заметку."""
        self.client.force_login(self.author)
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_not_author_cant_delete_note(self):
        """Другой пользователь не может удалить чужую заметку."""
        self.client.force_login(self.not_author)
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
