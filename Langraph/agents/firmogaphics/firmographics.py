# %%
import sys
from langchain_openai import ChatOpenAI,OpenAIEmbeddings
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate,ChatPromptTemplate
sys.path.insert(1, r'D:\Notebooks\LLM\env')
from enviorment import load_env
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os 
load_env()
model =ChatOpenAI()
from langchain_openai import OpenAIEmbeddings


# %%
import json
import re
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

# %%
from langchain_core.messages import HumanMessage, SystemMessage
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# %%
MAX_CHARS_PER_PAGE = 10_000   # per URL — reduced for speed
MAX_CHARS_TOTAL    = 40_000   # per search — enough context, smaller = faster LLM
URLS_PER_SEARCH    = 2        # reduced from 3

# %%

# ---------------------------------------------------------------------------
# Company name cleaner
# ---------------------------------------------------------------------------

_INSURANCE_SUFFIXES = [
    "terrorism", "property", "casualty", "liability", "marine", "aviation",
    "cyber", "workers comp", "workers compensation", "auto", "automobile",
    "umbrella", "excess", "gl", "general liability", "professional liability",
    "directors and officers", "d&o", "e&o", "errors and omissions",
    "inland marine", "crime", "surety", "fidelity", "flood", "earthquake",
    "boiler", "machinery", "equipment breakdown", "trade credit",
    "political risk", "kidnap", "ransom", "k&r", "product liability",
    "environmental", "construction", "builders risk", "package", "bop",
    "monoline", "primary", "quota share", "facultative", "treaty",
]

_SUFFIX_PATTERN = re.compile(
    r"[\s\-–/|,;]+("
    + "|".join(re.escape(s) for s in _INSURANCE_SUFFIXES)
    + r")[\s\-–/|,;]*$",
    re.IGNORECASE,
)


def clean_company_name(raw: str) -> str:
    """Strip insurance line/coverage suffixes from raw submission system company names."""
    name = raw.strip()
    prev = None
    while prev != name:
        prev = name
        name = _SUFFIX_PATTERN.sub("", name).strip()
    return re.sub(r"[\s\-–/|,;]+$", "", name).strip()




# %%
from langchain_community.tools.tavily_search import TavilySearchResults

# %%
search_Tavily = TavilySearchResults(max_results=2)
l=search_Tavily.invoke("State Farm Insurance")

# %%
for i in l:
    print(i['content'])

# %%

def _search(query: str) -> str:
    """
    Run a web search. Returns concatenated page text.
    """
    try:
       search_Tavily = TavilySearchResults(max_results=2)
       l=search_Tavily.invoke(query)
       s=[]
       for i in l:
            s.append(i['content'])
       output = "\n\n".join(s)
    except Exception as exc:
        logger.warning("SERP failed | query=%r | %s", query, exc)
        return f"[SERP unavailable for: {query}]"

    #logger.debug("search done | query=%r | pages=%d | chars=%d", query,  len(output))
    return output


# %%

def _run_parallel(queries: dict[str, str]) -> dict[str, str]:
    """
    Run multiple searches in parallel.

    Parameters
    ----------
    queries : dict[label -> query_string]
    zyte_token : str

    Returns
    -------
    dict[label -> result_text]
    """
    results = {}
    with ThreadPoolExecutor(max_workers=len(queries)) as pool:
        futures = {pool.submit(_search, q): label for label, q in queries.items()}
        for future in as_completed(futures):
            label = futures[future]
            try:
                results[label] = future.result()
            except Exception as exc:
                results[label] = f"[Error: {exc}]"
    return results

# %%
def _make_llm() :
    return ChatOpenAI()
def _extract_json(raw: str) -> dict:
    """Strip markdown fences and parse JSON from LLM response."""
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw).strip()
    return json.loads(raw)
# ---------------------------------------------------------------------------
# Step 1b — extract parent name from Phase 1 search results
# ---------------------------------------------------------------------------

_PARENT_EXTRACT_SYSTEM = """You are a corporate ownership analyst.
From the search results provided, identify the GLOBAL ULTIMATE PARENT of the subject company.
The global ultimate parent is the top-level entity at the very top of the ownership chain
with no further parent company above it.

Return ONLY a JSON object with exactly these two keys:
{
  "global_ultimate_parent": string or null,
  "global_ultimate_parent_country": string or null
}

- If a clear ultimate parent is found, return its full legal name and country.
- If the company appears to be independent (no parent), return null for both.
- Return ONLY the JSON. No explanation, no markdown fences."""


