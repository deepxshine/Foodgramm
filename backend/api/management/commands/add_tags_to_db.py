import csv

from django.core.management.base import BaseCommand

from foodgram.settings import CSV_FILES_DIR
from recipes.models import Tag


class Command(BaseCommand):
    help = 'Добавление тегов в базу данных'

    def handle(self, *args, **kwargs):
        with open(
                f'{CSV_FILES_DIR}/tags.csv', encoding='utf-8'
        ) as f:
            csv_reader = csv.reader(f, delimiter=',', quotechar='"')
            for row in csv_reader:
                name = row[0]
                color = row[1]
                slug = row[2]
                Tag.objects.create(
                    name=name, color=color, slug=slug
                )
