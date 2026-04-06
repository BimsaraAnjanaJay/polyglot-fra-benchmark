import "./instrumentation.js";
import express from "express";
import { trace } from "@opentelemetry/api";

const app = express();
app.use(express.json());
const tracer = trace.getTracer("internal-node");

app.post("/generate-internal", async (req, res) => {
  const { functionName, count, roundId } = req.body;
  for (let i = 0; i < count; i++) {
    await tracer.startActiveSpan("internal-node.generate", async span => {
      try {
        span.setAttribute("fra.function_name", functionName);
        span.setAttribute("fra.round_id", String(roundId));
        await fetch(`${process.env.HOST_JAVA_URL}/functions/${functionName}`, {
          headers: {
            "x-fra-source": "internal",
            "x-round-id": String(roundId),
            "x-caller-service": "internal-node"
          }
        });
        await new Promise(r => setTimeout(r, Math.floor(Math.random() * 10)));
      } finally {
        span.end();
      }
    });
  }
  res.json({ ok: true, count });
});

app.get("/health", (_, res) => res.json({ status: "ok", service: "internal-node" }));

app.listen(process.env.PORT || 8004, () => {
  console.log(`internal-node listening on ${process.env.PORT || 8004}`);
});
