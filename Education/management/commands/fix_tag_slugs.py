# management/commands/fix_tag_slugs.py
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from Education.models import Tag

class Command(BaseCommand):
    help = 'Исправляет пустые и дублирующиеся slug для тегов'

    def handle(self, *args, **options):
        tags = Tag.objects.all()
        fixed_count = 0
        
        for tag in tags:
            original_slug = tag.slug
            
            # Если slug пустой или None, генерируем новый
            if not tag.slug:
                base_slug = slugify(tag.name)
                new_slug = base_slug
                counter = 1
                
                # Проверяем уникальность
                while Tag.objects.filter(slug=new_slug).exclude(pk=tag.pk).exists():
                    new_slug = f"{base_slug}-{counter}"
                    counter += 1
                
                tag.slug = new_slug
                tag.save()
                fixed_count += 1
                self.stdout.write(
                    f'Исправлен тег "{tag.name}": {original_slug} -> {new_slug}'
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Исправлено {fixed_count} тегов из {tags.count()}')
        )