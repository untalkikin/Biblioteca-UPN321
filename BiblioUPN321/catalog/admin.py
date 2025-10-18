from django.contrib import admin
from django.utils.html import format_html
from .models import (
    BibliographicRecord, RecordContributor, Person, Subject,
    Publisher, Location, Item
)

@admin.action(description="(Re)generar QR")
def regen_qr(modeladmin, request, queryset):
    for obj in queryset:
        obj.generate_qr()
        obj.save(update_fields=["qr_image"])

class RecordContributorInline(admin.TabularInline):
    model = RecordContributor
    extra = 0
    autocomplete_fields = ["person"]  # <- requiere PersonAdmin.search_fields

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("full_name", "family", "given", "VIAF", "ORCID")
    search_fields = (
        "full_name",
        "family",
        "given",
        "VIAF",
        "ORCID",
    )
    ordering = ("family", "given")

@admin.register(BibliographicRecord)
class BibliographicRecordAdmin(admin.ModelAdmin):
    list_display = ("title", "lcc_code", "lcc_class", "lcc_number", "cutter", "publish_year","inventory_code", "qr_thumb")
    list_filter = ("resource_type", "lcc_class", "publish_year")
    search_fields = ("title", "subtitle", "lcc_code", "call_number")
    readonly_fields = ("lcc_code", "lcc_source", "call_number", "lcc_class", "lcc_number")
    inlines = [RecordContributorInline]
    actions = [regen_qr]


    def save_model(self, request, obj, form, change):
        """Inject subjects text for first-save LCC generation.

        The admin saves the object before committing M2M relations. For new
        records we can look at the submitted `subjects` in the form (a
        queryset) and provide a temporary `_subjects_text` so that
        `BibliographicRecord.save()` can use it when generating LCC.
        """
        if not change and not getattr(obj, 'lcc_code', None):
            subjects = form.cleaned_data.get('subjects') if form and hasattr(form, 'cleaned_data') else None
            if subjects:
                try:
                    obj._subjects_text = " ".join([s.term for s in subjects])
                except Exception:
                    # Tolerante: no bloquear si form data es inesperada
                    pass

        super().save_model(request, obj, form, change)
        
    def qr_thumb(self, obj):
        if obj.qr_image:
            return format_html('<img src="{}" width="80" height="80" />', obj.qr_image.url)
        return "—"

# (Opcional, por comodidad)
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    search_fields = ("term",)

@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    search_fields = ("name", "place")

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    search_fields = ("code", "name")

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("barcode", "record", "location", "status")
    search_fields = ("barcode", "record__title")
    list_filter = ("status", "location")
