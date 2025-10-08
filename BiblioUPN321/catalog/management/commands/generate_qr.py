from django.core.management.base import BaseCommand
from catalog.models import Item


class Command(BaseCommand):
    help = "Genera códigos QR para los ejemplares que no tengan uno asignado."

    def handle(self, *args, **options):
        qs = Item.objects.filter(qr_image__isnull=True)
        total = qs.count()
        self.stdout.write(f"Encontrados {total} ejemplares sin QR.\n")
        for idx, it in enumerate(qs, start=1):
            payload = f"barcode:{it.barcode}|record:{it.record.pk}|title:{it.record.title}"
            it.generate_qr(payload)
            it.save()
            self.stdout.write(f"[{idx}/{total}] Generado QR para {it.barcode}\n")

        self.stdout.write(self.style.SUCCESS("Generación de QR completada."))
