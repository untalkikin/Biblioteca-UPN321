# catalog/signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Book
from .utils.classmarks import generate_call_lcc, normalize_word

def _next_collision_suffix(existing_codes: set[str], base: str) -> str:
    """
    Si 'base' ya existe, intenta base, base2, base3...
    """
    if base not in existing_codes:
        return base
    i = 2
    while True:
        cand = f"{base}{i}"
        if cand not in existing_codes:
            return cand
        i += 1

@receiver(pre_save, sender=Book)
def autogenerate_classmarks(sender, instance: "Book", **kwargs):
    # Si ya vienen llenos, respeta
    if all([instance.call_lcc, instance.cutter1, instance.cutter2]):
        return

    subjects_list = []
    # si usas ManyToMany Subjects, en pre_save aún no está disponible rel;
    # puedes usar 'subjects_input' de texto o un campo cacheado.
    if hasattr(instance, "subjects_input") and instance.subjects_input:
        subjects_list = [s.strip() for s in instance.subjects_input.split(";") if s.strip()]
    elif hasattr(instance, "subjects_cache") and instance.subjects_cache:
        subjects_list = instance.subjects_cache

    call, c1, c2 = generate_call_lcc(
        authors=instance.authors or "",
        title=instance.title or "",
        subjects=subjects_list,
        year=instance.pub_year
    )

    # Unicidad suave dentro del mismo prefijo: evita colisiones simples
    base_call = call
    if not instance.pk:
        siblings = sender.objects.filter(call_lcc__startswith=" ".join((call.split()[:1]))).values_list("call_lcc", flat=True)
        existing = set(siblings)
        call = _next_collision_suffix(existing, base_call)

    # Rellena solo si faltan
    instance.cutter1 = instance.cutter1 or c1
    instance.cutter2 = instance.cutter2 or c2
    instance.call_lcc = instance.call_lcc or call
