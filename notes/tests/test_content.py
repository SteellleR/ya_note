from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note


class TestContent(TestCase):
    """Тесты отображения контента в проекте YaNote."""

    @classmethod
    def setUpTestData(cls):
        """Создаёт пользователей и заметки для проверок контента."""
        User = get_user_model()
        cls.author = User.objects.create_user(username="author")
        cls.reader = User.objects.create_user(username="reader")
        # Заметка автора — должна попадать в список его заметок.
        cls.author_note = Note.objects.create(
            title="Авторская заметка",
            text="Текст автора",
            slug="author-note",
            author=cls.author,
        )
        # Заметка другого пользователя — не должна попадать в список автора.
        cls.reader_note = Note.objects.create(
            title="Чужая заметка",
            text="Текст читателя",
            slug="reader-note",
            author=cls.reader,
        )

    def test_list_shows_only_author_notes(self):
        """В список заметок попадают только заметки залогиненного пользователя."""
        self.client.force_login(self.author)
        url = reverse("notes:list")
        response = self.client.get(url)
        object_list = response.context["object_list"]
        # Своя заметка есть.
        self.assertIn(self.author_note, object_list)
        # Чужой заметки нет.
        self.assertNotIn(self.reader_note, object_list)

    def test_note_in_object_list(self):
        """Отдельная заметка автора реально передаётся в object_list."""
        self.client.force_login(self.author)
        url = reverse("notes:list")
        response = self.client.get(url)
        object_list = response.context["object_list"]
        # У автора в БД по setUpTestData ровно одна заметка — проверим это.
        self.assertEqual(object_list.count(), 1)
        self.assertEqual(object_list[0], self.author_note)

    def test_add_page_has_form(self):
        """На странице создания заметки в контексте есть форма NoteForm."""
        self.client.force_login(self.author)
        url = reverse("notes:add")
        response = self.client.get(url)
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], NoteForm)

    def test_edit_page_has_form(self):
        """На странице редактирования заметки в контексте есть форма NoteForm."""
        self.client.force_login(self.author)
        url = reverse("notes:edit", kwargs={"slug": self.author_note.slug})
        response = self.client.get(url)
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], NoteForm)
