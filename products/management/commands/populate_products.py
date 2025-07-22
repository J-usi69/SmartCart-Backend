import json
from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = 'Popula la tabla Product y sus relaciones desde un JSON externo.'

    def add_arguments(self, parser):
        parser.add_argument(
            'data_file',
            type=str,
            help='Ruta al archivo JSON con datos de productos'
        )

    def handle(self, *args, **options):
        path = options['data_file']
        try:
            with open(path, encoding='utf-8') as f:
                records = json.load(f)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'❌ No pude leer el JSON: {e}'))
            return


        for rec in records:
            defaults = {
                'description': rec.get('description', ''),
                'price': rec['price'],
                'stock': rec['stock'],
                'is_active': rec.get('is_active', True),
                'has_discount': rec.get('has_discount', False),
                'discount_percentage': rec.get('discount_percentage', 0),
            }
            obj, created = Product.objects.update_or_create(
                name=rec['name'],
                defaults=defaults
            )
            action = '✅ Creado' if created else '🔄 Actualizado'
            self.stdout.write(f'{action} → {obj.name} (ID: {obj.pk})')


        for rec in records:
            related_ids = rec.get('related_ids', [])
            if not related_ids:
                continue
            prod = Product.objects.get(name=rec['name'])
            related_qs = Product.objects.filter(id__in=related_ids)
            prod.related_products.set(related_qs)
            names = ', '.join(related_qs.values_list('name', flat=True))
            self.stdout.write(f'🔗 Relaciones "{prod.name}": {names}')

        self.stdout.write(self.style.SUCCESS('🎉 Poblamiento completado.'))
