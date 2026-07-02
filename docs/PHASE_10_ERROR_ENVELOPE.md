# RailYatra Phase 10 Error Envelope

Status: ADDED

Goal:
Give backend API errors a standard response format.

Standard error response:

```json
{
  "ok": false,
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "status_code": 422,
    "path": "/feedback",
    "details": [],
    "timestamp": "UTC timestamp"
  }
}
```

Covered error types:

- HTTP errors
- Request validation errors
- Unexpected internal errors

Smoke script:

- scripts/smoke_phase10_error_envelope.py

Next:
Deploy to Render, then run the same smoke script against the deployed backend.
