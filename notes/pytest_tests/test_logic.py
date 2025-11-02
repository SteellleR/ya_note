from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertFormError, assertRedirects

from notes.forms import WARNING
from notes.models import Note
from pytils.translit import slugify


def test_user_can_create_note(author_client, author, form_data):
    response = author_client.post(reverse('notes:add'), data=form_data)
    assertRedirects(response, reverse('notes:success'))
    assert Note.objects.count() == 1
    note = Note.objects.get()
    assert note.title == form_data['title']
    assert note.text == form_data['text']
    assert note.slug == form_data['slug']
    assert note.author == author


@pytest.mark.django_db
def test_anonymous_user_cant_create_note(client, form_data):
    response = client.post(reverse('notes:add'), data=form_data)
    login_url = reverse('users:login')
    expected_redirect = f'{login_url}?next={reverse("notes:add")}'
    assertRedirects(response, expected_redirect)
    assert Note.objects.count() == 0


def test_not_unique_slug(author_client, note, form_data):
    form_data['slug'] = note.slug
    response = author_client.post(reverse('notes:add'), data=form_data)
    assertFormError(
        response.context['form'],
        'slug',
        note.slug + WARNING,
    )
    assert Note.objects.count() == 1


def test_empty_slug(author_client, form_data):
    form_data.pop('slug')
    response = author_client.post(reverse('notes:add'), data=form_data)
    assertRedirects(response, reverse('notes:success'))
    assert Note.objects.count() == 1
    new_note = Note.objects.get()
    assert new_note.slug == slugify(form_data['title'])


def test_author_can_edit_note(author_client, form_data, note):
    response = author_client.post(
        reverse('notes:edit', args=(note.slug,)),
        data=form_data,
    )
    assertRedirects(response, reverse('notes:success'))
    note.refresh_from_db()
    assert note.title == form_data['title']
    assert note.text == form_data['text']
    assert note.slug == form_data['slug']


def test_other_user_cant_edit_note(not_author_client, form_data, note):
    response = not_author_client.post(
        reverse('notes:edit', args=(note.slug,)),
        data=form_data,
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    fresh_note = Note.objects.get(id=note.id)
    assert fresh_note.title == note.title
    assert fresh_note.text == note.text
    assert fresh_note.slug == note.slug


def test_author_can_delete_note(author_client, slug_for_args):
    response = author_client.post(
        reverse('notes:delete', args=slug_for_args)
    )
    assertRedirects(response, reverse('notes:success'))
    assert Note.objects.count() == 0


def test_other_user_cant_delete_note(not_author_client, slug_for_args):
    response = not_author_client.post(
        reverse('notes:delete', args=slug_for_args)
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Note.objects.count() == 1


# В корне проекта должен быть pytest.ini c настройкой: testpaths = notes/pytest_tests
