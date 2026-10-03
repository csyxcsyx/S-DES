import unittest

from sdes_app.core import decrypt_block, decrypt_bytes, encrypt_block, encrypt_bytes, generate_subkeys, trace_block
from sdes_app.core.bit_ops import parse_bits
from .reference import reference_encrypt, reference_keys


class CoreTests(unittest.TestCase):
    def test_hand_calculated_vector_and_intermediate_steps(self):
        key, plaintext = 0b1010000010, 0b10011010
        self.assertEqual(generate_subkeys(key), (0b10100100, 0b10010010))
        trace = trace_block(plaintext, key)
        expected = (
            "1000001100", "0000111000", "10100100", "0001010001", "10010010", "00011011",
            "11010111", "01110011", "0011", "0110", "01111011", "10110111",
            "10111110", "00101100", "0001", "0100", "11110111", "11101111",
        )
        self.assertEqual(tuple(step.bits for step in trace.steps), expected)
        self.assertEqual(encrypt_block(plaintext, key), 0b11101111)
        self.assertEqual(decrypt_block(0b11101111, key), plaintext)
        self.assertEqual(trace_block(0b11101111, key, decrypt=True).output, plaintext)

    def test_independent_string_reference_for_every_key(self):
        for key in range(1024):
            self.assertEqual(generate_subkeys(key), tuple(int(bits, 2) for bits in reference_keys(key)))
            for block in (0, 1, 15, 85, 128, 154, 170, 255):
                self.assertEqual(encrypt_block(block, key), reference_encrypt(block, key), (block, key))

    def test_total_shift_two_creates_equivalent_keys(self):
        self.assertEqual(len({generate_subkeys(key) for key in range(1024)}), 512)
        for key in range(1024):
            self.assertEqual(generate_subkeys(key), generate_subkeys(key ^ 0b0100000000))
        for block in range(256):
            self.assertEqual(encrypt_block(block, 642), encrypt_block(block, 898))

    def test_exhaustive_262144_round_trips_and_permutations(self):
        for key in range(1024):
            ciphertexts = set()
            for block in range(256):
                cipher = encrypt_block(block, key)
                self.assertEqual(decrypt_block(cipher, key), block, (block, key))
                ciphertexts.add(cipher)
            self.assertEqual(len(ciphertexts), 256, key)

    def test_trace_matches_fast_api(self):
        for key in range(1024):
            for block in (0, 85, 154, 255):
                self.assertEqual(trace_block(block, key).output, encrypt_block(block, key))
                self.assertEqual(trace_block(block, key, True).output, decrypt_block(block, key))

    def test_byte_transform_preserves_every_value(self):
        data = bytes(range(256))
        for key in (0, 1, 642, 1023):
            self.assertEqual(decrypt_bytes(encrypt_bytes(data, key), key), data)
            self.assertEqual(encrypt_bytes(data, key), bytes(encrypt_block(value, key) for value in data))
            self.assertEqual(encrypt_bytes(b"", key), b"")

    def test_rejects_out_of_range_and_non_integer_arguments(self):
        for block in (-1, 256, True, 1.0, "0"):
            with self.assertRaises(ValueError):
                encrypt_block(block, 0)
        for key in (-1, 1024, False, 1.0, "0"):
            with self.assertRaises(ValueError):
                generate_subkeys(key)
        with self.assertRaises(ValueError):
            encrypt_bytes("text", 0)

    def test_bit_input_width_and_leading_zero(self):
        self.assertEqual(parse_bits("00000001", 8), 1)
        for value in ("", "1", "000000001", "0000000x", "００００００００", "0000 001"):
            with self.assertRaises(ValueError):
                parse_bits(value, 8)
