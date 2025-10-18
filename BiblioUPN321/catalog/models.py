import uuid
from django.db import models
from django.core.validators import RegexValidator 
from django.utils.translation import gettext_lazy as _
import io, qrcode
from django.core.files.base import ContentFile

from .services.lcc import generate_lcc, normalize_lcc, split_lcc, build_call_number, build_sort_key

LCC_REGEX = r"^[A-Z]{1,3}\s?\d{1,4}(\.\d+)?(\s?[A-Z]\d+)?(\s?\.\w+)?(\s?\d{4})?$"
# Modelo base abstracto para proveer marcas de tiempo comunes a todos
# los registros (creado/actualizado). Útil para auditoría y ordenamientos.
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Publisher(TimeStampedModel):
    """Editorial o entidad responsable de la publicación.

    Campos:
    - name: Nombre de la editorial.
    - place: Lugar de publicación (opcional).
    """
    name = models.CharField(max_length=255)
    place = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return self.name


class Subject(TimeStampedModel):
    """Término temático usado para describir el contenido (materia).

    Ejemplo: 'Programación', 'Historia del Perú', 'Matemáticas'
    """
    term = models.CharField(max_length=255, unique=True)
    
    def __str__(self):
        return self.term
    

class Location(TimeStampedModel):
    """Ubicación física dentro de la biblioteca (sección/estantería).

    - code: Código corto (p. ej. 'A1', 'REF', 'B3')
    - name: Descripción legible de la ubicación.
    """
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    

class Person(TimeStampedModel):
    """Persona relacionada con una obra: autor, editor, traductor, etc.

    - given: Nombres.
    - family: Apellidos.
    - full_name: Nombre completo usado para búsquedas y display.
    - VIAF / ORCID: Identificadores externos opcionales para enlazar
      a autoridades o perfiles académicos.
    """
    given = models.CharField(_("Nombres"), max_length=255, blank=True)
    family = models.CharField(_("Apellidos"), max_length=255, blank=True)
    full_name = models.CharField(max_length=255, unique=True)
    VIAF = models.CharField(max_length=50, blank=True)
    ORCID = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return self.full_name or f"{self.family}, {self.given}".strip(", ")
    

