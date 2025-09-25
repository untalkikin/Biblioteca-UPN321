# catalog/services/lcc.py
import re
from typing import Optional, Tuple

# ------------------ Configuración / Heurísticas ------------------
KEYWORDS_TO_CLASS = {
    # Educación y pedagogía
    "educación": "L",
    "pedagogía": "LB",
    "didáctica": "LB",
    "currículo": "LB",
    "docencia": "LB",
    "metodología de la investigación": "LB",
    "evaluación educativa": "LB",
    "psicopedagogía": "LB",

    # Ciencias sociales / psicología
    "psicología": "BF",
    "sociología": "HM",
    "antropología": "GN",

    # Computación / matemáticas
    "programación": "QA",
    "computación": "QA",
    "algoritmos": "QA",
    "matemáticas": "QA",
    "estadística": "QA",

    # Lengua y literatura / lingüística (¡clave para tu caso!)
    "gramática": "PC",          # Lenguas románicas (español = PC)
    "gramatical": "PC",
    "lingüística": "P",
    "filología": "P",
    "español": "PC",
    "castellano": "PC",
    "real academia española": "PC",
    "rae": "PC",

    # Historia / literatura (ya tenías)
    "historia": "D",
    "literatura": "P",
}

# QA 76.73 P98 D45 2023  (puntos en build_call_number)
LCC_REGEX = r"^([A-Z]{1,3})\s?(\d{1,4}(?:\.\d+)?)\s?([A-Z]\d+)?\s?([A-Z]\d+)?\s?(\d{4})?$"
SPACE_RE = re.compile(r"\s+")


# ------------------ Normalización básica ------------------
def normalize_lcc(code: Optional[str]) -> Optional[str]:
    """
    Normaliza espacios y mayúsculas. Mantiene formato "CLASE NUM CUTTER CUTTER2 AÑO".
    Los puntos ante cutters se agregan solo al render (build_call_number).
    """
    if not code:
        return code
    code = SPACE_RE.sub(" ", code.strip().upper())
    # Asegurar espacio entre letras y números iniciales
    code = re.sub(r"^([A-Z]{1,3})(\d)", r"\1 \2", code)
    # Compactar espacios múltiples
    code = re.sub(r"\s{2,}", " ", code)
    return code


# ------------------ Helpers de clasificación ------------------
# --- Asegúrate de que esta función devuelva 'Z' si no encuentra nada ---
def _class_letters_from_subjects(text: Optional[str]) -> str:
    text = (text or "").lower()
    for kw, clazz in KEYWORDS_TO_CLASS.items():
        if kw in text:
            return clazz
    return "Z"  # <--- Fallback: genera algo aunque no haya match

def _class_number_from_title(title: Optional[str]) -> str:
    """
    Genera un número base 100..999 a partir del título para dispersión.
    (Heurístico; puedes reemplazar por reglas reales de LCC si las implementas).
    """
    s = (title or "").strip()
    if not s:
        return "100"
    val = sum(ord(c) for c in s[:12])
    return str(100 + (val % 900))  # 100–999


def cutter_from_person_name(full_name: str) -> Optional[str]:
    """
    Cutter simple: inicial + dos dígitos pseudoestables. Placeholder de Cutter-Sanborn.
    """
    full_name = (full_name or "").strip()
    if not full_name:
        return None
    # Toma la primera letra del apellido principal si viene "Apellido, Nombre"
    letter = full_name.split(",")[0].strip()[:1].upper() or full_name[:1].upper()
    num = (abs(hash(full_name)) % 90) + 10  # 10..99
    return f"{letter}{num}"


def first_author_cutter(record) -> Optional[str]:
    """
    Si existe relación contributors(role='author'), usa la primera persona.
    No falla si no existe la relación.
    """
    try:
        rel = record.contributors.filter(role="author").select_related("person").first()
        if rel and getattr(rel, "person", None) and getattr(rel.person, "full_name", ""):
            return cutter_from_person_name(rel.person.full_name)
    except Exception:
        pass
    return None


def second_cutter_from_title(record) -> Optional[str]:
    """
    Usa la primera palabra significativa del título para un segundo cutter.
    """
    words = (record.title or "").split()
    for w in words:
        w = re.sub(r"[^\wÁÉÍÓÚÑáéíóúñ]", "", w, flags=re.UNICODE)
        if len(w) >= 3:
            letter = w[0].upper()
            num = (abs(hash(w)) % 90) + 10
            return f"{letter}{num}"
    return None


# --- Wrappers para compatibilidad con el código que te fallaba ---
def _author_cutter(text: Optional[str]) -> Optional[str]:
    """Compatibilidad: si te pasan texto (p.ej., título), genera un cutter simple."""
    return cutter_from_person_name(text or "")


