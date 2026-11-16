"""
Unit test to verify all 10 Golden Historical Cases exist and have valid structure.
"""

import json
from pathlib import Path
import pytest

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

        assert "case_id" in data
        assert "name" in data
        assert "quant_payload" in data
        assert "expected_evaluation" in data
        assert "verdict" in data["expected_evaluation"]
        assert "required_socratic_topics" in data["expected_evaluation"]
        assert len(data["expected_evaluation"]["required_socratic_topics"]) >= 2
