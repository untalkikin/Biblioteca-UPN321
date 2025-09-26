import re
import unicodedata
from typing import Optional, Literal, Dict, List, Set, Tuple

# ------------------ Configuración / Heurísticas ------------------
# Nota: priorizamos subclases cuando existen (p.ej., LB sobre L; PC/PQ sobre P).
KEYWORDS_TO_CLASS: dict[str, str] = {
    # Educación (L)
    "educacion": "L",
    "historia de la educacion": "LA",
    "pedagogia": "LB",
    "didactica": "LB",
    "curriculo": "LB",
    "curricular": "LB",
    "docencia": "LB",
    "metodologia de la investigacion educativa": "LB",
    "evaluacion educativa": "LB",
    "psicopedagogia": "LB",
    "inclusion educativa": "LC",
    "educacion especial": "LC",
    "politicas educativas": "LC",
    "libro de texto": "LT",
    "libros de texto": "LT",

    # Filosofía / Psicología / Religión (B…)
    "filosofia": "B",
    "logica": "BC",
    "estetica": "BH",
    "etica": "BJ",
    "psicologia": "BF",
    "religion": "BL",
    "mitologia": "BL",
    "cristianismo": "BR",
    "teologia": "BT",

    # Ciencias sociales (H…)
    "ciencias sociales": "H",
    "estadistica": "HA",
    "economia": "HB",
    "teoria economica": "HB",
    "historia economica": "HC",
    "industria": "HD",
    "agricultura (economia)": "HD",
    "trabajo": "HD",
    "transporte": "HE",
    "comercio": "HF",
    "finanzas": "HG",
    "finanzas publicas": "HJ",
    "sociologia": "HM",
    "problemas sociales": "HN",
    "familia": "HQ",
    "genero": "HQ",
    "criminologia": "HV",

    # Ciencia política (J…)
    "ciencia politica": "JA",
    "teoria del estado": "JC",
    "administracion publica": "JF",
    "gobierno local": "JS",
    "migracion": "JV",
    "relaciones internacionales": "JZ",

    # Derecho (K…)
    "derecho": "K",
    "derecho internacional": "KZ",

    # Lengua y literatura (P…)
    "linguistica": "P",
    "filologia": "P",
    "gramatica": "PC",         # Lenguas románicas → español en PC
    "gramatical": "PC",
    "espanol": "PC",
    "castellano": "PC",
    "real academia espanola": "PC",
    "rae": "PC",
    "literatura": "PN",
    "periodismo": "PN",
    "teoria literaria": "PN",
    "literatura espanola": "PQ",
    "literatura francesa": "PQ",
    "literatura italiana": "PQ",
    "literatura portuguesa": "PQ",
    "literatura inglesa": "PR",
    "literatura estadounidense": "PS",
    "literaturas germánicas": "PT",

    # Geografía / Antropología (G…)
    "geografia": "G",
    "cartografia": "GA",
    "geografia fisica": "GB",
    "oceanografia": "GC",
    "medio ambiente": "GE",
    "ecologia humana": "GF",
    "antropologia": "GN",
    "folklore": "GR",
    "deportes": "GV",

    # Historia (D/E/F)
    "historia": "D",
    "historia de america": "E",
    "estados unidos (historia)": "E",
    "america latina (historia)": "F",

    # Ciencias (Q…)
    "ciencias": "Q",
    "matematicas": "QA",
    "programacion": "QA",
    "computacion": "QA",
    "informatica": "QA",
    "algoritmos": "QA",
    "estadistica (matematicas)": "QA",
    "astronomia": "QB",
    "fisica": "QC",
    "quimica": "QD",
    "geologia": "QE",
    "biologia": "QH",
    "botanica": "QK",
    "zoologia": "QL",
    "anatomia": "QM",
    "fisiologia": "QP",
    "microbiologia": "QR",

    # Medicina (R…)
    "medicina": "R",
    "salud publica": "RA",
    "patologia": "RB",
    "medicina interna": "RC",
    "cirugia": "RD",
    "pediatria": "RJ",
    "enfermeria": "RT",
    "farmacia": "RS",

    # Tecnología / Ingeniería (T…)
    "tecnologia": "T",
    "ingenieria": "TA",
    "ingenieria civil": "TA",
    "hidraulica": "TC",
    "ambiental (ingenieria)": "TD",
    "ferrocarriles": "TF",
    "puentes": "TG",
    "construccion": "TH",
    "mecanica": "TJ",
    "electrica": "TK",
    "electronica": "TK",
    "computadores (hardware)": "TK",
    "vehiculos": "TL",
    "mineria": "TN",
    "quimica industrial": "TP",
    "fotografia": "TR",
    "manufactura": "TS",
    "artesania": "TT",
    "hogar (economia domestica)": "TX",

    # Arte / Música (N/M)
    "arte": "N",
    "arquitectura": "NA",
    "escultura": "NB",
    "dibujo": "NC",
    "pintura": "ND",
    "grabado": "NE",
    "artes decorativas": "NK",
    "musica": "M",
    "literatura musical": "ML",
    "ensenanza de la musica": "MT",

    # Bibliotecología / Información (Z)
    "bibliotecologia": "Z",
    "bibliografia": "Z",
    "museologia": "AM",
    "servicios de informacion": "ZA",
}