class BibliographicRecord(TimeStampedModel):
    """Registro bibliográfico principal que representa una obra.

    Incluye metadatos típicos: título, tipo de recurso, identificadores
    (ISBN/ISSN), signatura LCC y campos auxiliares para facilitar búsquedas
    y ordenamiento en colecciones físicas.
    """
    class ResourceType(models.TextChoices):
        BOOK = "book", _("Libro")
        THESIS = "thesis", _("Tesis")
        ARTICLE = "article", _("Articulo")
        REPORT = "report", _("Reporte")
        AUDIO = "audio", _("Audio")
        VIDEO = "video", _("Video")
        OTHER = "other", _("Otro")
    
    title = models.CharField(max_length=512)
    subtitle = models.CharField(max_length=512, blank=True)
    resource_type = models.CharField(max_length=20, choices=ResourceType.choices, default=ResourceType.BOOK)
    edition = models.CharField(max_length=128, blank=True)
    language = models.CharField(max_length=64, blank=True)
    publish_year = models.PositiveIntegerField(null=True, blank=True)
    publisher = models.ForeignKey(Publisher, null=True, blank=True, on_delete=models.SET_NULL)
    publish_place = models.CharField(max_length=255, blank=True)
    lcc_code = models.CharField(
        "Clasificación LCC",
        max_length=32,
        blank=True,
        null=True,
        db_index=True,
        validators=[RegexValidator(
            regex=LCC_REGEX,
            message="Formato LCC inválido (ej. 'QA76.73 .P98 2023')."
        )],
        help_text="Código de la Clasificación de la Library of Congress."
    )

    # Opcional: conservar la “razón” o pista de cómo se generó
    lcc_source = models.CharField(
        max_length=64, blank=True, null=True,
        help_text="Origen: heurística, asignación manual, importación, etc."
    )

    isbn = models.CharField(max_length=32, blank=True, null=True)
    issn = models.CharField(max_length=32, blank=True, null=True)
    iccn = models.CharField(max_length=32, blank=True, null=True)

    # Signatura LCC completa: usada para localización y clasificación.
    call_number = models.CharField(
        max_length=128, blank=True,
        help_text=_("Signatura LCC completa, ej: QA76.73.P98 D45 2021"),
    )
    
    # Campos desglosados de la signatura para facilitar ordenamiento
    # y búsquedas por clase, número y cutter.
    lcc_class = models.CharField(max_length=2, blank=True)      # ej: 'QA'
    lcc_number = models.CharField(max_length=16, blank=True)     # ej: '76.73'
    cutter = models.CharField(max_length=32, blank=True)         # ej: 'P98'
    cutter2 = models.CharField(max_length=32, blank=True)        # ej: 'D45'
    
    physical_description = models.CharField(max_length=255, blank=True)
    series = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    
    # Relaciones
    subjects = models.ManyToManyField(Subject, blank=True)
    cover = models.ImageField(upload_to='covers/', null=True, blank=True)
    inventory_code = models.CharField(max_length=64, unique=True, blank=True)
    qr_image = models.ImageField(upload_to="qr/", blank=True, null=True)
    
    class Meta:
        ordering = ["lcc_class", "lcc_number", "cutter", "title"]
        indexes = [
        models.Index(fields=["lcc_class", "lcc_number", "cutter"]),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("catalog:record_detail", args=[self.pk])

    # ---------- Lógica QR ----------
    def get_qr_payload(self) -> str:
        # Incluye pk + inventory_code => único y estable
        # Ajusta el dominio/base a tu despliegue real o usa reverse con sitio
        return f"/catalog/record/{self.pk}/?inv={self.inventory_code}"

    def _generate_qr_contentfile(self) -> ContentFile:
        data = self.get_qr_payload()
        img = qrcode.make(data)  # Requiere Pillow instalado
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return ContentFile(buf.getvalue())

    # ---------- Override save ----------
    def save(self, *args, **kwargs):
        # 0) Inventory code único si falta
        if not self.inventory_code:
            self.inventory_code = f"UPN-{uuid.uuid4().hex[:8].upper()}"

        # 1) Preparar texto de materias sólo si ya existe pk (M2M requiere pk)
        subjects_text = getattr(self, "_subjects_text", None)
        if subjects_text is None and self.pk:
            try:
                subjects_text = " ".join(self.subjects.values_list("term", flat=True))
            except Exception:
                subjects_text = ""

        # 2) Generar/normalizar LCC si hace falta
        if not self.lcc_code:
            generated, source = generate_lcc(self, subjects_text=subjects_text)
            if generated:
                self.lcc_code = normalize_lcc(generated)
                self.lcc_source = source or "heurística"
        else:
            self.lcc_code = normalize_lcc(self.lcc_code)

        # 3) Derivados de LCC
        if self.lcc_code:
            parts = split_lcc(self.lcc_code)  # dict con lcc_class, lcc_number, cutter, cutter2, year
            self.lcc_class = parts.get("lcc_class") or self.lcc_class
            self.lcc_number = parts.get("lcc_number") or self.lcc_number
            self.cutter = self.cutter or parts.get("cutter", "")
            self.cutter2 = self.cutter2 or parts.get("cutter2", "")

            # Año (si no hay publish_year explícito)
            if not self.publish_year and parts.get("year"):
                try:
                    self.publish_year = int(parts["year"])
                except (TypeError, ValueError):
                    pass

            # Signatura completa
            self.call_number = build_call_number({
                "lcc_class": self.lcc_class,
                "lcc_number": self.lcc_number,
                "cutter": self.cutter,
                "cutter2": self.cutter2,
                "year": (str(self.publish_year) if self.publish_year else parts.get("year")),
            })

        # 4) Primer guardado: asegura pk antes de generar QR
        new_record = self.pk is None
        super().save(*args, **kwargs)

        # 5) Generar QR si no existe
        if not self.qr_image:
            png = self._generate_qr_contentfile()
            self.qr_image.save(f"rec_{self.pk}.png", png, save=False)
            super().save(update_fields=["qr_image"])
    

class RecordContributor(models.Model):
    """Relación N:M entre `BibliographicRecord` y `Person` con rol.

    Permite almacenar autores, editores, traductores, etc. Un mismo
    `person` puede aparecer en distintos roles para un mismo registro.
    """
    class Role(models.TextChoices):
        AUTHOR = "author", _("Autor")
        EDITOR = "editor", _("Editor")
        TRANSLATOR = "translator", _("Traductor")
        COMPILER = "compiler", _("Compilador")
        
    record = models.ForeignKey(BibliographicRecord, on_delete=models.CASCADE, related_name="contributors")
    person =  models.ForeignKey(Person, on_delete=models.PROTECT)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.AUTHOR)
    
    class Meta:
        # Evita duplicados exactos (misma persona y rol para un registro)
        unique_together = ("record", "person", "role")
        
    def __str__(self):
        return f"{self.person} ({self.get_role_display()})"
    

