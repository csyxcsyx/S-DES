import csv
import tempfile
import unittest
from pathlib import Path
from threading import Event

from sdes_app.core import encrypt_block, encrypt_bytes
from sdes_app.services.checks import run_checks
from sdes_app.services.exchange import export_vectors, verify_csv, write_csv
from sdes_app.services.experiments import analyze_collisions, search_keys
from sdes_app.services.text_cipher import FORMATS, ascii_bytes, ascii_text, decrypt_text, encrypt_text, format_ciphertext, parse_ciphertext


class TextTests(unittest.TestCase):
    def test_all_ascii_control_characters_and_empty_text(self):
        for text in ("", "This is a test", " \t\r\n\x00\x7f", "".join(map(chr, range(128)))):
            encrypted = encrypt_text(text, 642)
            self.assertEqual(decrypt_text(encrypted, 642), text)
            for name in FORMATS:
                self.assertEqual(parse_ciphertext(format_ciphertext(encrypted, name), name), encrypted)

    def test_all_byte_values_round_trip_all_formats(self):
        data = bytes(range(256))
        for name in FORMATS:
            formatted = format_ciphertext(data, name)
            self.assertEqual(parse_ciphertext(" \n" + formatted + "\t", name), data)

    def test_invalid_ascii_ciphertext_and_format(self):
        for text in ("中文", "a🙂", "é"):
            with self.assertRaises(ValueError):
                ascii_bytes(text)
        with self.assertRaises(ValueError):
            ascii_text(b"\xff")
        for text, name in (("001", "二进制"), ("0000000x", "二进制"), ("F", "十六进制"),
                           ("GG", "十六进制"), ("Zg", "Base64"), ("!!!!", "Base64"),
                           ("Zh==", "Base64"), ("中文", "Base64"), ("", "unknown")):
            with self.assertRaises(ValueError):
                parse_ciphertext(text, name)


class ExperimentTests(unittest.TestCase):
    def test_search_returns_all_candidates_and_multi_pair_intersection(self):
        pair = (154, encrypt_block(154, 642))
        first = search_keys([pair])
        self.assertTrue(first.completed)
        self.assertEqual(first.checked, 1024)
        self.assertIn(642, first.candidates)
        self.assertGreater(len(first.candidates), 1)
        second_pair = (85, encrypt_block(85, 642))
        second = search_keys([pair, second_pair])
        expected = tuple(key for key in first.candidates if encrypt_block(85, key) == second_pair[1])
        self.assertEqual(second.candidates, expected)
        self.assertIn(642, second.candidates)

    def test_inconsistent_pairs_have_no_candidate(self):
        self.assertEqual(search_keys([(0, 0), (0, 1)]).candidates, ())
        with self.assertRaises(ValueError):
            search_keys([])

    def test_cancel_is_explicit_and_progress_matches_checked(self):
        cancel = Event()
        updates = []

        def on_progress(checked, total):
            updates.append((checked, total))
            cancel.set()

        result = search_keys([(154, 239)], on_progress, cancel)
        self.assertFalse(result.completed)
        self.assertEqual(result.checked, 32)
        self.assertEqual(updates[-1], (32, 1024))
        self.assertTrue(all(key < 32 for key in result.candidates))
        self.assertGreaterEqual(result.elapsed, 0)

    def test_collision_groups_cover_keys_and_equal_attack_candidates(self):
        result = analyze_collisions(154)
        self.assertTrue(result.completed)
        self.assertEqual(sorted(key for keys in result.groups.values() for key in keys), list(range(1024)))
        self.assertEqual(result.groups[239], search_keys([(154, 239)]).candidates)
        summary = result.summaries[0]
        self.assertEqual(summary.distinct_ciphertexts, len(result.groups))
        self.assertEqual(summary.collision_groups, sum(len(keys) > 1 for keys in result.groups.values()))
        self.assertGreater(summary.max_candidates, 1)

    def test_whole_plaintext_space_and_cancelled_partial_groups(self):
        result = analyze_collisions(154, True)
        self.assertTrue(result.completed)
        self.assertEqual(result.checked, 262144)
        self.assertEqual([row.plaintext for row in result.summaries], list(range(256)))
        self.assertTrue(all(row.collision_groups > 0 for row in result.summaries))
        cancel = Event()

        def stop_after_selected(checked, total):
            if checked == 1024:
                cancel.set()

        partial = analyze_collisions(154, True, stop_after_selected, cancel)
        self.assertFalse(partial.completed)
        self.assertEqual(len(partial.summaries), 1)
        self.assertEqual(partial.groups, result.groups)
        cancel.set()
        empty = analyze_collisions(154, cancel=cancel)
        self.assertFalse(empty.completed)
        self.assertEqual(empty.groups, {})

    def test_in_app_checks_and_cancellation(self):
        result = run_checks(True)
        self.assertTrue(result.completed)
        self.assertEqual(result.checked, 262144)
        self.assertTrue(all(row.passed for row in result.rows))
        cancel = Event()
        cancel.set()
        partial = run_checks(True, cancel=cancel)
        self.assertFalse(partial.completed)


class ExchangeTests(unittest.TestCase):
    def test_export_then_verify_and_bad_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "vectors.csv"
            export_vectors(path, [(154, 642), (0, 0), (255, 1023)])
            rows = verify_csv(path)
            self.assertTrue(all(row.passed for row in rows))
            self.assertEqual(rows[0].ciphertext, "11101111")
            write_csv(path, ("plaintext", "key", "ciphertext"),
                      [("10011010", "1010000010", "00000000"), ("x", "0000000000", "00000000")])
            rows = verify_csv(path)
            self.assertFalse(rows[0].passed)
            self.assertFalse(rows[1].passed)
            self.assertTrue(rows[1].error)

    def test_wrong_header_empty_and_extra_columns(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "vectors.csv"
            path.write_text("key,plaintext,ciphertext\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                verify_csv(path)
            path.write_text("plaintext,key,ciphertext\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                verify_csv(path)
            path.write_text("plaintext,key,ciphertext\n00000000,0000000000,00000000,extra\n", encoding="utf-8")
            self.assertFalse(verify_csv(path)[0].passed)
