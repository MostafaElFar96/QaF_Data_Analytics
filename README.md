# QaF Data Analytics — Module 4 practice materials

Everything needed to run the Module 4 code (Classes 1–4) on the fictional **Sanad Distribution** case.
The workflow is **VS Code + Docker**: the data lives in a PostgreSQL database running in Docker, and each class has a Jupyter notebook you run in VS Code.

## One-time setup

**Install:** [VS Code](https://code.visualstudio.com/) (with the Python and Jupyter extensions — VS Code suggests them when you open the folder), [Docker Desktop](https://www.docker.com/products/docker-desktop/), [Python 3.10+](https://www.python.org/downloads/) and [Git](https://git-scm.com/).

Then, in a terminal:

```bash
git clone https://github.com/MostafaElFar96/QaF_Data_Analytics
cd QaF_Data_Analytics
code .                                  # opens the folder in VS Code
```

In the VS Code terminal (**Terminal → New Terminal**):

```bash
python -m venv .venv
# activate it:  Windows: .venv\Scripts\activate    macOS / Linux: source .venv/bin/activate
pip install -r requirements.txt
python data/generate_sanad_data.py      # creates data/sanad/*.csv (~15 s, identical for everyone)
cd docker
docker compose up -d                    # first start loads the data into PostgreSQL (1-2 min)
docker ps                               # the "db" container should be running
```

Database connection: host `localhost`, port `5432`, database / user / password `sanad`.

## Notebooks

Open a notebook in VS Code, choose the `.venv` kernel (top-right **Select Kernel**), and run the cells top to bottom.

| Class | Notebook | Needs Docker |
|---|---|---|
| 1 — Framing the problem | `notebooks/Class_1_Framing.ipynb` | No |
| 2 — Internal data & feasibility | `notebooks/Class_2_Internal_Data.ipynb` | Yes |
| 3 — External data (scraping, APIs) | `notebooks/Class_3_External_Data.ipynb` | Yes |
| 4 — Joins, aggregation & visuals | `notebooks/Class_4_Joins_and_Visuals.ipynb` | Yes |

Class 3 also needs internet (the practice site, optional openrouteservice key, Overpass). If the practice site is unreachable, the notebook serves the same pages from this repo.

## Troubleshooting

| Problem | Fix |
|---|---|
| `port 5432 is already allocated` | Another PostgreSQL is running. In `docker/docker-compose.yml` change to `"5433:5432"` and set `SANAD_DB_URL=postgresql+psycopg2://sanad:sanad@localhost:5433/sanad` |
| `Cannot connect to the Docker daemon` | Open Docker Desktop and wait until it says it is running |
| Tables are empty | The container started before the data was generated: `python data/generate_sanad_data.py`, then in `docker/`: `docker compose down -v` and `docker compose up -d` |
| `ModuleNotFoundError` in a notebook | Select the `.venv` kernel, or run `pip install -r requirements.txt` with `.venv` activated |

## Data

- `data/generate_sanad_data.py` — builds Sanad's internal tables (areas, retailers, warehouses, orders, deliveries, stock) and the Class 3–4 reference data (candidate_sites, drive_times, fsq_places_sample). Fixed seed: everyone gets identical data.
- `data/check_script_numbers.py` — checks the generated data against every figure quoted in the course videos (`python data/check_script_numbers.py` → 38/38).
- `docker/` — PostgreSQL 16 compose file and the load script that runs on first start.

All data is synthetic. `fsq_places_sample` imitates the shape of Foursquare's open data but contains no real Foursquare records.

## Sandbox Warehouse Listings (practice scraping site)

A fictional warehouse-listings website for Class 3, served by GitHub Pages from this repo's root:
https://mostafaelfar96.github.io/QaF_Data_Analytics/

- Listings: `warehouses/page-1.html` … `page-5.html` (37 listings)
- `robots.txt`: disallows `/contacts/`, asks for a 2-second crawl delay
