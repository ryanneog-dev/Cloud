# BACSE344 Digital Assignment 3 - Project Tracker

## Application and peak demand
This submission extends the Assignment 1 Project Tracker. A realistic peak is a factory shift-change: supervisors simultaneously check and update production-project tasks. The busiest API is `GET /api/projects`, which supplies the project board.

## Q1: scale without downtime
`docker-compose.yml` runs `backend1`, `backend2`, and `backend3` (Flask/Gunicorn on port 5000) behind Nginx on port 8080. `GET /health/instance` returns each hostname, so repeated requests provide direct distribution evidence. Nginx marks an upstream unavailable after one failed attempt for five seconds and retries a request against up to three peers. Compose health checks prevent Nginx starting until all backends are healthy.

Run `./scripts/benchmark.sh http://localhost:8080/api/projects 1` and then `... 3`, with ApacheBench's fixed `-n 1000 -c 25`. Paste the actual RPS and mean-time lines from `evidence/ab-*.txt` here; no results are claimed before execution. Run `scripts/failover.sh` while stopping `backend2`; compare ApacheBench's `Failed requests` result before and after the Nginx retry settings. This repository intentionally does not invent those values.

The diagram is `architecture.mmd`. The amber component is cloud bursting through Render autoscaling/edge capacity. It fits shift-change traffic because capacity can expand for short bursts while Neon remains the shared, durable data store.

## Q2: secure real-person data
The sensitive data are supervisor credentials and production-project information. Passwords are bcrypt salted hashes in `User.password_hash`; plaintext passwords are not stored. The test proves the persisted value differs from the supplied password and starts with bcrypt's `$2` marker. TOTP is verified by `pyotp` during login, and Flask's signed, HttpOnly session cookie is required for `POST`, `PUT`, and `DELETE` project APIs. Only `supervisor` and `admin` roles pass that check; an unauthenticated mutation returns HTTP 401 and a lower role returns HTTP 403.

`Dockerfile.baseline` preserves the pre-hardening scan target. The deployed `Dockerfile` uses Alpine and a dedicated non-root `app` user. `scripts/scan-image.sh` records Trivy HIGH/CRITICAL findings into `evidence/trivy-before.txt` and `evidence/trivy-after.txt`; these must be populated from a real scan before submission.

Threat agent 1: a former shift supervisor using a stolen password. Control: bcrypt slows offline guessing and the authenticator code blocks password-only login. GDPR applies because user accounts identify natural persons; Article 32 requires appropriate security of processing.

Threat agent 2: an unauthenticated internet attacker attempting to modify production tasks. Control: signed login session plus server-side RBAC rejects requests before mutation. GDPR applies because access-control failure could expose or alter personal data associated with staff; the same Article 32 security requirement applies.

## Reproducible evidence and limitations
Actual local unit-test evidence is in `evidence/local-test-results.txt`. Docker, Trivy, ApacheBench, and a reachable Neon credential were unavailable in this workspace, so the required container measurements and screenshots remain an explicit final run step, not a made-up claim. Capture: (1) three `/health/instance` responses, (2) database row before/after bcrypt migration using a disposable test account, (3) a 401 rejected mutation, (4) benchmark outputs, (5) failover outputs, and (6) both Trivy tables.

## Demo-video order (three minutes)
Show the diagram, `docker compose ps`, three health responses, 1-v-3 benchmark tables, stop one backend during a run, rejected mutation, authenticator login, bcrypt database column, and Trivy before/after output.
