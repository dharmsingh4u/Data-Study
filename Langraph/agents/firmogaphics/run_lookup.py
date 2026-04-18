"""
run_lookup.py
-------------
Reads companies from Calude-input.xlsx, runs lookup_company() for each,
and appends results to output_results.jsonl (one JSON object per line).

Resume-safe: on restart it reads the output file, finds already-processed
run keys (company + country), and skips them — so no duplicate work.

Usage:
    python run_lookup.py

Optional env vars:
    INPUT_FILE   — path to xlsx  (default: Calude-input.xlsx)
    OUTPUT_FILE  — path to jsonl (default: output_results.jsonl)
    MAX_ROWS     — max number of rows to process (default: all)
"""

import json
import os
import sys
import time
import traceback

import pandas as pd

from firmographics import lookup_company

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
INPUT_FILE  = os.getenv("INPUT_FILE",  "Calude-input.xlsx")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "output_results.jsonl")
MAX_ROWS    = int(os.getenv("MAX_ROWS", 0))  # 0 = no limit

COMPANY_COL = "Company_Name_Global_Parent"
COUNTRY_COL = "Country_Global_Parent"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resume_key(company: str, country: str) -> str:
    return f"{company.strip().lower()}|||{country.strip().lower()}"


def load_already_done(output_path: str) -> set:
    """Return a set of resume keys for rows already written to the output file."""
    done = set()
    if not os.path.exists(output_path):
        return done
    with open(output_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                key = _resume_key(
                    obj.get("raw_company_name") or obj.get("subject_company", ""),
                    obj.get("country", ""),
                )
                done.add(key)
            except json.JSONDecodeError:
                pass  # skip corrupt lines
    return done


def append_result(output_path: str, result: dict) -> None:
    """Append a single result dict as a JSON line."""
    with open(output_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(result, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # -- Load input ----------------------------------------------------------
    print(f"Loading input: {INPUT_FILE}")
    df = pd.read_excel(INPUT_FILE)

    if COMPANY_COL not in df.columns or COUNTRY_COL not in df.columns:
        sys.exit(
            f"ERROR: Expected columns '{COMPANY_COL}' and '{COUNTRY_COL}' "
            f"in {INPUT_FILE}. Found: {df.columns.tolist()}"
        )

    rows = df[[COMPANY_COL, COUNTRY_COL]].dropna(subset=[COMPANY_COL]).to_dict("records")
    if MAX_ROWS > 0:
        rows = rows[:MAX_ROWS]
    total = len(rows)
    print(f"Total rows to process: {total}")

    # -- Resume: find already-done companies ---------------------------------
    done_keys = load_already_done(OUTPUT_FILE)
    print(f"Already done (will skip): {len(done_keys)}")

    # -- Loop ----------------------------------------------------------------
    processed = 0
    skipped   = 0
    errors    = 0

    for idx, row in enumerate(rows, start=1):
        company = str(row[COMPANY_COL]).strip()
        country = str(row.get(COUNTRY_COL, "")).strip()
        key     = _resume_key(company, country)

        if key in done_keys:
            skipped += 1
            continue

        print(f"[{idx}/{total}] Running: {company!r} | {country!r}")
        try:
            result = lookup_company(company, country)
            # Attach the original country in case lookup_company doesn't store it
            if "country" not in result:
                result["country"] = country
        except Exception as exc:
            errors += 1
            print(f"  ERROR: {exc}")
            traceback.print_exc()
            result = {
                "raw_company_name": company,
                "subject_company":  company,
                "country":          country,
                "mad_classification": "Undetermined",
                "error": str(exc),
            }

        append_result(OUTPUT_FILE, result)
        done_keys.add(key)   # prevent re-run within the same session
        processed += 1

        mad = result.get("mad_classification", "?")
        parent = result.get("global_ultimate_parent", "—")
        elapsed = result.get("elapsed_seconds", "?")
        print(f"  >> MAD={mad} | parent={parent!r} | {elapsed}s")

    # -- Summary -------------------------------------------------------------
    print("\n=== Done ===")
    print(f"  Processed : {processed}")
    print(f"  Skipped   : {skipped}")
    print(f"  Errors    : {errors}")
    print(f"  Output    : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