# ------------------ Inferencia de clase (opcional) ------------------
def infer_class(record) -> Optional[str]:
    """
    Mantengo tu función, pero la hago segura para el primer save:
    - NO toca M2M si el objeto no tiene pk aún.
    """
    bits = [
        record.title or "",
        getattr(record, "subtitle", "") or "",
        getattr(record, "notes", "") or "",
        getattr(record, "series", "") or "",
        getattr(record, "publish_place", "") or "",
    ]

    # Solo toca subjects si ya existe pk
    try:
        if getattr(record, "pk", None):
            if hasattr(record, "subjects"):
                subs_text = "; ".join(record.subjects.values_list("term", flat=True))
                bits.append(subs_text)
    except Exception:
        pass

    text = " ".join(bits).lower()
    for kw, clazz in KEYWORDS_TO_CLASS.items():
        if kw in text:
            return clazz
    return None


# ------------------ API principal ------------------
def generate_lcc(record, subjects_text: Optional[str] = None) -> Tuple[Optional[str], str]:
    letters = _class_letters_from_subjects(subjects_text)

    if not letters or letters.strip() == "":
        safe_text = " ".join([
            getattr(record, "series", "") or "",
            getattr(record, "publish_place", "") or "",
            getattr(record, "notes", "") or "",
            getattr(record, "title", "") or "",
            getattr(record, "subtitle", "") or "",
        ])
        letters = _class_letters_from_subjects(safe_text) or "Z"   # <--- asegura fallback

    number = _class_number_from_title(getattr(record, "title", None))

    cutter1 = first_author_cutter(record)
    if not cutter1 and getattr(record, "publisher", None):
        pub_name = getattr(record.publisher, "name", None) or str(record.publisher)
        cutter1 = cutter_from_person_name(pub_name)
    if not cutter1:
        cutter1 = _author_cutter(getattr(record, "title", None))

    year = getattr(record, "publish_year", None)

    # Ya no devolvemos None: siempre habrá letters y number
    parts = [f"{letters} {number}"]
    if cutter1:
        parts.append(f"{cutter1}")
    if year:
        parts.append(str(year))
    return " ".join(parts), "heurística"



def split_lcc(code: str):
    """
    Devuelve dict con lcc_class, lcc_number, cutter, cutter2, year (str o None).
    Acepta variantes con/ sin espacios y sin puntos ante cutters.
    """
    code = normalize_lcc(code or "")
    m = re.match(LCC_REGEX, code)
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
    Render amigable de la signatura (con puntos en cutters).
    Ejemplos:
      QA 76.73 P98 2023 → “QA76.73 .P98 2023”
      LB 102.25 A12    → “LB102.25 .A12”
    """
    cls = (parts.get("lcc_class", "") or "").strip()
    num = (parts.get("lcc_number", "") or "").strip()
    c1 = (parts.get("cutter", "") or "").strip()
    c2 = (parts.get("cutter2", "") or "").strip()
    year = parts.get("year")

    head = f"{cls}{num}".strip()
    segs = [head]
    if c1: segs.append(f".{c1}")
    if c2: segs.append(f".{c2}")
    if year: segs.append(str(year))
    return " ".join([s for s in segs if s])


def build_sort_key(
    lcc_class: str,
    lcc_number: str,
    cutter: str,
    cutter2: str,
    year: Optional[str]
    ) -> Tuple[str, str]:
        """
        Devuelve (sort_key, number_sort) para ordenar correctamente por estantería:
        - sort_key: CLASE(3) | INT(4) | DEC(6) | C1(L+4) | C2(L+4) | AÑO(4)
        - number_sort: INT.DEC (útil para depurar)
        """
        # separa entero y decimal del número
        m = re.match(r"^(\d{1,4})(?:\.(\d+))?$", (lcc_number or "").strip())
        if m:
            n_int = m.group(1).zfill(4)
            n_dec = (m.group(2) or "").ljust(6, "0")
        else:
            n_int, n_dec = "0000", "000000"

        def _pack(c: str) -> str:
            if not c:
                return "_0000"
            m2 = re.match(r"^([A-Z])(\d+)$", c.upper())
            if not m2:
                return "_0000"
            return f"{m2.group(1)}{m2.group(2).zfill(4)}"

        c1 = _pack(cutter or "")
        c2 = _pack(cutter2 or "")
        y  = (year or "").zfill(4) if year else "0000"

        sort_key = f"{(lcc_class or '').ljust(3,'_')}|{n_int}|{n_dec}|{c1}|{c2}|{y}"
        number_sort = f"{n_int}.{n_dec}"
        return sort_key, number_sort
