# Docker

The image packages the API and source only. It does not bake in datasets, models, reports,
`.env`, credentials, tests, or caches. Run the demo locally before Compose so the read-only
registry mount contains a champion.

```bash
docker build -t churnops-api:local .
docker compose up
```

For cloud use, store model artifacts outside the immutable image and fetch a reviewed champion
at startup or through a controlled sidecar/init mechanism.

