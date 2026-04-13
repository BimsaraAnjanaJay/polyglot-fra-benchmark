package fra.hostjava;

import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
public class FunctionController {
    private final Tracer tracer;
    private final FunctionConfigLoader loader;

    public FunctionController(OpenTelemetry openTelemetry, FunctionConfigLoader loader) {
        this.tracer = openTelemetry.getTracer("host-java");
        this.loader = loader;
    }

    @GetMapping("/functions/{name}")
    public Map<String, Object> invoke(
            @PathVariable("name") String name,
            @RequestHeader(value = "x-fra-source", required = false) String source,
            @RequestHeader(value = "x-round-id", required = false) String roundId,
            @RequestHeader(value = "x-caller-service", required = false) String callerService
    ) throws Exception {
        Map<String, Object> out = new HashMap<>();
        if (!loader.exists(name)) {
            out.put("error", "unknown function");
            out.put("name", name);
            return out;
        }
        String invocationType = "external".equals(source) ? "external" : "internal";
        Span span = tracer.spanBuilder("host-java.function").startSpan();
        try {
            span.setAttribute("fra.function_name", name);
            span.setAttribute("fra.invocation_type", invocationType);
            span.setAttribute("fra.host_service", "host-java");
            span.setAttribute("fra.round_id", roundId == null ? "unknown" : roundId);
            span.setAttribute("fra.caller_service", callerService == null ? "unknown" : callerService);
            Thread.sleep((long)(Math.random() * 10));
            out.put("ok", true);
            out.put("function", name);
            out.put("invocation_type", invocationType);
            return out;
        } finally {
            span.end();
        }
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "ok", "service", "host-java");
    }

    @GetMapping("/metrics-placeholder")
    public Map<String, String> metricsPlaceholder() {
        return Map.of("status", "noise");
    }
}
