"""Deterministic scoring + routing. No AI here: the AI only produces extracted.json.
Run: python score.py extracted.json
"""
import json, sys

WEIGHTS = {"experience": 30, "price": 25, "timeline": 15, "warranty": 15, "team": 15}


def gate(p, ceiling, max_weeks):
    """Return (status, reason) before any scoring."""
    if not p["licence_held"]:
        return "ineligible", "Licence not held by bidder (relies on a later-named subcontractor)"
    if not p["wsib_and_insurance"]:
        return "ineligible", "WSIB or $5M insurance not confirmed"
    if p["price"] is None or p["price"] > ceiling:
        return "ineligible", "Price missing or over budget ceiling"
    if p["weeks"] is not None and p["weeks"] > max_weeks:
        return "ineligible", "Timeline exceeds 16 weeks"
    if p["injection_suspected"]:
        return "flagged", "Embedded instruction aimed at the reviewer/AI; human review required"
    if p["weeks"] is None:
        return "flagged", "No committed schedule; timeline cannot be scored"
    return "ok", ""


def component_scores(p, best_price, best_weeks):
    return {
        "experience": 100 * min(p["qualifying_installs"], 15) / 15,
        "price": 100 * best_price / p["price"],
        "timeline": 0 if p["weeks"] is None else 100 * best_weeks / p["weeks"],
        "warranty": 50 * min(p["panel_years"], 25) / 25 + 50 * min(p["workmanship_years"], 12) / 12,
        "team": 25 * sum([p["named_lead"], p["crew_stated"], p["safety_plan"], p["monitoring_plan"]]),
    }


def total(c):
    return round(sum(c[k] * WEIGHTS[k] / 100 for k in WEIGHTS), 1)


def main(path):
    data = json.load(open(path))
    props = data["proposals"]
    gates = {k: gate(v, data["budget_ceiling"], data["max_weeks"]) for k, v in props.items()}
    # Normalisation reference = best value among proposals that passed mandatory gates
    passed = {k: v for k, v in props.items() if gates[k][0] in ("ok", "flagged")}
    best_price = min(v["price"] for v in passed.values())
    best_weeks = min(v["weeks"] for v in passed.values() if v["weeks"] is not None)
    out = {}
    for k, v in props.items():
        status, why = gates[k]
        if status == "ineligible":
            out[k] = (status, None, why)
        else:
            c = component_scores(v, best_price, best_weeks)
            out[k] = (status, total(c), why, c)
    ranked = sorted([k for k in out if out[k][0] == "ok"], key=lambda k: -out[k][1])
    for i, k in enumerate(ranked, 1):
        print(f"{i}. {k} score={out[k][1]}  components={ {a: round(b,1) for a,b in out[k][3].items()} }")
    for k in out:
        if out[k][0] != "ok":
            extra = f" (provisional, if cleared: {out[k][1]})" if out[k][0] == "flagged" and k == "C" else ""
            print(f"-  {k} {out[k][0]}: {out[k][2]}{extra}")


if __name__ == "__main__":
    main(sys.argv[1])
