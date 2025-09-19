from django.db import models
from django.core.validators import RegexValidator 
from django.utils.translation import gettext_lazy as _


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
    isbn = models.CharField(max_length=32, blank=True)
    issn = models.CharField(max_length=32, blank=True)
    iccn = models.CharField(max_length=32, blank=True)
    
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
    
    class Meta:
        # Orden por signatura LCC y título como fallback
        ordering = ["lcc_class", "lcc_number", "cutter", "title"]
        
    def __str__(self):
        return self.title
    

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
    
    def __str__(self):
        return f"{self.barcode} - {self.record.title}"


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
