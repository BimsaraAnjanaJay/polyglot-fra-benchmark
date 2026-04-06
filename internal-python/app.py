import os
import random
import time

import requests
from fastapi import FastAPI
from pydantic import BaseModel
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

resource = Resource.create({SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", "internal-python")})
provider = TracerProvider(resource=resource)
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") + "/v1/traces")))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("internal-python")

HOST_PYTHON_URL = os.getenv("HOST_PYTHON_URL")
app = FastAPI()

class InternalRequest(BaseModel):
    functionName: str
    hostService: str
    count: int
    roundId: str

@app.post("/generate-internal")
def generate_internal(req: InternalRequest):
    for _ in range(req.count):
        with tracer.start_as_current_span("internal-python.generate") as span:
            span.set_attribute("fra.function_name", req.functionName)
            span.set_attribute("fra.round_id", req.roundId)
            requests.get(
                f"{HOST_PYTHON_URL}/functions/{req.functionName}",
                headers={
                    "x-fra-source": "internal",
                    "x-round-id": str(req.roundId),
                    "x-caller-service": "internal-python"
                },
                timeout=5
            )
            time.sleep(random.uniform(0.001, 0.01))
    return {"ok": True, "count": req.count}

@app.get("/health")
def health():
    return {"status": "ok", "service": "internal-python"}
