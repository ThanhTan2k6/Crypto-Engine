"""
Unit test to verify all 10 Golden Historical Cases exist and have valid structure.
"""

import json
from pathlib import Path

GOLDEN_EVAL_DIR = Path("data/golden_eval")

EXPECTED_CASES = [
    "gc01_luna_crash.json",
    "gc02_ftx_insolvency.json",
    "gc03_cycle_top_mvrv.json",
    "gc04_sui_apt_vesting_cliff.json",
    "gc05_short_squeeze_funding.json",
    "gc06_binance_whale_dump.json",
    "gc07_fed_pivot_trap.json",
    "gc08_covid_black_thursday.json",
    "gc09_wash_trading_spike.json",
    "gc10_range_low_bear_trap.json",
]


def test_all_10_golden_cases_exist_and_valid():
    assert GOLDEN_EVAL_DIR.exists(), "data/golden_eval directory must exist"
    files = list(GOLDEN_EVAL_DIR.glob("*.json"))
    assert len(files) == 10, f"Expected exactly 10 Golden Cases, found {len(files)}"

    for case_file in EXPECTED_CASES:
        filepath = GOLDEN_EVAL_DIR / case_file
        assert filepath.exists(), f"Missing golden case: {case_file}"

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert isinstance(data, dict), f"{case_file} root must be a JSON object"
        assert isinstance(data.get("case_id"), str) and data["case_id"].strip(), f"{case_file} missing valid case_id"
        assert isinstance(data.get("name"), str) and data["name"].strip(), f"{case_file} missing valid name"
        assert isinstance(data.get("quant_payload"), dict) and len(data["quant_payload"]) > 0, (
            f"{case_file} quant_payload must be a non-empty mapping"
        )
        assert isinstance(data.get("expected_evaluation"), dict), f"{case_file} missing expected_evaluation dict"
        expected = data["expected_evaluation"]
        assert isinstance(expected.get("verdict"), str) and expected["verdict"].strip(), (
            f"{case_file} missing valid verdict string"
        )
        topics = expected.get("required_socratic_topics")
        assert isinstance(topics, list) and len(topics) >= 2, (
            f"{case_file} required_socratic_topics must be a list of at least 2 topics"
        )
        assert all(isinstance(t, str) and len(t.strip()) > 0 for t in topics), (
            f"{case_file} topics must all be non-empty strings"
        )
