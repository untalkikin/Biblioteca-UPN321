from django.contrib import admin
from .models import BibliographicRecord, Item, Subject, Publisher, Location, Person, RecordContributor


class RecordContributorInline(admin.TabularInline):
    """Inline para editar los contribuyentes (autores, editores) desde
    la página de edición del registro bibliográfico.
    """
    model = RecordContributor
    extra = 1


@admin.register(BibliographicRecord)
class BibliographicRecordAdmin(admin.ModelAdmin):
    """Configuración del admin para `BibliographicRecord`.

    Muestra campos útiles en la lista de administradores y permite buscar
    por identificadores y relaciones (autores, materias).
    """
    list_display = ("title", "publish_year", "call_number", "publisher")
    search_fields = ("title", "isbn", "issn", "lccn", "call_number", "contributors__person__full_name", "subjects__term")
    list_filter = ("resource_type", "publish_year", "publisher")
    inlines = [RecordContributorInline]
    filter_horizontal = ("subjects",)


# Registra modelos auxiliares con la configuración por defecto del admin.
admin.site.register([Item, Subject, Publisher, Location, Person])
