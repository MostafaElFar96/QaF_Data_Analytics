# Docker + PostgreSQL

The Sanad database used in Classes 2–4. From the repo folder:

```bash
python data/generate_sanad_data.py      # creates data/sanad/*.csv first
cd docker
docker compose up -d                    # first start runs init/01_load_sanad.sql (1-2 minutes)
docker ps
```

Connection: host `localhost`, port `5432`, database / user / password `sanad`.

- Reset everything (e.g. after regenerating the data): `docker compose down -v` then `docker compose up -d`
- Stop without losing data: `docker compose stop`
- Open a SQL prompt inside the container: `docker compose exec db psql -U sanad`
