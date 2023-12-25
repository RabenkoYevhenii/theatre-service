import os
import uuid

from django.utils.text import slugify


def play_image_file_path(instance, filename):
    _, extension = os.path.split(filename)
    filename = f"{slugify(instance.title)}-{uuid.uuid4()}{extension}"
    return os.path.join("uploads/plays", filename)
