"""Reject a model hint that gives the answer away.

A hint leaks when it contains the value of the correct option (in any of its usual
spellings), the correct letter written as an option ("C)", "(C)", "option C", "opció C",
"opción C"), or a phrase that announces the answer ("the answer is", "la resposta és",
"la respuesta es"). The check is deliberately strict: a false rejection costs one retry,
a missed leak costs the student the problem.

    leak_reason(hint, "C", {"A": "12", ..., "C": "18"})  -> None | "value:18" | "letter" | "phrase:..."
    leaks(hint, label, options) -> bool
"""
import re
import unicodedata

# Vulgar fractions and their decimal values
_VULGAR = {"½": 0.5, "⅓": 1 / 3, "⅔": 2 / 3, "¼": 0.25, "¾": 0.75, "⅕": 0.2, "⅖": 0.4, "⅗": 0.6,
           "⅘": 0.8, "⅙": 1 / 6, "⅚": 5 / 6, "⅛": 0.125, "⅜": 0.375, "⅝": 0.625, "⅞": 0.875}
_VULGAR_OF = {round(v, 4): ch for ch, v in _VULGAR.items()}

# Number words a hint might use instead of digits (Catalan, English, Spanish), 0..20 and tens
_WORDS = {
    0: ["zero", "cero"], 1: ["un", "una", "u", "one", "uno"], 2: ["dos", "dues", "two"],
    3: ["tres", "three"], 4: ["quatre", "four", "cuatro"], 5: ["cinc", "five", "cinco"],
    6: ["sis", "six", "seis"], 7: ["set", "seven", "siete"], 8: ["vuit", "eight", "ocho"],
    9: ["nou", "nine", "nueve"], 10: ["deu", "ten", "diez"], 11: ["onze", "eleven", "once"],
    12: ["dotze", "twelve", "doce"], 13: ["tretze", "thirteen", "trece"],
    14: ["catorze", "fourteen", "catorce"], 15: ["quinze", "fifteen", "quince"],
    16: ["setze", "sixteen", "dieciséis", "dieciseis"], 17: ["disset", "seventeen", "diecisiete"],
    18: ["divuit", "eighteen", "dieciocho"], 19: ["dinou", "nineteen", "diecinueve"],
    20: ["vint", "twenty", "veinte"], 30: ["trenta", "thirty", "treinta"],
    40: ["quaranta", "forty", "cuarenta"], 50: ["cinquanta", "fifty", "cincuenta"],
    60: ["seixanta", "sixty", "sesenta"], 70: ["setanta", "seventy", "setenta"],
    80: ["vuitanta", "eighty", "ochenta"], 90: ["noranta", "ninety", "noventa"],
    100: ["cent", "hundred", "cien", "ciento"], 1000: ["mil", "thousand"],
}
# "one" and "a" are too common in English to count as the number 1; "set" (7 in Catalan) is kept
_WORDS[1] = ["un", "una", "uno"]

_PHRASES = [
    r"the (?:correct |right )?(?:answer|solution|option|result) is",
    r"(?:correct|right) (?:answer|option) is",
    r"the answer (?:is|must be|has to be|would be)",
    r"la (?:resposta|solució|opció) (?:correcta )?(?:és|es|seria|ha de ser)",
    r"la (?:respuesta|solución|opción) (?:correcta )?(?:es|sería|debe ser|tiene que ser)",
    r"l'opció correcta",
    r"opció correcta és", r"opción correcta es", r"correct option is",
    r"resposta correcta és", r"respuesta correcta es",
    r"(?:tria|escull|marca|choose|pick|select|elige|marca) (?:la |the |l')?(?:opció|opción|option|lletra|letter|letra)?\s*[A-E]\b",
]
_PHRASE_RE = re.compile("|".join(f"(?:{p})" for p in _PHRASES), re.IGNORECASE)

_UNITS = r"(?:cm²|cm2|m²|m2|km²|km2|mm|cm|km|dm|m|kg|g|l|ml|€|\$|%|º|°|graus|degrees|grados|min|h|s|hores|hours|anys|years|euros)"


def _fold(text):
    """Lowercase, strip accents, collapse whitespace."""
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text.lower()).strip()


