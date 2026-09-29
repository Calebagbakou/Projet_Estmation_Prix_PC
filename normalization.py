import re
import unicodedata


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _ascii(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def normalize_brand(value: str) -> str:
    text = clean_text(value)
    lowered = _ascii(text)
    brands = {
        "asus": "Asus",
        "dell": "Dell",
        "hp": "HP",
        "hewlett packard": "HP",
        "lenovo": "Lenovo",
        "acer": "Acer",
        "apple": "Apple",
        "msi": "MSI",
        " microsoft": "Microsoft",
    }
    return next((brand for name, brand in brands.items() if name.strip() in lowered), "Autre")


def normalize_processor(value: str) -> str:
    text = _ascii(clean_text(value))
    match = re.search(r"(?:intel\s*)?core[\s-]*i([3579])\b", text)
    if match:
        return f"Core i{match.group(1)}"
    match = re.search(r"core[\s-]*ultra[\s-]*([3579])\b", text)
    if match:
        return f"Core Ultra {match.group(1)}"
    match = re.search(r"(?:amd\s*)?ryzen[\s-]*(?:pro[\s-]*)?([3579])\b", text)
    if match:
        return f"Ryzen {match.group(1)}"
    match = re.search(r"(?:amd\s*)?e[\s-]*(\d+)\b", text)
    if match:
        return f"AMD E{match.group(1)}"
    match = re.search(r"(?:apple\s*)?m([1-4])\b", text)
    if match:
        return f"Apple M{match.group(1)}"
    return "Autre"


def normalize_generation(value: str) -> str:
    text = _ascii(clean_text(value))
    if "non precise" in text or "inconnu" in text:
        return "Non Précisé"
    match = re.search(r"\b(\d{1,2})(?:eme|e|th|st|nd|rd)?\b", text)
    return f"{match.group(1)}eme" if match else "Non Précisé"


def normalize_gpu(value: str) -> str:
    text = _ascii(clean_text(value))
    if "rtx" in text:
        return "NVIDIA GeForce RTX"
    if "gtx" in text or "quadro" in text:
        return "NVIDIA GeForce GTX"
    if "nvidia" in text:
        return "NVIDIA"
    if "iris" in text:
        return "Intel Iris"
    if "uhd" in text or "intel" in text:
        return "Intel UHD"
    if "radeon" in text or "amd" in text:
        return "AMD Radeon"
    if "apple" in text:
        return "Apple GPU"
    return "Autre"


def normalize_screen(value: str) -> str:
    text = clean_text(value).replace(",", ".")
    match = re.search(r"\d+(?:\.\d+)?", text)
    return f'{match.group(0)}"' if match else "Non Précisé"


def normalize_condition(value: str) -> str:
    text = _ascii(clean_text(value))
    if "neuf" in text:
        return "Neuf"
    if "occasion" in text:
        return "Occasion"
    if "comme neuf" in text or "propre" in text:
        return "Comme neuf"
    if "non precise" in text or "inconnu" in text:
        return "Non Précisé"
    return "Autre"


def normalize_title(value: str) -> str:
    return clean_text(value) if clean_text(value) else "Modèle non précisé"
