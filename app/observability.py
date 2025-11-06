from dataclasses import dataclass
import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Tracer


@dataclass(frozen=True)
class TelemetryProviders:
    tracer_provider: TracerProvider


_TELEMETRY_PROVIDERS: Optional[TelemetryProviders] = None


def _build_resource(default_service_name: str) -> Resource:
    return Resource.create(
        {
            "service.name": os.getenv("OTEL_SERVICE_NAME", default_service_name),
            "service.version": os.getenv("OTEL_SERVICE_VERSION", "0.1.0"),
            "deployment.environment": os.getenv("OTEL_ENVIRONMENT", "local"),
        }
    )


def setup_telemetry(default_service_name: str) -> Optional[TelemetryProviders]:
    global _TELEMETRY_PROVIDERS
    if _TELEMETRY_PROVIDERS is not None:
        return _TELEMETRY_PROVIDERS

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return None

    tracer_provider = TracerProvider(resource=_build_resource(default_service_name))
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
    )
    trace.set_tracer_provider(tracer_provider)

    _TELEMETRY_PROVIDERS = TelemetryProviders(tracer_provider=tracer_provider)
    return _TELEMETRY_PROVIDERS


def get_tracer(instrumentation_name: str) -> Tracer:
    return trace.get_tracer(instrumentation_name)