def _numbers_in(value):
    """Numeric readings of an option value: '1/2' -> 0.5; '18 cm²' -> 18; '1,5' -> 1.5."""
    found = set()
    text = str(value)
    for ch, v in _VULGAR.items():
        if ch in text:
            found.add(round(v, 4))
    plain = unicodedata.normalize("NFKC", text)
    for m in re.finditer(r"(\d+)\s*/\s*(\d+)", plain):
        if int(m.group(2)):
            found.add(round(int(m.group(1)) / int(m.group(2)), 4))
    # a digit right after a letter belongs to the unit ("27cm2", "4cm²2" from the OCR), it is not a number
    for m in re.finditer(r"(?<![A-Za-z\d.,])\d+(?:[.,]\d+)?", plain):
        found.add(round(float(m.group(0).replace(",", ".")), 4))
    return found


def _spellings(number):
    """Every way a hint could write this number: 18, 18.0, 18,0, 0.5, 0,5, 1/2, ½, 'divuit'."""
    out = set()
    if number == int(number):
        n = int(number)
        out.update({str(n), f"{n}.0", f"{n},0"})
        out.update(_WORDS.get(n, []))
    else:
        s = f"{number:.4f}".rstrip("0")
        out.update({s, s.replace(".", ","), s.lstrip("0"), s.replace(".", ",").lstrip("0")})
        if number in _VULGAR_OF:
            out.add(_VULGAR_OF[number])
        for den in range(2, 13):  # the fraction with a small denominator, if any
            num = number * den
            if abs(num - round(num)) < 1e-6:
                out.add(f"{int(round(num))}/{den}")
                break
    return out


def _core(value):
    """The option text without units, e.g. '36 cm²' -> '36', 'x = 4' -> 'x = 4'."""
    text = _fold(value)
    text = re.sub(rf"(?<=\d)\s*{_UNITS}\d*\b", "", text)  # "27 cm²", "27cm2", "4cm²2" (OCR noise) -> the value
    return text.strip(" .")


def _contains_token(haystack, needle):
    """needle appears in haystack as a whole token (18 does not match 180 or 118)."""
    if not needle:
        return False
    # a number may be glued to its unit in the hint too ("27cm"), but 18 never matches 180 or 18.5
    after = r"(?![\d/]|[.,]\d)" if needle[-1].isdigit() else r"(?![\w/]|[.,]\d)"
    pattern = r"(?<![\w/.,])" + re.escape(needle) + after
    return re.search(pattern, haystack) is not None


def leak_reason(hint, label, options):
    """None when the hint is safe, otherwise a short reason: 'value:18', 'letter', 'phrase:...'."""
    if not hint or not str(hint).strip():
        return "empty"
    folded = _fold(hint)
    value = (options or {}).get(label)

    # 1. Announcing phrases
    m = _PHRASE_RE.search(hint)
    if m:
        return "phrase:" + m.group(0)

    # 2. The letter as an option: "C)", "(C)", "option C", "opció C", "opción C", "letter C", "resposta: C"
    if label:
        letter = re.escape(label.upper())
        letter_patterns = [
            rf"\({letter}\)", rf"(?<![A-Za-z]){letter}\)",
            rf"\b(?:option|opcio|opcion|opció|opción|letter|lletra|letra|answer|resposta|respuesta|solucio|solució|solution)\s*(?:is|és|es|:)?\s*\(?{letter}\b",
            rf"\b(?:is|és|es)\s+{letter}(?=[\s.,;!?]|$)",
            rf"(?<![A-Za-z]){letter}(?:\.|$)\s*$",   # a bare "C." at the very end
        ]
        for p in letter_patterns:
            if re.search(p, hint.strip(), re.IGNORECASE if "option" in p else 0):
                return "letter"

    # 3. The value of the correct option
    if value not in (None, ""):
        core = _core(value)
        if _contains_token(folded, core):
            return f"value:{value}"
        for number in _numbers_in(value):
            for spelling in _spellings(number):
                if _contains_token(folded, _fold(spelling)):
                    return f"value:{value}"
    return None


def leaks(hint, label, options):
    return leak_reason(hint, label, options) is not None
