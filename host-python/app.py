import json
import os
import random
import time
from pathlib import Path

from fastapi import FastAPI, Request
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

resource = Resource.create({SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", "host-python")})
provider = TracerProvider(resource=resource)
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") + "/v1/traces")))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("host-python")

app = FastAPI()
cfg = json.loads(Path(os.getenv("FUNCTIONS_CONFIG_PATH")).read_text())["functions"]
FUNCTIONS = {f["name"]: f for f in cfg if f["host_service"] == "host-python"}

@app.get("/functions/{name}")
async def invoke_function(name: str, request: Request):
    if name not in FUNCTIONS:
        return {"error": "unknown function", "name": name}
    invocation_type = "external" if request.headers.get("x-fra-source") == "external" else "internal"
    round_id = request.headers.get("x-round-id", "unknown")
    caller_service = request.headers.get("x-caller-service", "unknown")
    with tracer.start_as_current_span("host-python.function") as span:
        span.set_attribute("fra.function_name", name)
        span.set_attribute("fra.invocation_type", invocation_type)
        span.set_attribute("fra.host_service", "host-python")
        span.set_attribute("fra.round_id", round_id)
        span.set_attribute("fra.caller_service", caller_service)
        # small simulated work
        time.sleep(random.uniform(0.001, 0.01))
        return {"ok": True, "function": name, "invocation_type": invocation_type, "round_id": round_id}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "host-python"}

@app.get("/metrics-placeholder")
async def metrics_placeholder():
    return {"status": "noise"}
