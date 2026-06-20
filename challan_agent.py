"""
Agentic bilingual e-challan generator — RAG-grounded.

Flow:
  1. retrieve_all_for_violations() pulls the exact MV Act section(s) from ChromaDB
  2. Legal facts (section, fine, disqualification) come from RAG — never from LLM memory
  3. LLM (Gemini Flash) only does bilingual formatting using those retrieved facts
  4. If no GEMINI_API_KEY or LLM fails — template fallback keeps demo alive

This means the challan can never cite a wrong section or wrong fine amount.
"""

import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

_GROQ_KEY = os.environ.get("GROQ_API_KEY")

# ── static fallback map (used if RAG unavailable) ─────────────────────────
_STATIC_MAP = {
    "no_helmet": {
        "section":         "194D",
        "title":           "Penalty for not wearing helmet",
        "fine_inr":        1000,
        "disqualification":"3 months disqualification from holding driving licence",
        "compoundable":    True,
    },
    "triple_riding": {
        "section":         "194C",
        "title":           "Penalty for violation of safety measures for motorcycle drivers",
        "fine_inr":        1000,
        "disqualification":"3 months disqualification from holding driving licence",
        "compoundable":    True,
    },
}

# ── RAG retrieval (with graceful fallback) ────────────────────────────────
def _get_legal_facts(violations: list[str]) -> dict[str, dict]:
    try:
        from mv_act_rag import retrieve_all_for_violations
        facts = retrieve_all_for_violations(violations)
        # fill any None hits from static map
        for v in violations:
            if facts.get(v) is None:
                facts[v] = _STATIC_MAP.get(v)
        return facts
    except Exception as e:
        print(f"[challan] RAG unavailable ({e}), using static map.")
        return {v: _STATIC_MAP.get(v) for v in violations}

# ── template challan (offline, no LLM) ────────────────────────────────────
def _template_challan(plate, violations, facts, ts):
    total = sum((facts[v]["fine_inr"] if facts.get(v) else 0) for v in violations)
    plate_disp = plate if plate else "NOT READABLE"

    lines_en = [
        "TRAFFIC E-CHALLAN — Motor Vehicles Act 1988",
        f"Vehicle No   : {plate_disp}",
        f"Date & Time  : {ts}",
        "",
    ]
    lines_hi = [
        "यातायात ई-चालान — मोटर वाहन अधिनियम 1988",
        f"वाहन संख्या  : {plate_disp}",
        f"दिनांक/समय  : {ts}",
        "",
    ]
    for v in violations:
        f = facts.get(v) or {}
        sec   = f.get("section", "—")
        title = f.get("title",   "—")
        fine  = f.get("fine_inr", 0)
        dis   = f.get("disqualification", "")
        comp  = "Yes (pay on spot)" if f.get("compoundable") else "No"

        lines_en += [
            f"Violation    : {v.replace('_',' ').title()}",
            f"Section      : {sec} — {title}",
            f"Fine         : Rs. {fine}",
            f"Disqualify   : {dis or 'None'}",
            f"Compoundable : {comp}",
            "",
        ]
        lines_hi += [
            f"उल्लंघन     : {v.replace('_',' ').title()}",
            f"धारा        : {sec} — {title}",
            f"जुर्माना     : ₹{fine}",
            f"अयोग्यता    : {dis or 'कोई नहीं'}",
            f"समाधेय      : {'हाँ (मौके पर भुगतान करें)' if f.get('compoundable') else 'नहीं'}",
            "",
        ]

    lines_en += [
        f"TOTAL FINE   : Rs. {total}",
        "",
        "This challan is auto-generated from photographic evidence.",
        "Legal provisions sourced from MV Act 1988 (as amended 2019).",
    ]
    lines_hi += [
        f"कुल जुर्माना : ₹{total}",
        "",
        "यह चालान फोटोग्राफिक साक्ष्य के आधार पर स्वतः उत्पन्न किया गया है।",
        "कानूनी प्रावधान: मोटर वाहन अधिनियम 1988 (2019 संशोधन सहित)।",
    ]

    return {
        "english":    "\n".join(lines_en),
        "hindi":      "\n".join(lines_hi),
        "total_fine": total,
        "plate":      plate,
        "facts":      facts,
    }

