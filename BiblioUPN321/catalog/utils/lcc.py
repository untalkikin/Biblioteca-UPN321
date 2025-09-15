import re

LCC-RE = re.compile(
    r"""
    ^\s*
    (?P<class>[A-Z]{1,2})               # QA
    \s*
    (?P<number>\d{1,4}(\.\d+)?)?        # 76.73
    \s*
    (?P<cutter>\.[A-Z]\d+[A-Za-z0-9]*)? # .P98
    \s*
    (?P<cutter2>[A-Z]\d+[A-Za-z0-9]*)?  # D45 (a veces sin punto)
    \s*
    (?P<year>\d{4})?                    # 2021
    \s*$
    """,
    re.VERBOSE
)

def parse_lcc(call_number: str):
    if not call_number:
        return {}
    m = LCC_RE.match(call_number.strip())
    return m.groupdict() if m else {}



def normalize_lcc(call_number: str) -> str:
    """
    Intenta normalizar a formato: CCNNN.NN .C123 C45 YYYY (Cuando existen)
    """    
    
    g = parse_lcc(call_number)
    if not g:
        return call_number.strip()
    
    parts = []
    
    if g.get("class"): parts.append(g["class"])
    if g.get("number"): parts.append(g["number"])
    if g.get("cutter"): parts.append(g["cutter"])
    if g.get("cutter2"): parts.append(g["cutter2"])
    if g.get("year"): parts.append(g["year"])
    return " ".join(parts)
    