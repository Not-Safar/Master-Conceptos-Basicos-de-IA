import re
import unicodedata


def normalize(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text.lower())
                   if unicodedata.category(c) != "Mn")


def contents_text(text: str) -> bool:
    normalized = normalize(text)
    heading = re.search(r"(?:^|\n)\s*(?:\d+\s+)?(?:indice|tabla de contenidos|tabla de contenido)\b", normalized)
    entries = re.findall(r"\b\d{1,3}\.\s*[^.\d\s]", normalized)
    # Los PDF suelen separar el indice en varias paginas sin repetir su encabezado.
    return bool(heading or (len(entries) >= 3 and re.search(r"\.{3,}", text)))


def positional_question(question: str) -> str | None:
    normalized = normalize(question)
    if not re.search(r"\b(?:cuento|capitulo|seccion|tema|articulo)s?\b", normalized):
        return None
    if re.search(r"\b(?:primer|primero|primera)\b", normalized):
        return "first"
    if re.search(r"\b(?:ultimo|ultima)\b", normalized):
        return "last"
    return None


def page_count_question(question: str) -> bool:
    normalized = normalize(question)
    if not re.search(r"\b(?:cuantas|numero de|total de|cantidad de)\s+(?:paginas|hojas)\b", normalized):
        return False
    if re.search(r"\b(?:dedica\w*|ocupa\w*|corresponde\w*|desde|hasta)\b", normalized):
        return False
    # El cuento puede identificar el archivo sin ser el objeto del recuento:
    # «¿Cuántas páginas tiene el archivo donde está el primer cuento?».
    if re.search(r"\b(?:tiene|contiene|hay en)\s+(?:(?:el|este|ese|un)\s+)?(?:archivo|pdf|documento)\b", normalized):
        return True
    return not bool(re.search(r"\b(?:cuento|capitulo|seccion)s?\b", normalized))
