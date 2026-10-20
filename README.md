# Assignment 3 - Secure, scalable Project Tracker

## Requirement checklist
- [x] Three Flask/Gunicorn backends behind Nginx, each with a health check
- [x] Instance identity endpoint for round-robin verification
- [x] Docker benchmark, failover, and Trivy evidence scripts
- [x] bcrypt password hashes, TOTP login, session token, and supervisor-only mutations
- [x] Non-root Alpine image and upstream retry configuration
- [x] Architecture diagram, tests, report, and evidence folder

## Run safely
1. Copy `.env.example` to `.env`, add the Neon connection string and a long random `SECRET_KEY`; do not commit it.
2. `docker compose up --build -d`
3. Seed the first privileged user once: `docker compose exec backend1 sh -lc 'ADMIN_USERNAME=supervisor ADMIN_PASSWORD=<strong-password> flask --app app seed-supervisor'`. Store the printed TOTP secret in an authenticator app, then delete it from terminal history.
4. Visit `http://localhost:8080/health/instance` and repeat it to show all container hostnames.

## Evidence commands
Use `scripts/benchmark.sh`, `scripts/failover.sh`, and `scripts/scan-image.sh`. Their raw outputs are saved under `evidence/`; only completed, real runs should be reported as measurements.

## Neon DNS diagnosis
The service names `backend1`, `backend2`, and `backend3` resolve only on Docker's internal network. Neon must be addressed by its public hostname in `DATABASE_URL`; do not replace it with a Docker service name. Test DNS from a running backend with `getent hosts <neon-host>` and confirm outbound TCP/5432 plus `sslmode=require`. The compose file passes `.env` unchanged to each backend and never exposes it to Nginx.
