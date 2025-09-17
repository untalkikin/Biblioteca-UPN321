from django.contrib import admin
from .models import BibliographicRecord, Item, Subject, Publisher, Location, Person, RecordContributor

class RecordContributorInline(admin.TabularInline):
    model = RecordContributor
    extra = 1

@admin.register(BibliographicRecord)
class BibliographicRecordAdmin(admin.ModelAdmin):
    list_display = ("title","publish_year","call_number","publisher")
    search_fields = ("title","isbn","issn","lccn","call_number","contributors__person__full_name","subjects__term")
    list_filter = ("resource_type","publish_year","publisher")
    inlines = [RecordContributorInline]
    filter_horizontal = ("subjects",)

admin.site.register([Item, Subject, Publisher, Location, Person])
