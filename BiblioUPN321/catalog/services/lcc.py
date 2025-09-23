# catalog/services/lcc.py
# -*- coding: utf-8 -*-
import re
from typing import Optional, Tuple

KEYWORDS_TO_CLASS = {
    # Educación y pedagogía (UPN ♥)
    "educación": "L",
    "pedagogía": "LB",
    "didáctica": "LB",
    "currículo": "LB",
    "docencia": "LB",
    "metodología de la investigación": "LB",
    "evaluación educativa": "LB",
    "psicopedagogía": "LB",
    # Ciencias sociales / psicología (muy presentes en UPN)
    "psicología": "BF",
    "sociología": "HM",
    "antropología": "GN",
    # Computación / matemáticas
    "programación": "QA",
    "computación": "QA",
    "algoritmos": "QA",
    "matemáticas": "QA",
    "estadística": "QA",
    # Historia / literatura (ejemplos)
    "historia": "D",
    "literatura": "P",
}

LCC_REGEX = r"^([A-Z]{1,3})\s?(\d{1,4}(?:\.\d+)?)\s?([A-Z]\d+)?\s?([A-Z]\d+)?\s?(\d{4})?$"
SPACE_RE = re.compile(r"\s+")

def normalize_lcc(code: Optional[str]) -> Optional[str]:
    if not code:
        return code
    code = SPACE_RE.sub(" ", code.strip().upper())
    # Asegurar espacio entre letras y números iniciales
    code = re.sub(r"^([A-Z]{1,3})(\d)", r"\1 \2", code)
    # Compactar espacios
    code = re.sub(r"\s{2,}", " ", code)
    return code

def infer_class(record) -> Optional[str]:
    text = " ".join([
        record.title or "",
        record.subtitle or "",
        getattr(record, "notes", "") or "",
        getattr(record, "series", "") or "",
        getattr(record, "publish_place", "") or "",
        # incluir subjects (M2M)
        "; ".join(getattr(record, "subjects", []).values_list("term", flat=True)) if hasattr(record, "subjects") else ""
    ]).lower()
    for kw, clazz in KEYWORDS_TO_CLASS.items():
        if kw in text:
            return clazz
    return None

def cutter_from_person_name(full_name: str) -> Optional[str]:
    full_name = (full_name or "").strip()
    if not full_name:
        return None
    # Toma la primera letra del apellido “principal”
    # y un número pseudoestable (placeholder). Sustituir por Cutter-Sanborn si lo agregas.
    letter = full_name.split(",")[0].strip()[:1].upper() or full_name[:1].upper()
    num = (abs(hash(full_name)) % 90) + 10  # 10..99
    return f"{letter}{num}"

def first_author_cutter(record) -> Optional[str]:
    # Record.contributors → usa el primer AUTHOR si existe
    try:
        author_rel = record.contributors.filter(role="author").select_related("person").first()
        if author_rel and author_rel.person and author_rel.person.full_name:
            return cutter_from_person_name(author_rel.person.full_name)
    except Exception:
        pass
    return None

def second_cutter_from_title(record) -> Optional[str]:
    # Usa la primera palabra “significativa” del título para cutter2
    words = (record.title or "").split()
    for w in words:
        w = re.sub(r"[^\wÁÉÍÓÚÑáéíóúñ]", "", w, flags=re.UNICODE)
        if len(w) >= 3:
            letter = w[0].upper()
            num = (abs(hash(w)) % 90) + 10
            return f"{letter}{num}"
    return None

def generate_lcc(record) -> Tuple[Optional[str], Optional[str]]:
    base = infer_class(record)
    if not base:
        return None, None

    # Número de clase: placeholder básico (mejorable por tabla real)
    # Si hay año, cuélgalo como decimal: LB 102.25 para 2025
    year = record.publish_year
    class_num = None
    if year:
        class_num = f"102.{int(year) % 100:02d}" if base in ("L","LB") else f"76.{int(year) % 100:02d}"
    else:
        # Si no hay año, usa longitud del título (placeholder)
        class_num = f"1.{len((record.title or '').split()):02d}"

    c1 = first_author_cutter(record) or second_cutter_from_title(record)
    c2 = None  # opcional

    parts = [base, class_num]
    if c1: parts.append(c1)
    if year: parts.append(str(year))
    code = " ".join(parts)
    return code, "heurística"

def split_lcc(code: str):
    """
    Devuelve dict con lcc_class, lcc_number, cutter, cutter2, year (str o None).
    """
    m = re.match(LCC_REGEX, code or "")
    if not m:
        return {"lcc_class": "", "lcc_number": "", "cutter": "", "cutter2": "", "year": None}
    lcc_class, lcc_number, c1, c2, year = m.groups()
    return {
        "lcc_class": lcc_class or "",
        "lcc_number": lcc_number or "",
        "cutter": c1 or "",
        "cutter2": c2 or "",
        "year": year
    }

def build_call_number(parts: dict) -> str:
    """
    QA 76.73 P98 2023 → “QA 76.73 .P98 2023”
    LB 102.25 A12 → “LB 102.25 .A12”
    """
    cls = parts.get("lcc_class", "")
    num = parts.get("lcc_number", "")
    c1 = parts.get("cutter", "")
    c2 = parts.get("cutter2", "")
    year = parts.get("year")

    segs = [f"{cls} {num}".strip()]
    if c1: segs.append(f".{c1}")
    if c2: segs.append(f".{c2}")
    if year: segs.append(str(year))
    return " ".join([s for s in segs if s])
