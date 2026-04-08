# DevOps Project

A containerised microservices application with a fully automated CI/CD pipeline built on GitLab CI. Services are built, tested, packaged into Docker images, smoke tested, and deployed to a remote server via SSH — all on push.

---

## Architecture

The system is composed of six independently containerised services:

| Service | Description |
|---|---|
| **gateway** | Entry point for all traffic, routes to api_v1 or api_v2 (ports 8198 / 8199) |
| **api_v1** | Version 1 of the backend API (Service1) |
| **api_v2** | Version 2 of the backend API (Service1, alternate branch) |
| **service2** | Supporting backend service (port 8300) |
| **storage** | Persistent data store with a named volume (port 8200) |
| **monitoring** | System monitoring service with Docker socket access (port 8400) |

The two API versions (`api_v1` / `api_v2`) are built from different branches (`project1.0` / `project1.1`) of the same service, allowing parallel versioning behind a single gateway.

---

## Tech Stack

| Category | Technology |
|---|---|
| Languages | Python, JavaScript, C++, HTML, Shell |
| Containerisation | Docker, Docker Compose |
| Container Registry | Harbor |
| CI/CD | GitLab CI |
| Deployment | SSH + rsync to remote server |

---

## Project Structure

```
devOps_project/
├── gateway/               # API gateway service
├── service1/              # Versioned API backend (v1 / v2)
├── service2/              # Supporting backend service
├── storage/               # Persistent storage service
├── monitoring/            # Monitoring service
├── tests/                 # Test scripts
├── docker-compose.yaml    # Production Compose file (uses Harbor images)
├── docker-compose-dev.yaml# Local development Compose file
├── .gitlab-ci.yml         # Full CI/CD pipeline definition
├── EndReport.pdf          # Project end report
├── test_gateway.bat        # Manual gateway test script (Windows)
└── vstorage               # Volume storage reference
```

---

## CI/CD Pipeline

The GitLab CI pipeline runs on pushes to the `project1.0` and `project1.1` branches and consists of five stages:

```
build → test → package → smoketest → deploy
```

**build** — Copies service source files into build artifacts.

**test** — Validates that build artifacts exist and are complete.

**package** — Builds Docker images for all services and pushes them to a Harbor container registry. The correct API version image (`api_v1` or `api_v2`) is built based on the active branch.

**smoketest** — Spins up the full stack with Docker Compose and runs HTTP checks against the gateway to verify the system starts correctly.

**deploy** — SSHes into the remote production server, pulls the latest images from Harbor, and restarts the stack with `docker compose up -d`.

---

## Running Locally (Development)

```bash
docker compose -f docker-compose-dev.yaml up
```

| Service | URL |
|---|---|
| Gateway | http://localhost:8198 |
| Gateway (alt) | http://localhost:8199 |
| Monitoring | http://localhost:8400 |

---

## Running in Production

Production deployments are handled automatically by the CI/CD pipeline. To run manually on a server with Docker installed:

1. Set the required environment variables:

```env
HARBOR_REGISTRY=your.harbor.registry
HARBOR_PROJECT=your-project
IMAGE_TAG=project1.0
```

2. Pull and start:

```bash
docker compose pull
docker compose up -d
```

---

## Required CI/CD Variables

Set these as protected variables in GitLab CI settings:

| Variable | Description |
|---|---|
| `HARBOR_REGISTRY` | Harbor registry hostname |
| `HARBOR_PROJECT` | Harbor project name |
| `HARBOR_USER` | Harbor login username |
| `HARBOR_PASS` | Harbor login password |
| `SERVER_USER` | SSH user on the deployment server |
| `SERVER_IP` | IP address of the deployment server |
| `SSH_PRIVKEY_B64` | Base64-encoded SSH private key for deployment |

---

## Documentation

See `EndReport.pdf` for the full project report.

---
