# catalog/views_inventory.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from .models import BibliographicRecord

@require_POST
def mark_seen(request):
    payload = json.loads(request.body)
    code = payload.get("code","")
    # code puede ser la URL o el inventory_code; parsea según tu get_qr_payload()
    inv = code.split("inv=")[-1] if "inv=" in code else code
    obj = BibliographicRecord.objects.filter(inventory_code=inv).first()
    if not obj:
        return JsonResponse({"ok": False, "msg": "No encontrado"}, status=404)
    # registra “visto”
    InventoryEvent.objects.create(record=obj, event="SEEN")
    return JsonResponse({"ok": True, "title": obj.title})
