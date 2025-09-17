from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import BibliographicRecord, Item
from .forms import BibliographicRecordForm
from .permissions import cataloger_required


# Create your views here.
def record_list(request):
    q = request.GET.get("q","").strip()
    lcc = request.GET.get("lcc","").strip()
    resource_type = request.GET.get("type","").strip()
    
    qs = BibliographicRecord.objects.all()
    if q:    
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(subtitle__icontains=q) |
            Q(isbn__icontains=q) |
            Q(issn__icontains=q) |
            Q(subjects__term__icontains=q) |
            q(contributors__person__full_name__icontains=q)
        ).distinct()
    if lcc:
        qs = qs.filter(lcc_class__istartwith=lcc.upper())
    if resource_type:
        qs = qs.filter(resource_type=resource_type)
    
    paginator = Paginator(qs.select_related("publisher"), 20)
    page = request.GET.get("page")
    records = paginator.get_page(page)
    return render(request, "catalog/record_list.html", {"records":records, "q":q, "lcc": lcc, "type": resource_type})

def record_detail(request, pk):
    record = get_object_or_404(BibliographicRecord.objects.sele_related("publisher"), pk=pk)
    return render(request, "catalog/record_detail.html", {"record": record})

@login_required
@cataloger_required
def record_create(request):
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
    rec = get_object_or_404(BibliographicRecord, pk=pk)
    if request.method == "POST":
        form = BibliographicRecordForm(request.POST, request.FILES, instance=rec)
        if form.is_valid():
            rec = form.save()
            return redirect("catalog:record_detail", pk=rec.pk)
    else:
        form = BibliographicRecordForm(instance=rec)
    return render(request, "catalog/record_form.html", {"form": form, "mode": "edit", "record": rec})
    