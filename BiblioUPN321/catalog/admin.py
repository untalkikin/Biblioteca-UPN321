# catalog/admin.py
from django.contrib import admin
from .models import (
    BibliographicRecord, RecordContributor, Person, Subject,
    Publisher, Location, Item
)

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
    list_display = ("title", "lcc_code", "lcc_class", "lcc_number", "cutter", "publish_year")
    list_filter = ("resource_type", "lcc_class", "publish_year")
    search_fields = ("title", "subtitle", "lcc_code", "call_number")
    readonly_fields = ("lcc_code", "lcc_source", "call_number", "lcc_class", "lcc_number")
    inlines = [RecordContributorInline]

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
