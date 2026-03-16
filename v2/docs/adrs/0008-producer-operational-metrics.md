## ADR 0008: Keep producer operational metrics light

## Context

• Needed enough producer metrics to support basic throughput and delivery visibility
• Risk of overengineering beyond portfolio and interview-defense scope
• Primary focus of project is downstream consumption, modeling, and reliability
• Hands-on operation clarified why production systems use deeper telemetry

## Decision

• Implement lightweight structured logging via stdout
• Prioritize delivery visibility (send success/failure + counts) over deep platform metrics
• Avoid external sinks and complex observability tooling

## Alternatives Considered

• Fixed window throughput metrics (e.g., 10-second rolling counts)
• JSONL event logging with detailed timestamps and counters
• Rejected to keep scope aligned with pipeline design focus rather than platform ops

## Tradeoffs

• Limited visibility into deeper producer bottlenecks
• Simpler system and clearer architectural defense
• Lower comprehension overhead during interviews
• Acceptable given project scale and throughput assumptions

## Future Revisit Trigger

• If producer becomes a scaling or reliability bottleneck
• If role scope shifts toward platform or Kafka operations ownership