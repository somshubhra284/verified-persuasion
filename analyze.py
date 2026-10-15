"""Results table from participant logs: belief change per arm, plus unsupported claims (system arm).

  python3 analyze.py               # reads sessions/P*.jsonl (+ P*.check.jsonl from check_claims.py)
  python3 analyze.py some/dir      # same, other folder
  python3 analyze.py --selfcheck   # offline asserts

Lower score = less agreement with "I don't need a health insurance policy of my own", so a negative delta is the
belief moving. No significance tests: n is 5-7; report the numbers and say so.
"""
import json, sys, tempfile
from pathlib import Path
from statistics import mean

HERE = Path(__file__).parent


def load(path):
    """One participant: arm, status, bucket, scores, checker summary."""
    p = {"pid": path.stem, "arm": None, "status": "incomplete", "bucket": None, "t0": None, "t1": None, "t2": None,
         "looked": None, "factual": None, "unsupported": None, "agreement": None}
    for e in map(json.loads, path.read_text().splitlines()):
        ev = e["event"]
        if ev in ("declined", "screened_out"):
            p["status"], p["arm"] = ev, e.get("arm")
        elif ev == "t0":
            p["t0"], p["arm"] = e["score"], e.get("arm")
        elif ev == "classify":
            p["bucket"] = e.get("primary")
        elif ev == "end" and e.get("reason") == "unclassified":
            p["status"] = "unclassified"
        elif ev == "t1":
            p["t1"], p["status"] = e["score"], "complete"
        elif ev == "t2":
            p["t2"], p["looked"] = e["score"], e.get("looked_into_policy")
    check = path.with_suffix(".check.jsonl")
    if check.exists():
        summary = json.loads(check.read_text().splitlines()[-1])["summary"]
        # ponytail: hand labels are the metric (16 Oct decision); an unreviewed session shows "unreviewed", never the checker count
        p["factual"] = summary.get("hand_factual", summary["factual_sentences"])
        p["unsupported"] = summary.get("hand_unsupported", "unreviewed")
        p["agreement"] = summary.get("checker_agreement")
    return p


def delta(a, b):
    return None if a is None or b is None else b - a


def fmt(x):
    return "–" if x is None else f"{x:+.1f}" if isinstance(x, float) else str(x)


def report(folder):
    people = [load(f) for f in sorted(Path(folder).glob("P*.jsonl")) if not f.name.endswith(".check.jsonl")]
    done = [p for p in people if p["status"] == "complete"]
    lines = ["| pid | arm | bucket | T0 | T1 | T2 | ΔT1 | ΔT2 | looked into policy | factual sentences | unsupported claims (hand) | checker agreed |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for p in done:
        lines.append("| " + " | ".join(fmt(x) for x in (p["pid"], p["arm"], p["bucket"], p["t0"], p["t1"], p["t2"],
                     delta(p["t0"], p["t1"]), delta(p["t0"], p["t2"]), p["looked"], p["factual"], p["unsupported"], p["agreement"])) + " |")
    summary = {}
    lines += ["", "| arm | n | mean ΔT1 | mean ΔT2 (n) | looked into policy | unsupported claims per conversation |",
              "|---|---|---|---|---|---|"]
    for arm in ("system", "brief"):
        g = [p for p in done if p["arm"] == arm]
        d1 = [delta(p["t0"], p["t1"]) for p in g]
        d2 = [delta(p["t0"], p["t2"]) for p in g if p["t2"] is not None]
        unsup = [p["unsupported"] for p in g if isinstance(p["unsupported"], int)]
        s = {"n": len(g), "d1": mean(d1) if d1 else None, "d2": mean(d2) if d2 else None, "n2": len(d2),
             "looked": sum(p["looked"] == "yes" for p in g), "unsup": mean(unsup) if unsup else None}
        summary[arm] = s
        lines.append(f"| {arm} | {s['n']} | {fmt(s['d1'])} | {fmt(s['d2'])} ({s['n2']}) | {s['looked']}/{s['n']} | "
                     f"{fmt(s['unsup'])} |")
    others = {st: sum(p["status"] == st for p in people) for st in ("declined", "screened_out", "unclassified", "incomplete")}
    lines += ["", "Not in the table: " + ", ".join(f"{k} {v}" for k, v in others.items()) + f" (of {len(people)} sessions)."]
    return "\n".join(lines), summary


def selfcheck():
    with tempfile.TemporaryDirectory() as d:
        def write(name, events):
            Path(d, name).write_text("\n".join(json.dumps(e) for e in events) + "\n")
        write("P01.jsonl", [{"event": "t0", "score": 80, "arm": "system"}, {"event": "classify", "primary": "B3"},
                            {"event": "t1", "score": 50}, {"event": "t2", "score": 60, "looked_into_policy": "yes"}])
        write("P01.check.jsonl", [{"summary": {"factual_sentences": 6, "unsupported_claims": 3, "hand_factual": 6,
                                               "hand_unsupported": 1, "checker_agreement": "4/6"}}])
        write("P02.jsonl", [{"event": "t0", "score": 70, "arm": "brief"}, {"event": "classify", "primary": "B2"},
                            {"event": "t1", "score": 65}])
        write("P03.jsonl", [{"event": "t0", "score": 40, "arm": "brief"}, {"event": "screened_out", "arm": "brief"}])
        write("P04.jsonl", [{"event": "declined", "arm": "system"}])
        text, s = report(d)
    assert s["system"]["n"] == 1 and s["system"]["d1"] == -30 and s["system"]["d2"] == -20 and s["system"]["unsup"] == 1
    assert s["brief"]["n"] == 1 and s["brief"]["d1"] == -5 and s["brief"]["d2"] is None and s["brief"]["unsup"] is None
    assert "screened_out 1" in text and "declined 1" in text and "| P01 | system | B3 | 80 | 50 | 60 | -30 | -20 | yes | 6 | 1 | 4/6 |" in text
    print("selfcheck ok")


if __name__ == "__main__":
    selfcheck()
    args = [a for a in sys.argv[1:] if a != "--selfcheck"]
    if "--selfcheck" not in sys.argv:
        print(report(args[0] if args else HERE / "sessions")[0])
