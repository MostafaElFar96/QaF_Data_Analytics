# QaF Data Analytics — Module 4 practice materials

Everything students and instructors need to run the Module 4 code (Classes 1–4) on the fictional **Sanad Distribution** case.

## Notebooks (Google Colab or VS Code)

| Class | Notebook | Open in Colab |
|---|---|---|
| 1 — Framing the problem | `notebooks/Class_1_Framing.ipynb` | [Open](https://colab.research.google.com/github/MostafaElFar96/QaF_Data_Analytics/blob/main/notebooks/Class_1_Framing.ipynb) |
| 2 — Internal data & feasibility | `notebooks/Class_2_Internal_Data.ipynb` | [Open](https://colab.research.google.com/github/MostafaElFar96/QaF_Data_Analytics/blob/main/notebooks/Class_2_Internal_Data.ipynb) |
| 3 — External data (scraping, APIs) | `notebooks/Class_3_External_Data.ipynb` | [Open](https://colab.research.google.com/github/MostafaElFar96/QaF_Data_Analytics/blob/main/notebooks/Class_3_External_Data.ipynb) |
| 4 — Joins, aggregation & visuals | `notebooks/Class_4_Joins_and_Visuals.ipynb` | [Open](https://colab.research.google.com/github/MostafaElFar96/QaF_Data_Analytics/blob/main/notebooks/Class_4_Joins_and_Visuals.ipynb) |

Each notebook sets itself up: it clones this repo (in Colab), generates the dataset, and loads it into **DuckDB** — a database inside Python, so no Docker is needed. The SQL is the same as in the videos.

**VS Code:** clone the repo, open a notebook, pick a Python 3 kernel, run top to bottom. To use the real Docker + PostgreSQL setup from Class 2, see [`docker/README.md`](docker/README.md).

## Data

- `data/generate_sanad_data.py` — builds Sanad's internal tables (areas, retailers, warehouses, orders, deliveries, stock) and the Class 3–4 reference data (candidate_sites, drive_times, fsq_places_sample). Fixed seed: everyone gets identical data.
- `data/check_script_numbers.py` — checks the generated data against every figure quoted in the course videos.

```bash
python data/generate_sanad_data.py      # writes data/sanad/*.csv
python data/check_script_numbers.py     # 38/38 figures should match
```

All data is synthetic. `fsq_places_sample` imitates the shape of Foursquare's open data but contains no real Foursquare records.

## Sandbox Warehouse Listings (practice scraping site)

A fictional warehouse-listings website for Class 3, served by GitHub Pages from this repo's root:
https://mostafaelfar96.github.io/QaF_Data_Analytics/

- Listings: `warehouses/page-1.html` … `page-5.html` (37 listings)
- `robots.txt`: disallows `/contacts/`, asks for a 2-second crawl delay

Run it locally if the live site is unavailable: `python -m http.server 8000` in the repo folder, then use `BASE = "http://localhost:8000"`.
