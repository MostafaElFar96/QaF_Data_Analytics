# Docker + PostgreSQL (VS Code option)

The notebooks run on DuckDB by default (no Docker needed). To practise with the real PostgreSQL setup from Class 2:

```bash
# from the repo folder
python data/generate_sanad_data.py      # creates data/sanad/*.csv (~15 s)
cd docker
docker compose up -d                    # first start loads the CSVs (1-2 minutes)
docker ps
```

Connect from DBeaver or a notebook: host `localhost`, port `5432`, database / user / password `sanad`.

```python
from sqlalchemy import create_engine
import pandas as pd
engine = create_engine("postgresql+psycopg2://sanad:sanad@localhost:5432/sanad")
pd.read_sql("SELECT COUNT(*) FROM orders", engine)
```

Common errors: port 5432 in use -> change to `"5433:5432"`; Docker not running -> open Docker Desktop;
empty tables -> `docker compose down -v` then `docker compose up -d` (after generating the CSVs).
