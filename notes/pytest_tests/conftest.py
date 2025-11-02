import pytest
from django.test import Client

from notes.models import Note


@pytest.fixture
def author(django_user_model):
    """Создаёт автора заметки."""
    return django_user_model.objects.create_user(username='Автор')


@pytest.fixture
def not_author(django_user_model):
    """Создаёт пользователя без прав автора."""
    return django_user_model.objects.create_user(username='Не автор')


@pytest.fixture
def author_client(author):
    """Авторизует клиента под пользователем-автором."""
    client = Client()
    client.force_login(author)
    return client


@pytest.fixture
def not_author_client(not_author):
    """Авторизует клиента под пользователем-читателем."""
    client = Client()
    client.force_login(not_author)
    return client


@pytest.fixture
def note(author):
    """Создаёт тестовую заметку автора."""
    return Note.objects.create(
        title='Заголовок',
        text='Текст заметки',
        slug='note-slug',
        author=author,
    )


@pytest.fixture
def form_data():
    """Готовит словарь данных для формы заметки."""
    return {
        'title': 'Новый заголовок',
        'text': 'Новый текст',
        'slug': 'new-slug',
    }


@pytest.fixture
def slug_for_args(note):
    """Возвращает кортеж со слагом для передачи в args."""
    return (note.slug,)
