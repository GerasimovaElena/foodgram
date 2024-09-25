import csv
import os

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка данных из CSV'

    def handle(self, *args, **kwargs):
        file_path = os.path.join(os.path.dirname(__file__), 'ingredients.csv')

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"Файл не найден: {file_path}"))
            return

        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)

            for row in reader:
                name, measurement_unit = row
                Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=measurement_unit
                )

        self.stdout.write(
            self.style.SUCCESS(f'Загрузка завершена {file_path}')
        )
