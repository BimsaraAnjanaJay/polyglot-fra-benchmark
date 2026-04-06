import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

import requests

JAEGER_BASE = "http://localhost:16686/api"
CONFIG_PATH = Path("benchmark/functions.json")
THRESHOLDS = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80]

def load_config():
    data = json.loads(CONFIG_PATH.read_text())
    return data["functions"]

def fetch_traces(service_name: str, limit=2000):
    r = requests.get(f"{JAEGER_BASE}/traces", params={"service": service_name, "limit": limit})
    r.raise_for_status()
    return r.json().get("data", [])

def tag_dict(span):
    return {t["key"]: t.get("value") for t in span.get("tags", [])}

def collect_counts():
    traces = []
    for service in ["host-python", "host-java"]:
        traces.extend(fetch_traces(service))
    counts = defaultdict(lambda: {"internal": 0, "external": 0, "rounds": defaultdict(lambda: {"internal": 0, "external": 0})})
    for trace in traces:
        for span in trace.get("spans", []):
            tags = tag_dict(span)
            fn = tags.get("fra.function_name")
            inv = tags.get("fra.invocation_type")
            round_id = str(tags.get("fra.round_id", "unknown"))
            if fn and inv in ("internal", "external"):
                counts[fn][inv] += 1
                counts[fn]["rounds"][round_id][inv] += 1
    return counts

def strict_label(observed_ratio, threshold):
    return "misplaced" if observed_ratio >= threshold else "not_misplaced"

def truth_to_binary(truth):
    return "misplaced" if truth == "misplaced" else "not_misplaced"

def metrics(records, threshold):
    tp = fp = fn = 0
    for rec in records:
        pred = strict_label(rec["observed_ratio"], threshold)
        truth = truth_to_binary(rec["ground_truth"])
        if pred == "misplaced" and truth == "misplaced":
            tp += 1
        elif pred == "misplaced" and truth != "misplaced":
            fp += 1
        elif pred != "misplaced" and truth == "misplaced":
            fn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}

def metrics_per_round(functions, counts, threshold):
    round_ids = set()
    for fn in counts.values():
        round_ids.update(fn["rounds"].keys())
    f1s = []
    for rid in sorted(round_ids):
        records = []
        for f in functions:
            c = counts[f["name"]]["rounds"].get(rid, {"internal": 0, "external": 0})
            total = c["internal"] + c["external"]
            ratio = c["external"] / total if total else 0.0
            records.append({"ground_truth": f["ground_truth"], "observed_ratio": ratio})
        f1s.append(metrics(records, threshold)["f1"])
    return f1s

def main():
    functions = load_config()
    counts = collect_counts()
    records = []
    for f in functions:
        c = counts[f["name"]]
        total = c["internal"] + c["external"]
        ratio = c["external"] / total if total else 0.0
        records.append({
            "name": f["name"],
            "service": f["host_service"],
            "ground_truth": f["ground_truth"],
            "target_ratio": f["external_ratio"],
            "internal": c["internal"],
            "external": c["external"],
            "observed_ratio": ratio
        })

    print("\nPer-function summary")
    print("name,service,ground_truth,target_ratio,internal,external,observed_ratio")
    for r in records:
        print(f'{r["name"]},{r["service"]},{r["ground_truth"]},{r["target_ratio"]:.2f},{r["internal"]},{r["external"]},{r["observed_ratio"]:.3f}')

    print("\nThreshold summary")
    print("threshold,tp,fp,fn,precision,recall,f1,f1_stddev")
    for th in THRESHOLDS:
        m = metrics(records, th)
        round_f1s = metrics_per_round(functions, counts, th)
        stddev = statistics.pstdev(round_f1s) if len(round_f1s) > 1 else 0.0
        print(f"{int(th*100)}%,{m['tp']},{m['fp']},{m['fn']},{m['precision']:.3f},{m['recall']:.3f},{m['f1']:.3f},{stddev:.3f}")

if __name__ == "__main__":
    main()
