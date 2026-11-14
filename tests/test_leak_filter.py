"""copilot/leak_filter.py: a model hint must never give the answer away."""
import unittest

from copilot.leak_filter import leak_reason, leaks

OPTIONS = {"A": "12", "B": "15", "C": "18", "D": "20", "E": "24"}


class SafeHintsTest(unittest.TestCase):
    """Hints that must pass: they mention numbers from the problem, wrong options, or the letter in prose."""

    SAFE = [
        "Pensa en quantes pomes hi ha en total abans de treure'n cap.",
        "First count how many apples the bags hold in total.",
        "Hi ha 12 pomes en total, i després se'n mengen algunes.",   # 12 is a wrong option
        "Multiply 3 by 4 first, then subtract.",
        "Hi ha 180 pomes al magatzem.",      # 18 inside 180
        "Compta fins a 118 si cal.",         # 18 inside 118
        "Pensa en 1.8 i en 18.5 com a límits.",  # 18 as part of a decimal
        "A square has four equal sides.",    # label A: 'A' as an article
        "Angle C is the largest, so start there.",  # label C in prose, not as an option
        "Compta els casos d'un en un.",
        "Use 2 and 4 to count the ways.",
        "Half of the figure is shaded, compare it with the rest.",   # value 1/2 written as a word: allowed
        "El costat fa 9 cm; l'àrea és costat per costat.",            # 9 for an answer of 81
    ]

    def test_safe_hints_pass(self):
        for hint in self.SAFE:
            label = "A" if hint.startswith("A square") else "C"
            options = {"C": "81 cm²"} if "9 cm" in hint else ({"C": "1/2"} if "Half" in hint else OPTIONS)
            self.assertIsNone(leak_reason(hint, label, options), hint)


class ValueLeakTest(unittest.TestCase):
    def check(self, hint, label, options, prefix="value"):
        reason = leak_reason(hint, label, options)
        self.assertIsNotNone(reason, hint)
        self.assertTrue(reason.startswith(prefix), f"{hint!r}: {reason}")

    def test_plain_value(self):
        self.check("Hi ha 18 pomes.", "C", OPTIONS)
        self.check("Queden 18.", "C", OPTIONS)
        self.check("(18)", "C", OPTIONS)
        self.check("18", "C", OPTIONS)

    def test_number_words(self):
        self.check("Són divuit pomes.", "C", OPTIONS)
        self.check("There are eighteen apples.", "C", OPTIONS)
        self.check("Quedan dieciocho manzanas.", "C", OPTIONS)
        self.check("Resten nou cromos.", "C", {"C": "9"})

    def test_decimal_spellings(self):
        self.check("Think of 18.0 apples.", "C", OPTIONS)
        self.check("Pensa en 18,0 pomes.", "C", OPTIONS)
        self.check("It costs 1.5 euros.", "C", {"C": "1,5 €"})
        self.check("Costa 1,5 euros.", "C", {"C": "1.5"})

    def test_fractions(self):
        self.check("Pensa en ½ del total.", "C", {"C": "1/2"})
        self.check("Pensa en 0,5 del total.", "C", {"C": "1/2"})
        self.check("Pensa en 0.5 del total.", "C", {"C": "½"})
        self.check("Pensa en 1/2 del total.", "C", {"C": "0,5"})
        self.check("Two thirds, so 2/3 of it.", "C", {"C": "⅔"})
        self.check("És a dir, 3/4.", "C", {"C": "0.75"})

    def test_units(self):
        self.check("The area is 81.", "C", {"C": "81 cm²"})
        self.check("The area is 81 cm2.", "C", {"C": "81 cm²"})
        self.check("L'àrea fa 81 cm².", "C", {"C": "81"})
        self.check("Angle C is 60 degrees here.", "B", {"B": "60°"})
        self.check("It is 60°.", "B", {"B": "60"})
        self.check("Costa 25 €.", "D", {"D": "25 euros"})

    def test_spacing_and_case(self):
        self.check("Hi   ha  18   pomes", "C", OPTIONS)
        self.check("ÀREA: 81 CM²", "C", {"C": "81 cm²"})

    def test_text_values(self):
        self.check("Pensa en el nombre set.", "A", {"A": "set"})
        self.check("The shape is a hexagon.", "B", {"B": "hexagon"})
        self.check("Pensa en x = 4.", "C", {"C": "x = 4"})


