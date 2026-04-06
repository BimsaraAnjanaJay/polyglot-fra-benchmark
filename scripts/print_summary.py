import json
from pathlib import Path
cfg = json.loads(Path("benchmark/functions.json").read_text())["functions"]
by_host = {}
for f in cfg:
    by_host.setdefault(f["host_service"], 0)
    by_host[f["host_service"]] += 1
print("Functions per host:", by_host)
