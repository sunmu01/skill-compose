---
sidebar_position: 3
slug: /development-setup
---

# Development Setup

## Rebuild After Code Changes

When running with Docker, rebuild after modifying source code:

```bash
cd docker
./rebuild.sh          # Rebuild all services
./rebuild.sh api      # Backend only
./rebuild.sh web      # Frontend only
```

## Troubleshooting

### Port already in use

```bash
lsof -i :62600    # Check port 62600
lsof -i :62610    # Check port 62610
```

### Docker containers won't start

```bash
docker compose logs -f api    # View API logs
docker compose logs -f web    # View frontend logs
docker compose restart        # Restart all services
```

### Database connection failed

```bash
# Docker: check db container health
docker compose ps

# Local: verify PostgreSQL is running
psql -h localhost -U postgres -l
```