def _extract_parent_name(company: str, country: str, search_text: str, llm) -> tuple[str | None, str | None]:
    """Quick LLM call to pull the global ultimate parent name from Phase 1 results."""
    prompt = f"""Subject company: {company} ({country})

Search results about ownership:
{search_text[:15_000]}

Return ONLY the JSON with global_ultimate_parent and global_ultimate_parent_country."""

    try:
        response = llm.invoke([
            SystemMessage(content=_PARENT_EXTRACT_SYSTEM),
            HumanMessage(content=prompt),
        ])
        raw = response.content if hasattr(response, "content") else str(response)
        parsed = _extract_json(raw)
        parent = parsed.get("global_ultimate_parent")
        parent_country = parsed.get("global_ultimate_parent_country")
        logger.info("Parent identified | parent=%r | country=%r", parent, parent_country)
        return parent, parent_country
    except Exception as exc:
        logger.warning("Parent extraction failed | %s", exc)
        return None, None



# %%

# ---------------------------------------------------------------------------
# Step 3 — final synthesis
# ---------------------------------------------------------------------------

_SYNTHESIS_SYSTEM = """You are a corporate data extraction specialist.
You will be given web search results and must extract specific fields into a JSON object.
Return ONLY valid JSON — no markdown fences, no explanation outside the JSON.

JSON schema (return exactly these keys):
{
  "subject_company":                              string,
  "subject_company_revenue_usd_millions":         number | null,
  "subject_company_revenue_fy":                   string | null,
  "subject_company_revenue_source":               string | null,
  "global_ultimate_parent":                       string | null,
  "global_ultimate_parent_country":               string | null,
  "global_ultimate_parent_revenue_usd_millions":  number | null,
  "global_ultimate_parent_revenue_fy":            string | null,
  "global_ultimate_parent_revenue_source":        string | null,
  "fx_rate_applied":                              string | null,
  "mad_classification":                           "MAD Account" | "Non-MAD Account" | "Undetermined",
  "mad_revenue_basis":                            string,
  "error":                                        null | string
}

## Global Ultimate Parent
Use the parent name already identified — do not change it unless the search results
clearly show a higher-level entity above it.

## Revenue — Currency Conversion (MANDATORY)
Convert ALL revenue to USD millions BEFORE classification.
NEVER compare local currency against the threshold directly.

Formula: USD millions = local amount in millions × FX rate
  SGD × 0.74  |  GBP × 1.27  |  EUR × 1.08  |  AUD × 0.65
  NZD × 0.60  |  CAD × 0.74  |  HKD × 0.13  |  INR ÷ 83   |  JPY ÷ 150

Examples:
  NZD 2.0B = 2000 × 0.60 = 1200 USD M  → MAD  (> 1000)
  AUD 1.5B = 1500 × 0.65 =  975 USD M  → Non-MAD (≤ 1000)
  SGD 2.4B = 2400 × 0.74 = 1776 USD M  → MAD  (> 1000)
  USD 800M =  800 × 1.00 =  800 USD M  → Non-MAD (≤ 1000)

## MAD Classification
Priority: global ultimate parent revenue → subject company revenue → Undetermined
Threshold = 1,000 USD millions (= USD 1 billion):
  > 1000 → "MAD Account" | ≤ 1000 → "Non-MAD Account"

Revenue source priority:
  1. Company annual report  2. Investor relations  3. Stock exchange filing  4. Bloomberg/Reuters

Set mad_revenue_basis to show the arithmetic: e.g. "AUD 1.5B × 0.65 = 975M ≤ 1000M → Non-MAD"
"""


# %%

def _build_synthesis_prompt(company: str, country: str, parent: str | None,
                             parent_country: str | None, search_results: dict[str, str]) -> str:
    parent_line = f"Global Ultimate Parent (already identified): {parent} ({parent_country})" \
        if parent else "Global Ultimate Parent: not yet identified — infer from search results"

    sections = "\n\n".join(
        f"=== {label.upper()} ===\n{text}"
        for label, text in search_results.items()
    )
    return f"""Extract the required JSON fields from the search results below.

Subject Company: {company}
Country: {country}
{parent_line}

SEARCH RESULTS:
{sections}

Return ONLY the JSON object. No other text."""


# ---------------------------------------------------------------------------
# Core lookup logic
# ---------------------------------------------------------------------------

