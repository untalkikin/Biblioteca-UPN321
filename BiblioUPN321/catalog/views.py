from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required, permission_required
from .models import BibliographicRecord, Item
from .forms import BibliographicRecordForm
from .permissions import cataloger_required


def record_list(request):
    """Lista de registros bibliográficos con filtros básicos.

    Parámetros GET soportados:
    - q: término de búsqueda libre (título, subtítulo, ISBN, ISSN, sujeto, autor)
    - lcc: filtro por clase LCC (ej. 'QA')
    - type: tipo de recurso (book, thesis, article, ...)

    Devuelve una página con hasta 20 resultados paginados.
    """
    q = request.GET.get("q", "").strip()
    lcc = request.GET.get("lcc", "").strip()
    resource_type = request.GET.get("type", "").strip()

    qs = BibliographicRecord.objects.all()

    if q:
        # Búsqueda simple por campos relevantes; usar `distinct()` por joins M2M
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(subtitle__icontains=q) |
            Q(isbn__icontains=q) |
            Q(issn__icontains=q) |
            Q(subjects__term__icontains=q) |
            Q(contributors__person__full_name__icontains=q)
        ).distinct()

    if lcc:
        # Filtrar por la clase LCC (comienza con), mayúsculas para normalizar
        qs = qs.filter(lcc_class__istartswith=lcc.upper())

    if resource_type:
        qs = qs.filter(resource_type=resource_type)

    # Seleccionamos la editorial en la misma consulta para evitar consultas extra
    paginator = Paginator(qs.select_related("publisher"), 20)
    page = request.GET.get("page")
    records = paginator.get_page(page)
    return render(request, "catalog/record_list.html", {"records": records, "q": q, "lcc": lcc, "type": resource_type})


def record_detail(request, pk):
    """Detalle de un registro bibliográfico.

    Usa `select_related('publisher')` para optimizar la obtención de la
    relación con la editorial.
    """
    record = get_object_or_404(BibliographicRecord.objects.select_related("publisher"), pk=pk)

    # Calcular resúmenes de existencias para mostrar en la plantilla.
    items_qs = record.items.all()
    total_items = items_qs.count()
    available_count = items_qs.filter(status=Item.Status.AVAILABLE).count()
    loaned_count = items_qs.filter(status=Item.Status.LOANED).count()
    repair_count = items_qs.filter(status=Item.Status.REPAIR).count()
    lost_count = items_qs.filter(status=Item.Status.LOST).count()

    context = {
        "record": record,
        "total_items": total_items,
        "available_count": available_count,
        "loaned_count": loaned_count,
        "repair_count": repair_count,
        "lost_count": lost_count,
    }
    return render(request, "catalog/record_detail.html", context)


@login_required
@permission_required('catalog.add_bibliographicrecord', raise_exception=True)
def record_create(request):
    """Crear un nuevo `BibliographicRecord` desde un formulario.

    Requiere autenticación y que el usuario tenga permisos de catalogador.
    Al crear, redirige a la vista de detalle del registro.
    """
    if request.method == "POST":
        form = BibliographicRecordForm(request.POST, request.FILES)
        if form.is_valid():
            rec = form.save()
            return redirect("catalog:record_detail", pk=rec.pk)
    else:
        form = BibliographicRecordForm()
    return render(request, "catalog/record_form.html", {"form": form, "mode": "create"})


@login_required
@cataloger_required
def record_update(request, pk):
    """Editar un registro existente.

    Permisos iguales a `record_create`. Carga la instancia y procesa
    el formulario para actualizar los campos.
    """
    rec = get_object_or_404(BibliographicRecord, pk=pk)
    if request.method == "POST":
        form = BibliographicRecordForm(request.POST, request.FILES, instance=rec)
        if form.is_valid():
            rec = form.save()
            return redirect("catalog:record_detail", pk=rec.pk)
    else:
        form = BibliographicRecordForm(instance=rec)
    return render(request, "catalog/record_form.html", {"form": form, "mode": "edit", "record": rec})
    