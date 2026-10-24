# SpoofSky Security Notes

## Current posture

No application code, credentials, network service, or database exists yet. These notes define requirements for the first implementation; they are not a claim that the eventual application is completely secure.

## Local prototype assumptions

- Bind services to localhost by default.
- Do not commit API keys, tokens, connection strings, or private datasets.
- Keep local configuration in ignored files and provide redacted examples only.
- Do not expose the development API to the public internet.
- Treat all imported observations and source metadata as untrusted input.

## Required controls before external exposure

- Strict Pydantic validation for request bodies, query parameters, coordinates, timestamps, pagination, and uploaded/imported data.
- Parameterized database access and least-privilege database roles if PostgreSQL is added.
- Explicit CORS allowlists; no wildcard origin with credentials.
- Request-size, page-size, execution-time, and resource limits to reduce exhaustion risk.
- Safe error responses that do not expose stack traces, filesystem paths, credentials, or provider responses unnecessarily.
- SSRF protections if users can submit source URLs: allowlisted schemes/hosts, blocked private/link-local ranges, bounded redirects, and timeouts.
- Authentication and server-side authorization before multi-user or public deployment; do not add fake authentication.
- CSRF protection where cookie-based browser sessions are used.
- Content Security Policy and output encoding for any user-controlled text rendered by the UI.
- Dependency and container scanning where those artifacts are introduced.
- Audit-friendly logs that record ingestion/detection decisions without secrets or unnecessary sensitive payloads.
- HTTPS and secret rotation in production.

## Data integrity and trust

- Preserve raw observations separately from normalized/derived records.
- Record source, acquisition time, processing version, and provenance on derived results.
- Never silently substitute simulated data after real-source failure.
- Treat detector output as an inference; require independent evidence before using “verified incident”.
