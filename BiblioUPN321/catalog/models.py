from django.db import models
from django.core.validators import RegexValidator 
from django.utils.translation import gettext_lazy as _

#Auxiliares para estructura
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
class Publisher(TimeStampedModel):
    name = models.CharField(max_lenght=255)
    place = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return self.name

class Subject(TimeStampedModel):
    term = models.CharField(max_length=255, unique=True)
    
    def __str__(self):
        return self.term
    
class Location(TimeStampedModel):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
class Person(TimeStampedModel):
    given = models.CharField(_("Nombres"), max_length=255, blank=True)
    family = models.CharField(_("Apellidos"), max_length=255, blank=True)
    full_name = models.CharField(max_length=255, unique=True)
    VIAF = models.CharField(max_length=50, blank=True)
    ORCID = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return self.full_name or f"{self.family}, {self.given}".strip(", ")
    
class BibliographicRecord(TimeStampedModel):
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
    publish_place = models.CharField(max_lenght=255, blank=True)
    isbn = models.CharField(max_length=32, blank=True)
    issn = models.CharField(max_length=32, blank=True)
    iccn = models.CharField(max_length=32, blank=True)
    
    # Signatura LCC completa: Pendiente la revison del codigo
    call_number = models.CharField(
        max_length=128, blank=True,
        help_text=_("Signatura LCC completa, ej: QA76.73.P98 D45 2021"),
    )
    
        # Campos opcionales para parseo/consulta:
    lcc_class = models.CharField(max_length=2, blank=True)      # ej: 'QA'
    lcc_number = models.CharField(max_length=16, blank=True)     # ej: '76.73'
    cutter = models.CharField(max_length=32, blank=True)         # ej: 'P98'
    cutter2 = models.CharField(max_length=32, blank=True)        # ej: 'D45'
    
    physical_description = models.CharField(max_length=255, blank=True)
    series = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    
    subjects = models.ManyToManyField(Subject, blank=True)
    cover = models.ImageField(upload_to='covers/', null=True, blank=True)
    
    class Meta:
        ordering = ["lcc_class", "lcc_number", "cutter", "title"]
        
    def __str__(self):
        return self.title
    
class RecordContributor(models.Model):
    class Role(models.TextChoices):
        AUTHOR = "author", _("Autor")
        EDITOR = "editor", _("Editor")
        TRANSLATOR = "translator", _("Traductor")
        COMPILER = "compiler", _("Compilador")
        
    record = models.ForeignKey(BibliographicRecord, on_delete=models.CASCADE, related_name="contributors")
    person =  models.ForeignKey(Person, on_delete=models.PROTECT)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.AUTHOR)
    
    class Meta:
        unique_together = ("record", "person", "role")
        
    def __str__(self):
        return f"{self.person} ({self.get_role_display()})"
    
class Item(TimeStampedModel):
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
    

