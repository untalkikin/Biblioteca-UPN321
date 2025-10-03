import csv
from django.core.management.base import BaseCommand
from catalog.models import BibliographicRecord, Publisher, Subject, Person


class Command(BaseCommand):
    """Comando de gestión para importar registros bibliográficos desde CSV.

    El CSV debe contener columnas (al menos): `title`. Opcionales: `subtitle`,
    `resource_type`, `edition`, `language`, `publish_year`, `publisher`,
    `publish_place`, `isbn`, `issn`, `call_number`, `physical_desc`, `series`,
    `notes`, `authors` (separados por ';'), `subjects` (separados por ';').

    NOTA: Asegúrate de que los nombres de columna del CSV coincidan con los
    esperados por este script o ajusta las claves en el código.
    """

    help = "Importa registros bibliográficos desde CSV"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str)

    def handle(self, *args, **opts):
        path = opts["csv_path"]
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pub = None
                if row.get("publisher"):
                    pub, _ = Publisher.objects.get_or_create(name=row["publisher"])

                # Mapear valores del CSV a los campos del modelo. Si hay
                # columnas con nombres distintos, aquí es donde ajustarlas.
                rec, created = BibliographicRecord.objects.get_or_create(
                    title=row["title"].strip(),
                    defaults={
                        "subtitle": row.get("subtitle", ""),
                        "resource_type": row.get("resource_type", "book"),
                        "edition": row.get("edition", ""),
                        "language": row.get("language", ""),
                        "publish_year": int(row["publish_year"]) if row.get("publish_year") else None,
                        "publisher": pub,
                        "publish_place": row.get("publish_place", ""),
                        "isbn": row.get("isbn", ""),
                        "issn": row.get("issn", ""),
                        # `call_number` es la signatura LCC completa
                        "call_number": row.get("call_number", ""),
                        # Si tu CSV usa otro nombre, ajustarlo (p.ej. physical_desc -> physical_description)
                        "physical_description": row.get("physical_desc", ""),
                        "series": row.get("series", ""),
                        "notes": row.get("notes", ""),
                    }
                )

                # Autores: crear Person si no existe y añadir como contributor
                authors = [a.strip() for a in row.get("authors", "").split(";") if a.strip()]
                for a in authors:
                    p, _ = Person.objects.get_or_create(full_name=a)
                    rec.contributors.get_or_create(person=p)

                # Materias: crear Subject si no existe y enlazar
                subs = [s.strip() for s in row.get("subjects", "").split(";") if s.strip()]
                for s in subs:
                    subj, _ = Subject.objects.get_or_create(term=s)
                    rec.subjects.add(subj)

                # Si el importador creó/actualizó materias y el registro no
                # tiene lcc_code, volver a guardar para que la heurística
                # pueda usar las subjects y generar la LCC.
                if not rec.lcc_code:
                    rec.save()

                self.stdout.write(self.style.SUCCESS(f"{'Creado' if created else 'Actualizado'}: {rec.title}"))
