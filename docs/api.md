# API

Start the API after creating a champion:

```bash
uv run churnops demo
uv run uvicorn churnops.api:app --port 8000
```

Endpoints:

- `GET /health`: process health and champion availability.
- `GET /model/info`: champion metadata and evaluation metrics.
- `POST /predict`: one validated feature record.
- `POST /predict/batch`: up to 1,000 validated records.
- `GET /metrics/summary`: champion and latest monitoring reports.

Prediction responses include model version, threshold, probability, class, and request ID.
V1 intentionally has no authentication. A cloud version should validate OIDC/JWT identity at
the service or gateway and authorize callers by least privilege.

