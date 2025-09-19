# catalog/utils/classmarks.py
import re
import unicodedata

# ---- 1) Normalización básica ----
ARTICLES = {"el","la","los","las","un","una","unos","unas","the","a","an"}
def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def normalize_word(s: str) -> str:
    s = _strip_accents(s or "").lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def title_key(title: str) -> str:
    t = normalize_word(title)
    parts = t.split()
    if parts and parts[0] in ARTICLES:
        parts = parts[1:]
    return parts[0] if parts else ""

def primary_author_lastname(authors_field: str) -> str:
    """
    Espera 'Apellido, Nombre; Apellido2, Nombre2' o variantes.
    Toma el primer autor y su primer apellido/token significativo.
    """
    if not authors_field:
        return ""
    first = authors_field.split(";")[0]
    # formatos comunes: "García Márquez, Gabriel" | "Gabriel García Márquez"
    if "," in first:
        last = first.split(",")[0]
    else:
        last = first.strip().split()[-1]
    return normalize_word(last)

# ---- 2) Cutter aproximado (estilo Sanborn simplificado) ----
# Tabla simple y estable para 2ª/3ª letra (no perfecta, pero práctica y consistente)
LETTER_MAP = {
    'a': 11, 'b': 12, 'c': 13, 'd': 14, 'e': 15, 'f': 16, 'g': 17, 'h': 18,
    'i': 19, 'j': 21, 'k': 22, 'l': 23, 'm': 24, 'n': 25, 'o': 26, 'p': 27,
    'q': 28, 'r': 29, 's': 31, 't': 32, 'u': 33, 'v': 34, 'w': 35, 'x': 36,
    'y': 37, 'z': 38
}

def cutter_for(word: str, width: int = 3) -> str:
    """
    Genera '.Xnnn' donde X es la primera letra y nnn deriva de siguientes letras.
    Ej.: 'garcia' -> '.G216', 'maria' -> '.M115'
    """
    w = normalize_word(word)
    if not w:
        return ""
    first = w[0].upper()
    nums = []
    for ch in w[1:1+width]:
        nums.append(LETTER_MAP.get(ch, 30))  # default 30 para letras raras/vacíos
    # Compactar a 2-3 dígitos reproducibles
    if not nums:
        code = "1"
    else:
        # Toma dos primeros mapeos y forma un número de 2-3 dígitos estable
        code = "".join(str(n % 10) for n in nums[:3])  # solo últimas cifras para estabilidad
        code = code.lstrip("0") or "1"
    return f".{first}{code}"

# ---- 3) Prefijos LCC internos por materia (ajústalo a tu acervo UPN321) ----
SUBJECT_TO_LCC = {
    # Educación y pedagogía
    "educacion": "L", "pedagogia": "LB", "didactica": "LB", "evaluacion educativa": "LB",
    # Psicología y educación especial
    "psicologia": "BF", "neuroeducacion": "BF", "educacion especial": "LC",
    # Computación y matemáticas
    "computacion": "QA76", "informatica": "QA76", "programacion": "QA76.6", "matematicas": "QA",
    # Ciencias sociales / Metodología
    "metodologia de la investigacion": "H62", "sociologia": "HM", "economia": "HB",
    # Lengua y literatura
    "literatura": "PN", "literatura hispanoamericana": "PQ", "linguistica": "P",
    # Historia México / América
    "historia de mexico": "F1219", "historia de america latina": "F1401",
}

def lcc_prefix_from_subjects(subjects: list[str]) -> str:
    """
    Busca el primer match en SUBJECT_TO_LCC (case/acentos insensibles).
    Si no encuentra, devuelve 'Z' (ciencia de la información/bibliografía) como comodín.
    """
    for s in subjects or []:
        key = normalize_word(s)
        for k, code in SUBJECT_TO_LCC.items():
            if k in key:
                return code
    return "Z"  # comodín/por revisar

# ---- 4) Generador principal ----
def generate_call_lcc(authors: str, title: str, subjects: list[str], year: int | str | None):
    last = primary_author_lastname(authors)
    c1 = cutter_for(last) if last else ""
    tk = title_key(title)
    c2 = cutter_for(tk) if tk else ""
    prefix = lcc_prefix_from_subjects(subjects)
    y = str(year) if (year and str(year).isdigit()) else ""
    # call number estilo: "QA76 .G216 .C55 2025" (sin puntos extra)
    call = " ".join(filter(None, [prefix, c1, c2, y]))
    return call, c1, c2
