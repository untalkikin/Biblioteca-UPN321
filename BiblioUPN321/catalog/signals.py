from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import BibliographicRecord
from .utils.lcc import parse_lcc, normalize_lcc

@receiver(pre_save, sender=BibliographicRecord)
def fill_lcc_parts(sender, instance: BibliographicRecord, **kwargs):
    if instance.call_number_lcc:
        instance.call_number = normalize_lcc(instance.call_number)
        parts = parse_lcc(instance.call_number)
        instance.lcc_class = parts.get("class") or ""
        instance.lcc_number = parts.get("number") or ""
        instance.lcc_cutter = parts.get("cutter") or ""
        instance.cutter2 = parts.get("cutter2") or ""
        
        