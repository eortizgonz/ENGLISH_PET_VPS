# Observability requirements
Production target must expose structured logs and metrics for login, API errors, database, audio, email, consent and authorization failures. Minimum metrics: request latency, error rate, active users, DB connections, CPU and memory. Alert target: sustained API error rate >5% must trigger an operational alert.