class Item(TimeStampedModel):
    """Copia física o ejemplar de un `BibliographicRecord`.

    - barcode: Identificador único físico del ejemplar (lectores de código
      de barras en la biblioteca lo usan para préstamos).
    - location: Ubicación física dentro de la biblioteca.
    - status: Estado del ejemplar (disponible, prestado, perdido, etc.).
    """
    class Status(models.TextChoices):
        AVAILABLE = "available", _("Disponible")
        LOANED = "loaned", _("Prestado")
        REPAIR = "repair", _("En reparacion")
        LOST = "lost", _("Perdido")

    record = models.ForeignKey(BibliographicRecord, on_delete=models.CASCADE, related_name="items")
    barcode = models.CharField(max_length=64, unique=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    acquisition_date = models.DateField(null=True, blank=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    # Código QR del ejemplar (usado para etiquetado físico)
    qr_image = models.ImageField(upload_to="qrcodes/", null=True, blank=True)
    
    def __str__(self):
        return f"{self.barcode} - {self.record.title}"

    def generate_qr(self, data: str) -> None:
        """Genera un PNG de código QR a partir de `data` y lo guarda en `qr_image`.

        Usamos la librería `qrcode` para generar la imagen en memoria y
        luego la asignamos al campo `qr_image` sin hacer save() del modelo
        para que el workflow de save() del modelo controle la persistencia.
        """
        try:
            # Importar localmente para evitar error de import si la dependencia
            # no está instalada en el entorno de análisis estático.
            import qrcode

            qr = qrcode.QRCode(box_size=6, border=2)
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            bio = io.BytesIO()
            img.save(bio, format="PNG")
            bio.seek(0)

            filename = f"{self.barcode}_qr.png"
            self.qr_image.save(filename, ContentFile(bio.read()), save=False)
        except Exception:
            # No queremos romper el guardado por un fallo en la generación de QR.
            pass

    def save(self, *args, **kwargs):
        """Override para generar QR automáticamente tras el primer guardado.

        Se guarda la instancia primero para asegurar que tiene PK y luego,
        si no existe `qr_image`, se genera y se guarda sólo ese campo.
        """
        # Guardar primero la instancia normal
        super().save(*args, **kwargs)

        # Si no existe imagen QR y hay barcode y record, generarla
        if not self.qr_image and self.barcode and self.record:
            payload = f"barcode:{self.barcode}|record:{self.record.pk}|title:{self.record.title}"
            self.generate_qr(payload)
            # Guardar sólo el campo qr_image para evitar tocar otros campos
            try:
                super().save(update_fields=["qr_image"])
            except Exception:
                # En caso de fallo, intentamos un save completo
                try:
                    super().save()
                except Exception:
                    pass


class Book(models.Model):
    title = models.CharField(max_length=512)
    authors = models.CharField(
        max_length=512,
        help_text="Formato sugerido: 'Apellido, Nombre; Apellido2, Nombre2'"
    )
    pub_year = models.PositiveIntegerField(null=True, blank=True)
    subjects_input = models.TextField(
        blank=True,
        help_text="Temas separados por ';' (ej. 'Educación; Metodología de la investigación')"
    )

    cutter1 = models.CharField(max_length=16, blank=True)
    cutter2 = models.CharField(max_length=16, blank=True)
    call_lcc = models.CharField(max_length=64, blank=True, unique=False)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title