def lookup_company(company_name: str, country: str) -> dict:
    """
    Look up global ultimate parent and revenue for a single company.

    Execution flow:
      Phase 1 (parallel)  — find parent chain AND subject revenue simultaneously
      Step  1b            — quick LLM call to extract the parent name from Phase 1
      Phase 2 (parallel)  — search parent revenue using the ACTUAL parent name
      Phase 3             — single LLM synthesis call → JSON

    Returns a JSON-serialisable dict with consistent schema.
    """
    run_id = str(uuid.uuid4())
    raw_name = company_name
    company_name = clean_company_name(company_name)

    if raw_name != company_name:
        logger.info("Name cleaned | %r → %r", raw_name, company_name)

    logger.info("Lookup started | run_id=%s | company=%r | country=%r", run_id, company_name, country)
    start = time.perf_counter()

    base = {
        "run_id": run_id,
        "raw_company_name": raw_name,
        "subject_company": company_name,
        "country": country,
        "subject_company_revenue_usd_millions": None,
        "subject_company_revenue_fy": None,
        "subject_company_revenue_source": None,
        "global_ultimate_parent": None,
        "global_ultimate_parent_country": None,
        "global_ultimate_parent_revenue_usd_millions": None,
        "global_ultimate_parent_revenue_fy": None,
        "global_ultimate_parent_revenue_source": None,
        "fx_rate_applied": None,
        "mad_classification": "Undetermined",
        "mad_revenue_basis": None,
        "elapsed_seconds": None,
        "error": None,
    }

    raw_response = ""
    try:
        llm = _make_llm()

        # -- Fetch Zyte token ONCE for the entire lookup ------------------
        #zyte_token = token_zyte()
        logger.debug("Zyte token fetched in %.2fs", time.perf_counter() - start)

        # -- Phase 1: parallel — find parent chain + subject revenue ------
        logger.info("Phase 1 | parent chain + subject revenue (parallel)")
        phase1 = _run_parallel({
            "parent_chain":    f"{company_name} parent company ultimate owner global holding group {country}",
            "subject_revenue": f"{company_name} annual report latest revenue {country}",
        })
        logger.info("Phase 1 done | %.2fs", time.perf_counter() - start)

        # -- Step 1b: extract actual parent name from Phase 1 results -----
        parent_name, parent_country = _extract_parent_name(
            company_name, country, phase1["parent_chain"], llm
        )
        logger.info("Step 1b done | parent=%r | %.2fs", parent_name, time.perf_counter() - start)

        # -- Phase 2: parallel — search parent revenue by ACTUAL name -----
        if parent_name:
            logger.info("Phase 2 | parent revenue searches using %r (parallel)", parent_name)
            phase2 = _run_parallel({
                "parent_revenue_annual_report":  f"{parent_name} annual report latest revenue fiscal year",
                "parent_revenue_filing":         f"{parent_name} investor relations revenue annual report SEC 10-K Bloomberg",
            })
        else:
            logger.info("Phase 2 | no parent found — skipping parent revenue searches")
            phase2 = {}
        logger.info("Phase 2 done | %.2fs", time.perf_counter() - start)

        # -- Phase 3: single LLM synthesis call ---------------------------
        all_results = {**phase1, **phase2}
        synthesis_prompt = _build_synthesis_prompt(
            company_name, country, parent_name, parent_country, all_results
        )

        logger.info("Phase 3 | LLM synthesis call")
        response = llm.invoke([
            SystemMessage(content=_SYNTHESIS_SYSTEM),
            HumanMessage(content=synthesis_prompt),
        ])
        raw_response = response.content if hasattr(response, "content") else str(response)

        parsed = _extract_json(raw_response)
        base.update({k: v for k, v in parsed.items() if k in base})

        # Ensure parent fields from Step 1b are preserved if LLM left them null
        if parent_name and not base.get("global_ultimate_parent"):
            base["global_ultimate_parent"] = parent_name
        if parent_country and not base.get("global_ultimate_parent_country"):
            base["global_ultimate_parent_country"] = parent_country

    except json.JSONDecodeError as exc:
        logger.error("JSON parse failed | run_id=%s | %s | raw=%r", run_id, exc, raw_response[:300])
        base["error"] = f"JSON parse error: {exc} — raw: {raw_response[:200]}"
    except Exception as exc:
        logger.error("Lookup failed | run_id=%s | %s", run_id, exc, exc_info=True)
        base["error"] = str(exc)

    base["elapsed_seconds"] = round(time.perf_counter() - start, 2)
    logger.info(
        "Lookup done | run_id=%s | company=%r | parent=%r | mad=%s | elapsed=%.2fs",
        run_id, company_name, base["global_ultimate_parent"],
        base["mad_classification"], base["elapsed_seconds"],
    )
    return base



# %%
#lookup_company("SINGAPORE TECHNOLOGIES ENGINEERING LTD", "Singapore")

# %%



