import os
import tempfile

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from theatre_service.models import Play, Genre, Actor, TheatreHall, Performance
from theatre_service.serializers import (
    PlayListSerializer,
    PlayDetailSerializer,
)

PLAY_URL = reverse("theatre_service:play-list")
PERFORMANCE_URL = reverse("theatre_service:performance-list")


def sample_play(**params):
    defaults = {
        "title": "Sample play",
        "description": "Sample description",
    }
    defaults.update(params)

    return Play.objects.create(**defaults)


def sample_genre(**params):
    defaults = {
        "name": "Drama",
    }
    defaults.update(params)

    return Genre.objects.create(**defaults)


def sample_actor(**params):
    defaults = {"first_name": "Michael", "last_name": "Jackson"}
    defaults.update(params)

    return Actor.objects.create(**defaults)


def sample_performance(**params):
    theatre_hall = TheatreHall.objects.create(
        name="Main", rows=15, seats_in_row=20
    )

    defaults = {
        "showtime": "2023-11-12 14:00:00",
        "play": None,
        "theatre_hall": theatre_hall,
    }
    defaults.update(params)

    return Performance.objects.create(**defaults)


def image_upload_url(play_id):
    """Return URL for recipe image upload"""
    return reverse("theatre_service:play-upload-image", args=[play_id])


def detail_url(play_id):
    return reverse("theatre_service:play-detail", args=[play_id])


class PlayImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "adminuser@admin.com", "password258"
        )
        self.client.force_authenticate(self.user)
        self.play = sample_play()
        self.genre = sample_genre()
        self.actor = sample_actor()
        self.performance = sample_performance(play=self.play)

    def tearDown(self):
        self.play.image.delete()

    def test_upload_image_to_play(self):
        """Test uploading an image to play"""
        url = image_upload_url(self.play.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.play.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.play.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.play.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_play_list(self):
        url = PLAY_URL
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                url,
                {
                    "title": "Title",
                    "description": "Description",
                    "image": ntf,
                },
                format="multipart",
            )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        play = Play.objects.get(title="Title")
        self.assertFalse(play.image)

    def test_image_url_is_shown_on_play_detail(self):
        url = image_upload_url(self.play.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(detail_url(self.play.id))

        self.assertIn("image", res.data)

    def test_image_url_is_shown_on_play_list(self):
        url = image_upload_url(self.play.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(PLAY_URL)

        self.assertIn("image", res.data["results"][0].keys())

    def test_image_url_is_shown_on_performance_detail(self):
        url = image_upload_url(self.play.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(PERFORMANCE_URL)

        self.assertIn("play_image", res.data[0].keys())


class UnauthenticatedPlayApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(PLAY_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedPlayApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com", "test12345"
        )
        self.client.force_authenticate(self.user)

    def test_list_plays(self):
        sample_play()
        play_with_genre = sample_play(title="Test Genre")
        play_with_actor = sample_play(title="Test Actor")

        genre = sample_genre(name="Test")
        actor = sample_actor(first_name="TestName")

        play_with_genre.genres.add(genre)
        play_with_actor.actors.add(actor)

        response = self.client.get(PLAY_URL)

        plays_from_response = response.data.get("results", [])

        plays = Play.objects.all()
        serializer = PlayListSerializer(plays, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(plays_from_response, serializer.data)

    def test_filter_plays_by_genre(self):
        play_with_genre = sample_play(title="Test With Genre")
        play_without_genre = sample_play(title="Test Without Genre")

        genre = sample_genre(name="Test")
        play_with_genre.genres.add(genre)

        response = self.client.get(PLAY_URL, {"genres": f"{genre.id}"})

        serializer_play_with_genre = PlayListSerializer(play_with_genre)
        serializer_play_without_genre = PlayListSerializer(play_without_genre)

        expected_data_play_with_genre = tuple(
            (field, value)
            for field, value in serializer_play_with_genre.data.items()
            if field != "actors"
        )
        actual_data = list(
            map(
                lambda play: tuple(
                    (field, value) for field, value in play.items()
                    if field != "actors"
                ),
                response.data.get("results", []),
            )
        )

        self.assertIn(expected_data_play_with_genre, actual_data)
        self.assertNotIn(
            tuple(serializer_play_without_genre.data.items()), actual_data
        )

    def test_filter_plays_by_actor(self):
        play_with_actor = sample_play(title="Test With Actor")
        play_without_actor = sample_play(title="Test Without Actor")

        actor = sample_actor(first_name="TestName")
        play_with_actor.actors.add(actor)

        response = self.client.get(PLAY_URL, {"actors": f"{actor.id}"})

        serializer1 = PlayListSerializer(play_with_actor)
        serializer2 = PlayListSerializer(play_without_actor)

        expected_data = tuple(
            (field, value)
            for field, value in serializer1.data.items()
            if field != "actors"
        )
        actual_data = list(
            map(
                lambda play: tuple(
                    (field, value) for field, value in play.items()
                    if field != "actors"
                ),
                response.data.get("results", []),
            )
        )

        self.assertIn(expected_data, actual_data)
        self.assertNotIn(tuple(serializer2.data.items()), actual_data)

    def test_filter_plays_by_title(self):
        play_with_title = sample_play(title="Ukraine")
        play_without_title = sample_play(title="Test")

        response = self.client.get(PLAY_URL, {"title": "Ukraine"})

        serializer_play_with_title = PlayListSerializer(play_with_title)
        serializer_play_without_title = PlayListSerializer(play_without_title)

        expected_data_play_with_title = tuple(
            (field, value)
            for field, value in serializer_play_with_title.data.items()
            if field != "actors"
        )
        actual_data = list(
            map(
                lambda play: tuple(
                    (field, value) for field, value in play.items()
                    if field != "actors"
                ),
                response.data.get("results", []),
            )
        )

        self.assertIn(expected_data_play_with_title, actual_data)
        self.assertNotIn(
            tuple(serializer_play_without_title.data.items()), actual_data
        )

    def test_retrieve_play_detail(self):
        play = sample_play(title="Test")
        genre = sample_genre(name="Test")

        play.genres.add(genre)

        url = detail_url(play.id)

        response = self.client.get(url)

        serializer = PlayDetailSerializer(play)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_play_forbidden(self):
        payload = {
            "title": "Test Title",
            "description": "Test Description",
        }
        response = self.client.post(PLAY_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminPlayApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "adminuser2@admin.com", "test12345", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_play(self):
        payload = {
            "title": "Test Title",
            "description": "Test Description",
        }

        response = self.client.post(PLAY_URL, payload)
        play = Play.objects.get(id=response.data["id"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key in payload:
            self.assertEqual(payload[key], getattr(play, key))

    def test_create_play_with_actor_and_genre(self):
        genre = sample_genre(name="Test")

        actor = sample_actor(first_name="TestName")

        payload = {
            "title": "play",
            "description": "description",
            "genres": [genre.id],
            "actors": [actor.id],
        }

        response = self.client.post(PLAY_URL, payload)
        play = Play.objects.get(id=response.data["id"])

        genres = play.genres.all()
        actors = play.actors.all()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn(genre, genres)
        self.assertIn(actor, actors)