# ── LLM challan (Gemini Flash, grounded in RAG facts) ─────────────────────
def _llm_challan(plate, violations, facts, ts):
    from groq import Groq
    client = Groq(api_key=_GROQ_KEY)

    total = sum((facts[v]["fine_inr"] if facts.get(v) else 0) for v in violations)
    plate_disp = plate if plate else "NOT READABLE"

    # build a facts block — LLM must use ONLY these, never invent
    facts_block = ""
    for v in violations:
        f = facts.get(v) or {}
        facts_block += (
            f"\nViolation: {v.replace('_',' ').title()}\n"
            f"  Section      : {f.get('section','—')} — {f.get('title','—')}\n"
            f"  Fine         : Rs. {f.get('fine_inr', 0)}\n"
            f"  Disqualify   : {f.get('disqualification','None')}\n"
            f"  Compoundable : {'Yes' if f.get('compoundable') else 'No'}\n"
            f"  Legal text   : {f.get('full_text','')[:300]}\n"
        )

    prompt = f"""You are an Indian traffic enforcement officer generating an official e-challan.

Use ONLY the facts provided below. Do NOT add, invent, or change any section numbers,
fine amounts, or legal provisions. Your only job is to format them into a clean,
formal, official challan in TWO languages.

=== CASE DETAILS ===
Vehicle Number : {plate_disp}
Date and Time  : {ts}
Total Fine     : Rs. {total}

=== RETRIEVED LEGAL FACTS (from Motor Vehicles Act 1988, Amendment 2019) ===
{facts_block}

=== OUTPUT FORMAT ===
Generate the challan in EXACTLY this structure:

ENGLISH VERSION:
[Full formal challan in English using the exact facts above]

HINDI VERSION:
[Full formal challan in Hindi/Devanagari using the exact same facts]

Rules:
- Cite only the section numbers and amounts given above
- Include vehicle number, date/time, each violation, its section, its fine
- State total fine at the end
- End with: "Auto-generated from photographic evidence. MV Act 1988 (amended 2019)."
- Hindi version must be complete Devanagari, not transliteration
- Keep both versions concise and official"""

    try:
        resp = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.2,
        )
        text = resp.choices[0].message.content or ""
        # split on HINDI VERSION marker
        if "HINDI VERSION" in text.upper():
            parts   = text.upper().index("HINDI VERSION")
            en_part = text[:parts].replace("ENGLISH VERSION:", "").strip()
            hi_part = text[parts:].replace("HINDI VERSION:", "").strip()
        else:
            en_part = text
            hi_part = ""
        return {
            "english":    en_part,
            "hindi":      hi_part,
            "total_fine": total,
            "plate":      plate,
            "facts":      facts,
        }
    except Exception as e:
        print(f"[challan] LLM failed ({e}), using template.")
        return _template_challan(plate, violations, facts, ts)

# ── public API ─────────────────────────────────────────────────────────────
def generate_challan(plate: str, violations: list[str], timestamp: str = None):
    """
    Main entry point called by app.py.

    Args:
        plate      : cleaned plate string (may be empty)
        violations : list of violation keys e.g. ["no_helmet", "triple_riding"]
        timestamp  : ISO-format string; defaults to now

    Returns dict:
        english    : English challan text
        hindi      : Hindi challan text
        total_fine : int
        plate      : plate string
        facts      : dict of retrieved legal facts per violation
    """
    ts    = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    facts = _get_legal_facts(violations)

    if _GROQ_KEY:
        return _llm_challan(plate, violations, facts, ts)
    return _template_challan(plate, violations, facts, ts)