class GluedUnitsTest(unittest.TestCase):
    """OCR often glues the unit to the value ("27cm2", "4cm²2"): the digits of the unit are not numbers."""

    def test_unit_digits_are_not_numbers(self):
        self.assertIsNone(leak_reason("Hi ha 2 peces iguals.", "C", {"C": "27cm2"}))
        self.assertIsNone(leak_reason("Compta 3 costats.", "C", {"C": "4cm²2"}))   # stray digit after the unit
        self.assertIsNone(leak_reason("Pensa en 2 i en 3.", "B", {"B": "165 cm²"}))

    def test_the_value_itself_still_leaks_with_or_without_its_unit(self):
        for hint in ["Fa 27 en total.", "Fa 27cm2.", "Mesura 27 cm².", "Són 27cm de costat."]:
            self.assertIsNotNone(leak_reason(hint, "C", {"C": "27cm2"}), hint)
        self.assertIsNotNone(leak_reason("El costat fa 4cm.", "C", {"C": "4cm²2"}))
        self.assertIsNone(leak_reason("Fa 270 en total.", "C", {"C": "27cm2"}))
        self.assertIsNone(leak_reason("Fa 27.5 en total.", "C", {"C": "27cm2"}))


class LetterLeakTest(unittest.TestCase):
    def check(self, hint, label="C"):
        reason = leak_reason(hint, label, OPTIONS)
        self.assertIsNotNone(reason, hint)
        self.assertIn(reason.split(":")[0], ("letter", "phrase"), f"{hint!r}: {reason}")

    def test_letter_as_option(self):
        for hint in ["Option C is right.", "Opció C.", "Opción C.", "(C)", "Suma i mira C)",
                     "Letter C fits.", "La lletra C.", "The answer: C", "Resposta: C",
                     "Try it, C.", "So it is C", "Per tant és C.", "Choose C", "Tria la C", "Pick C"]:
            self.check(hint)

    def test_other_letters(self):
        self.check("Option A is right.", "A")
        self.check("(E)", "E")
        self.check("Opció B", "B")
        self.assertIsNone(leak_reason("Option A is wrong, think again.", "C", OPTIONS))


class PhraseLeakTest(unittest.TestCase):
    def check(self, hint):
        reason = leak_reason(hint, "C", OPTIONS)
        self.assertIsNotNone(reason, hint)
        self.assertTrue(reason.startswith("phrase") or reason.startswith("letter"), f"{hint!r}: {reason}")

    def test_phrases(self):
        for hint in ["The answer is simple.", "The correct answer is to subtract.", "The solution is below.",
                     "La resposta és restar.", "La resposta correcta és la suma.", "La respuesta es restar.",
                     "La solución es sumar.", "L'opció correcta surt restant.", "The right answer is clear.",
                     "The answer must be a round number.", "Correct option is the largest."]:
            self.check(hint)


class EdgeCasesTest(unittest.TestCase):
    def test_empty_hint_is_rejected(self):
        self.assertEqual(leak_reason("", "C", OPTIONS), "empty")
        self.assertEqual(leak_reason("   ", "C", OPTIONS), "empty")

    def test_missing_options(self):
        self.assertIsNone(leak_reason("Count the cases.", "C", {}))
        self.assertIsNone(leak_reason("Count the cases.", "C", None))
        self.assertEqual(leak_reason("Opció C.", "C", {}), "letter")

    def test_leaks_is_boolean(self):
        self.assertTrue(leaks("Hi ha 18 pomes.", "C", OPTIONS))
        self.assertFalse(leaks("Compta primer.", "C", OPTIONS))


if __name__ == "__main__":
    unittest.main()
