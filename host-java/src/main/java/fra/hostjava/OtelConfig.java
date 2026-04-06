package fra.hostjava;

import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.exporter.otlp.trace.OtlpHttpSpanExporter;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.resources.Resource;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.export.BatchSpanProcessor;
import io.opentelemetry.semconv.ServiceAttributes;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OtelConfig {
    @Bean
    public OpenTelemetry openTelemetry(
            @Value("${otel.exporter.otlp.endpoint}") String endpoint,
            @Value("${otel.service.name}") String serviceName
    ) {
        OtlpHttpSpanExporter exporter = OtlpHttpSpanExporter.builder()
                .setEndpoint(endpoint + "/v1/traces")
                .build();

        Resource resource = Resource.getDefault().merge(
                Resource.create(Attributes.of(ServiceAttributes.SERVICE_NAME, serviceName))
        );

        SdkTracerProvider provider = SdkTracerProvider.builder()
                .setResource(resource)
                .addSpanProcessor(BatchSpanProcessor.builder(exporter).build())
                .build();

        return OpenTelemetrySdk.builder().setTracerProvider(provider).build();
    }
}
