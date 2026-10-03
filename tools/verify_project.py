"""运行真实测试并生成实验数据；不会伪造其他小组的测试记录。"""
import csv
import io
import json
import platform
import sys
import unittest
from datetime import datetime
from pathlib import Path
from time import perf_counter
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from datetime import timedelta, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sdes_app.core import encrypt_block, encrypt_bytes, generate_subkeys
from sdes_app.services.exchange import export_vectors, write_csv
from sdes_app.services.experiments import analyze_collisions, search_keys
from sdes_app.services.text_cipher import format_ciphertext
from tools.reporting import write_report


def main():
    output = ROOT / "docs" / "evidence" / "results"
    output.mkdir(parents=True, exist_ok=True)
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT))
    started = perf_counter()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    duration = perf_counter() - started
    log = stream.getvalue()
    (output / "unittest.txt").write_text(log, encoding="utf-8")
    print(log)
    if not result.wasSuccessful():
        return 1
    pairs = [(154, 642), (0, 0), (255, 1023), (1, 1), (128, 512), (215, 170), (85, 341), (170, 682)]
    export_vectors(output / "local-vectors.csv", pairs)
    searches = []
    known = []
    for plaintext in (154, 85, 0, 255):
        known.append((plaintext, encrypt_block(plaintext, 642)))
        found = search_keys(known)
        searches.append({"pair_count": len(known), "pairs": [list(pair) for pair in known],
                         "candidates": [f"{key:010b}" for key in found.candidates],
                         "checked": found.checked, "elapsed_seconds": found.elapsed, "completed": found.completed})
    collisions = analyze_collisions(154, True)
    write_csv(output / "collision-statistics.csv", ("plaintext", "distinct_ciphertexts", "collision_groups", "max_candidates"),
              [(f"{row.plaintext:08b}", row.distinct_ciphertexts, row.collision_groups, row.max_candidates)
               for row in collisions.summaries])
    write_csv(output / "collision-mapping-10011010.csv", ("plaintext", "ciphertext", "key"),
              [("10011010", f"{cipher:08b}", f"{key:010b}") for cipher, keys in collisions.groups.items() for key in keys])
    text = "This is a test"
    encrypted = encrypt_bytes(text.encode("ascii"), 642)
    try:
        local_zone = ZoneInfo("Asia/Shanghai")
    except ZoneInfoNotFoundError:
        local_zone = timezone(timedelta(hours=8))
    import PySide6
    summary = {
        "generated_at": datetime.now(local_zone).isoformat(),
        "environment": {"python": platform.python_version(), "pyside6": PySide6.__version__,
                        "platform": platform.platform(), "processor": platform.processor()},
        "ui_motion": {"minimum_feedback_ms": 600, "page_transition_ms": 0,
                      "progress_transition_ms": 180, "compute_time_excludes_feedback": True,
                      "reduced_motion": "Windows 客户区动画偏好，或 SDES_REDUCED_MOTION=1"},
        "ui_tables": {"base_row_height": 44, "header_height": 42, "grid": "horizontal separators",
                      "scale_factors_verified": [1.5, 2.0], "persistent_model": True},
        "tests": {"run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
                  "elapsed_seconds": duration, "round_trip_combinations": 262144,
                  "independent_reference_combinations": 8192},
        "known_vector": {"plaintext": "10011010", "key": "1010000010", "ciphertext": "11101111",
                         "k1": "10100100", "k2": "10010010"},
        "key_equivalence": {"unique_subkey_pairs": len({generate_subkeys(key) for key in range(1024)}),
                            "xor_mask": "0100000000",
                            "all_keys_have_same_subkeys_as_partner": all(generate_subkeys(key) == generate_subkeys(key ^ 256)
                                                                        for key in range(1024)),
                            "sample_equivalent_keys": ["1010000010", "1110000010"]},
        "ascii": {"plaintext": text, "ciphertext_hex": format_ciphertext(encrypted, "十六进制"),
                  "ciphertext_base64": format_ciphertext(encrypted, "Base64")},
        "searches": searches,
        "timing_note": "本地进程完成测试、缓存预热后的一次实测，包含搜索循环，不含界面启动；不代表性能保证。",
        "collisions": {"completed": collisions.completed, "checked": collisions.checked,
                       "elapsed_seconds": collisions.elapsed, "plaintext_count": len(collisions.summaries),
                       "selected_summary": next(row.__dict__ for row in collisions.summaries if row.plaintext == 154),
                       "min_distinct_ciphertexts": min(row.distinct_ciphertexts for row in collisions.summaries),
                       "max_distinct_ciphertexts": max(row.distinct_ciphertexts for row in collisions.summaries),
                       "min_max_candidates": min(row.max_candidates for row in collisions.summaries),
                       "max_max_candidates": max(row.max_candidates for row in collisions.summaries)},
        "external_cross_test": {"status": "待完成", "reason": "尚未取得其他小组程序或测试数据"},
    }
    path = output / "summary.json"
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(ROOT, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