# ------------------ Regex / Constantes ------------------
SPACE_RE = re.compile(r"\s+")
NON_WORD_DOT_RE = re.compile(r"[^\w\s\.]")  # conserva letras/números/espacios/puntos
LCC_LETTERS_NUM_RE = re.compile(r"^([A-Z]{1,3})(\d)")  # separa clase (letras) y números
MULTISPACE_RE = re.compile(r"\s{2,}")

# LCC: CLASE (1–3) + NÚMERO (1–4 con opcional .dec) + [Cutter] + [Cutter2] + [AÑO]
LCC_REGEX = re.compile(
    r"""
    ^\s*
    ([A-Z]{1,3})                # clase
    \s+
    (\d{1,4}(?:\.\d+)?)         # número (entero y opcional decimal)
    (?:\s+([A-Z]\d{1,4}))?      # cutter1 (sin punto)
    (?:\s+([A-Z]\d{1,4}))?      # cutter2 (sin punto)
    (?:\s+(\d{4}))?             # año
    \s*$
    """,
    re.VERBOSE,
)

# ------------------ Normalización ------------------
def _strip_diacritics(txt: str) -> str:
    """Remueve tildes/diacríticos conservando ASCII base."""
    norm = unicodedata.normalize("NFKD", txt)
    return "".join(ch for ch in norm if not unicodedata.combining(ch))

def normalize(value: Optional[str], mode: Literal["text", "lcc"] = "text") -> Optional[str]:
    """
    Normalizador unificado.
    - mode="text": minúsculas, sin tildes, reemplaza '_' y '-' por espacio,
      elimina signos (salvo '.'); colapsa espacios.
    - mode="lcc": mayúsculas, recorta, colapsa espacios, asegura espacio entre
      letras de la clase (1–3) y el primer dígito. Mantiene formato
      'CLASE NUM CUTTER CUTTER2 AÑO'. Los puntos de Cutter se agregan al render.
    """
    if value is None:
        return "" if mode == "text" else None

    if mode == "text":
        txt = value.lower()
        txt = _strip_diacritics(txt)
        txt = txt.replace("_", " ").replace("-", " ")
        txt = NON_WORD_DOT_RE.sub(" ", txt)
        txt = SPACE_RE.sub(" ", txt).strip()
        return txt

    # mode == "lcc"
    code = SPACE_RE.sub(" ", value.strip().upper())
    # Asegurar espacio entre letras iniciales (1–3) y primer número
    code = LCC_LETTERS_NUM_RE.sub(r"\1 \2", code)
    code = MULTISPACE_RE.sub(" ", code)
    return code

# --- Shims de compatibilidad (mantienen tu API anterior) ---
def normalize_lcc(code: Optional[str]) -> Optional[str]:
    """Compat: conserva la antigua API."""
    return normalize(code, mode="lcc")

def normalize_text(text: Optional[str]) -> str:
    """Compat: conserva la antigua API."""
    return normalize(text or "", mode="text") or ""

# ------------------ Helpers de clasificación ------------------
def _class_letters_from_subjects(text: Optional[str]) -> str:
    """Devuelve la clase (letras) a partir de keywords; fallback Z si no hay match."""
    text = (text or "").lower()
    for kw, clazz in KEYWORDS_TO_CLASS.items():
        if kw in text:
            return clazz
    return "Z"  # Fallback: al menos algo válido

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

# --- Wrapper para compatibilidad con firmas antiguas ---
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
        letters = _class_letters_from_subjects(safe_text) or "Z"   # asegura fallback

    number = _class_number_from_title(getattr(record, "title", None))

    cutter1 = first_author_cutter(record)
    if not cutter1 and getattr(record, "publisher", None):
        pub_name = getattr(record.publisher, "name", None) or str(record.publisher)
        cutter1 = cutter_from_person_name(pub_name)
    if not cutter1:
        cutter1 = _author_cutter(getattr(record, "title", None))

    year = getattr(record, "publish_year", None)

    # Siempre habrá letters y number
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
    code = normalize_lcc(code or "") or ""
    m = LCC_REGEX.match(code)
    if not m:
        return {"lcc_class": "", "lcc_number": "", "cutter": "", "cutter2": "", "year": None}
    lcc_class, lcc_number, c1, c2, year = m.groups()
    return {
        "lcc_class": lcc_class or "",
        "lcc_number": lcc_number or "",
        "cutter": c1 or "",
        "cutter2": c2 or "",
        "year": year,
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
    if c1:
        segs.append(f".{c1}")
    if c2:
        segs.append(f".{c2}")
    if year:
        segs.append(str(year))
    return " ".join([s for s in segs if s])

def build_sort_key(
    lcc_class: str,
    lcc_number: str,
    cutter: str,
    cutter2: str,
    year: Optional[str],
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
    y = (year or "").zfill(4) if year else "0000"

    sort_key = f"{(lcc_class or '').ljust(3,'_')}|{n_int}|{n_dec}|{c1}|{c2}|{y}"
    number_sort = f"{n_int}.{n_dec}"
    return sort_key, number_sort

# (Opcional) Exporta nombres públicos del módulo
__all__ = [
    "KEYWORDS_TO_CLASS",
    "normalize", "normalize_lcc", "normalize_text",
    "generate_lcc", "split_lcc", "build_call_number", "build_sort_key",
    "infer_class", "LCC_REGEX",
]
