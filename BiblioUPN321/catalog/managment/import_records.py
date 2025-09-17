import csv
from django.core.management.base import BaseCommand
from catalog.models import BibliographicRecord, Publisher, Subject, Person

class Command(BaseCommand):
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
                rec, created = BibliographicRecord.objects.get_or_create(
                    title=row["title"].strip(),
                    defaults={
                        "subtitle": row.get("subtitle",""),
                        "resource_type": row.get("resource_type","book"),
                        "edition": row.get("edition",""),
                        "language": row.get("language",""),
                        "publish_year": int(row["publish_year"]) if row.get("publish_year") else None,
                        "publisher": pub,
                        "publish_place": row.get("publish_place",""),
                        "isbn": row.get("isbn",""),
                        "issn": row.get("issn",""),
                        "lccn": row.get("lccn",""),
                        "call_number": row.get("call_number",""),
                        "physical_desc": row.get("physical_desc",""),
                        "series": row.get("series",""),
                        "notes": row.get("notes",""),
                    }
                )
                # autores
                authors = [a.strip() for a in row.get("authors","").split(";") if a.strip()]
                for a in authors:
                    p, _ = Person.objects.get_or_create(full_name=a)
                    rec.contributors.get_or_create(person=p)
                # materias
                subs = [s.strip() for s in row.get("subjects","").split(";") if s.strip()]
                for s in subs:
                    subj, _ = Subject.objects.get_or_create(term=s)
                    rec.subjects.add(subj)

                self.stdout.write(self.style.SUCCESS(f"{'Creado' if created else 'Actualizado'}: {rec.title}"))
