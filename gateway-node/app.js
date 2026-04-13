import "./instrumentation.js";
import fs from "fs";
import express from "express";
import { trace } from "@opentelemetry/api";

const app = express();
app.use(express.json());

const tracer = trace.getTracer("gateway-node");
const cfg = JSON.parse(fs.readFileSync(process.env.FUNCTIONS_CONFIG_PATH, "utf-8")).functions;

const hostBase = {
  "host-python": process.env.HOST_PYTHON_URL,
  "host-java": process.env.HOST_JAVA_URL
};
const internalBase = {
  "internal-python": process.env.INTERNAL_PYTHON_URL,
  "internal-node": process.env.INTERNAL_NODE_URL
};

function shuffle(arr) {
  const copy = [...arr];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
function jitter(max=30) { return Math.floor(Math.random() * max); }

function buildRoundPlan(roundId) {
  return shuffle(cfg).map(f => {
    const variation = 1 + ((Math.random() * 0.2) - 0.1); // +/-10%
    const total = Math.max(20, Math.round(f.base_total_calls * variation));
    const externalCalls = Math.round(total * f.external_ratio);
    const internalCalls = Math.max(0, total - externalCalls);
    return { ...f, roundId, totalCalls: total, externalCalls, internalCalls };
  });
}

async function callUrl(url, headers = {}) {
  const res = await fetch(url, { headers });
  // On non-ok, return a partial error object rather than throwing — keeps the
  // experiment loop alive even when a downstream service is temporarily down.
  if (!res.ok) {
    console.warn(`[gateway] Downstream error ${res.status} ${url}`);
    return { _error: true, status: res.status, url };
  }
  return await res.json().catch(() => ({}));
}

async function runNoise(roundId) {
  const noiseUrls = [
    `${process.env.HOST_PYTHON_URL}/health`,
    `${process.env.HOST_PYTHON_URL}/metrics-placeholder`,
    `${process.env.HOST_JAVA_URL}/health`,
    `${process.env.HOST_JAVA_URL}/metrics-placeholder`
  ];
  for (const url of noiseUrls) {
    try { await callUrl(url, { "x-round-id": String(roundId), "x-noise": "true" }); } catch {}
  }
}

async function runPlan(plan, roundId) {
  // internal calls first via internal generators
  for (const item of plan) {
    const payload = {
      functionName: item.name,
      hostService: item.host_service,
      count: item.internalCalls,
      roundId
    };
    const url = `${internalBase[item.internal_generator]}/generate-internal`;
    await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    await sleep(jitter());
  }

  // external calls with shuffled order
  const expanded = [];
  for (const item of plan) {
    for (let i = 0; i < item.externalCalls; i++) expanded.push(item);
  }
  for (const item of shuffle(expanded)) {
    await tracer.startActiveSpan("gateway.external.invoke", async span => {
      try {
        // NOTE: do NOT set fra.function_name here — gateway-node is the external
        // caller, not the host. Setting it here creates ghost entries in the FRA
        // plugin attributed to gateway-node. The host service sets fra.function_name.
        span.setAttribute("fra.round_id", roundId);
        const url = `${hostBase[item.host_service]}${item.path}`;
        await callUrl(url, { "x-fra-source": "external", "x-round-id": String(roundId), "x-caller-service": "gateway-node" });
      } catch (err) {
        console.warn(`[gateway] External call failed for ${item.name}: ${err.message}`);
      } finally {
        span.end();
      }
    });
    await sleep(jitter());
  }

  await runNoise(roundId);

  return {
    roundId,
    functions: plan.length,
    totalExternalCalls: plan.reduce((a, x) => a + x.externalCalls, 0),
    totalInternalCalls: plan.reduce((a, x) => a + x.internalCalls, 0)
  };
}

app.post("/run-round", async (req, res) => {
  const roundId = req.body?.roundId ?? Date.now();
  const plan = buildRoundPlan(roundId);
  const summary = await runPlan(plan, roundId);
  res.json({ ok: true, summary, plan });
});

app.post("/run-experiment", async (req, res) => {
  const rounds = Number(req.body?.rounds || process.env.DEFAULT_ROUNDS || 5);
  const sleepBetween = Number(req.body?.sleep_between_rounds_ms || 1000);
  const summaries = [];
  for (let i = 1; i <= rounds; i++) {
    const roundId = `${Date.now()}-${i}`;
    const plan = buildRoundPlan(roundId);
    const summary = await runPlan(plan, roundId);
    summaries.push(summary);
    if (i < rounds) await sleep(sleepBetween);
  }
  res.json({ ok: true, rounds, summaries });
});

app.get("/config", (_, res) => res.json(cfg));
app.get("/health", (_, res) => res.json({ status: "ok", service: "gateway-node" }));

app.listen(process.env.PORT || 3000, () => {
  console.log(`gateway-node running on ${process.env.PORT || 3000}`);
});
