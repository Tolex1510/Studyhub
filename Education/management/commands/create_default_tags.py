# management/commands/create_default_tags.py
from django.core.management.base import BaseCommand
from Education.models import Tag

class Command(BaseCommand):
    help = 'Создает стандартные теги для курсов'

    def handle(self, *args, **options):
        default_tags = [
            {'name': 'Python', 'color': '#3776AB', 'description': 'Курсы по Python'},
            {'name': 'JavaScript', 'color': '#F7DF1E', 'description': 'Курсы по JavaScript'},
            {'name': 'Веб-разработка', 'color': '#61DAFB', 'description': 'Веб-разработка'},
            {'name': 'Data Science', 'color': '#306998', 'description': 'Наука о данных'},
            {'name': 'Для начинающих', 'color': '#28A745', 'description': 'Курсы для новичков'},
            {'name': 'Продвинутый', 'color': '#DC3545', 'description': 'Продвинутые курсы'},
            {'name': 'Проекты', 'color': '#6F42C1', 'description': 'Курсы с реальными проектами'},
        ]
        
        created_count = 0
        for tag_data in default_tags:
            tag, created = Tag.objects.get_or_create(
                name=tag_data['name'],
                defaults=tag_data
            )
            if created:
                created_count += 1
                self.stdout.write(f'Создан тег: {tag.name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Создано {created_count} тегов из {len(default_tags)}')
        )