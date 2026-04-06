# Polyglot FRA Benchmark V2

This is a controlled polyglot microservice benchmark for calibrating thresholds in a Function Relocation Analyzer (FRA).

## Services

- `gateway-node` - external traffic generator and round orchestrator
- `host-python` - Python host service that exposes benchmark functions
- `host-java` - Java host service that exposes benchmark functions
- `internal-python` - internal traffic generator for `host-python`
- `internal-node` - internal traffic generator for `host-java`
- `otel-collector` - receives OTLP traces and forwards them to Jaeger
- `jaeger` - trace storage and UI

## Benchmark design

- 50 benchmark functions
- 10 ratio groups: 20, 30, 40, 50, 60, 65, 70, 75, 80, 100
- 5 functions per ratio group
- 5 repeated rounds by default
- round variability:
  - shuffled call order
  - timing jitter
  - volume variation (+/- 10%)
  - synthetic noise endpoints

## Run

```bash
docker compose up --build
```

Start an experiment:

```bash
curl -X POST http://localhost:3000/run-experiment   -H "Content-Type: application/json"   -d '{"rounds":5,"sleep_between_rounds_ms":1000}'
```

Quick single round:

```bash
curl -X POST http://localhost:3000/run-round
```

Jaeger UI:

- <http://localhost:16686>

Analyze results:

```bash
python analyzer.py
```

## Notes

This is a thesis-oriented benchmark starter. It is intentionally synthetic and controlled. It is not a production framework.

## Output from analyzer

The analyzer computes:

- observed internal calls
- observed external calls
- observed external ratio
- strict threshold evaluation
- ground-truth evaluation
- average precision, recall, F1 across thresholds
- F1 standard deviation across rounds (best-effort using round tags)
