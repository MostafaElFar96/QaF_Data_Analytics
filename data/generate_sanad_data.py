"""
Generate the fictional "Sanad Distribution" dataset used in Module 4 (Classes 2-4).

Same seed -> same data for everyone. Run:
    python data/generate_sanad_data.py            # writes CSVs to data/sanad/
    python data/generate_sanad_data.py --out DIR

Tables (internal, Class 2): areas, retailers, warehouses, orders, deliveries, stock
Reference data (external, Classes 3-4): candidate_sites, drive_times, fsq_places_sample

All data is synthetic. "fsq_places_sample" imitates the shape of Foursquare open data
but contains NO real Foursquare records.
"""
import argparse
import os

import numpy as np
import pandas as pd

SEED = 2026
MONTHS = pd.period_range("2025-05", "2026-10", freq="M")          # 18 months
DAYS_PER_MONTH = 26
RENAME_MONTH = pd.Period("2026-02", "M")                            # "Tagamoa 5" -> "Fifth Settlement"

# ---------------------------------------------------------------- areas
# New Cairo cluster: share of cluster demand, cost per drop, on-time anchor, centroid
NC = [
    # name,             share, cost, lat,     lon
    ("Fifth Settlement", .14, 178, 30.0130, 31.4500),
    ("Madinaty",         .14, 191, 30.0950, 31.6350),
    ("Shorouk",          .12, 186, 30.1450, 31.6100),
    ("First Settlement", .12, 162, 30.0470, 31.4200),
    ("Third Settlement", .07, 168, 29.9950, 31.4700),
    ("El Rehab",         .09, 165, 30.0600, 31.4950),
    ("Katameya",         .10, 158, 29.9900, 31.4050),
    ("New Heliopolis",   .06, 172, 30.1200, 31.5600),
    ("Mostakbal City",   .08, 184, 30.0300, 31.5500),
    ("Badr City",        .08, 189, 30.1350, 31.7250),
]
# Other areas named in the scripts (cost per drop targets)
NAMED = [
    ("Nasr City", "East", 121, 30.0560, 31.3450),
    ("Heliopolis", "East", 115, 30.0900, 31.3300),
    ("Giza", "West", 112, 29.9900, 31.1500),
    ("Downtown", "Central", 109, 30.0440, 31.2400),
    ("Sheikh Zayed", "West", 104, 30.0400, 30.9800),
    ("6th of October", "West", 98, 29.9300, 30.9300),
    ("Obour", "East", 108, 30.2300, 31.4800),
    ("Maadi", "Central", 112, 29.9600, 31.2600),
    ("Shubra", "Central", 106, 30.0900, 31.2450),
    ("Hadayek October", "West", 101, 29.9100, 31.0300),
]
NC_TARGET_MONTHLY = {  # EGP millions, from the Class 2 chart (others interpolated)
    "2025-05": 28.0, "2025-08": 30.1, "2025-11": 32.6, "2026-02": 35.0,
    "2026-05": 37.8, "2026-08": 39.9, "2026-10": 41.0,
}


def build_areas(rng):
    rows = []
    aid = 1
    for name, share, cost, lat, lon in NC:
        rows.append(dict(area_id=aid, area_name=name, zone="East", cluster="New Cairo",
                         served_by_wh=1, nc_share=share, cost_target=cost, lat=lat, lon=lon))
        aid += 1
    # the pre-rename name of Fifth Settlement (used by retailer records created before Feb 2026)
    rows.append(dict(area_id=aid, area_name="Tagamoa 5", zone="East", cluster="New Cairo",
                     served_by_wh=1, nc_share=0, cost_target=178, lat=30.0130, lon=31.4500))
    TAGAMOA_ID = aid
    aid += 1
    for name, zone, cost, lat, lon in NAMED:
        rows.append(dict(area_id=aid, area_name=name, zone=zone, cluster=None,
                         served_by_wh=1 if zone == "East" else 2, nc_share=0, cost_target=cost, lat=lat, lon=lon))
        aid += 1
    # filler districts to reach 60 areas; costs chosen so the unweighted area mean is 118
    n_fill = 60 - len(rows)
    named_costs = [r["cost_target"] for r in rows if r["area_name"] != "Tagamoa 5"]
    total_needed = 118 * 59 - sum(named_costs)          # 59 distinct areas (Tagamoa 5 = Fifth Settlement)
    fill_costs = rng.normal(total_needed / n_fill, 6, n_fill)
    fill_costs += (total_needed - fill_costs.sum()) / n_fill
    for i in range(n_fill):
        zone = ["East", "West", "Central"][i % 3]
        base = {"East": (30.08, 31.35), "West": (30.00, 31.05), "Central": (30.05, 31.24)}[zone]
        rows.append(dict(area_id=aid, area_name=f"District {i + 1:02d}", zone=zone, cluster=None,
                         served_by_wh=1 if zone == "East" else 2, nc_share=0,
                         cost_target=round(float(fill_costs[i]), 1),
                         lat=base[0] + rng.uniform(-.06, .06), lon=base[1] + rng.uniform(-.06, .06)))
        aid += 1
    return pd.DataFrame(rows), TAGAMOA_ID


def nc_monthly_targets():
    s = pd.Series({pd.Period(k, "M"): v for k, v in NC_TARGET_MONTHLY.items()})
    s = s.reindex(MONTHS).astype(float).interpolate()
    return s * 1e6


def main(out):
    rng = np.random.default_rng(SEED)
    os.makedirs(out, exist_ok=True)
    areas, TAGAMOA_ID = build_areas(rng)
    fifth_id = int(areas.loc[areas.area_name == "Fifth Settlement", "area_id"].iloc[0])

    # ------------------------------------------------------------ retailers (4,000 rows)
    nc_ids = areas.loc[areas.cluster.eq("New Cairo") & areas.area_id.ne(TAGAMOA_ID), "area_id"].tolist()
    nc_counts = {a: int(round(800 * s)) for a, s in zip(nc_ids, [x[1] for x in NC])}
    other_ids = areas.loc[areas.cluster.isna(), "area_id"].tolist()
    n_fifth_dup = nc_counts[fifth_id]                     # re-registered in Feb 2026 (system migration)
    n_other = 4000 - sum(nc_counts.values()) - n_fifth_dup
    other_counts = rng.multinomial(n_other, np.ones(len(other_ids)) / len(other_ids))
    r_rows = []
    rid = 100001
    area_lookup = areas.set_index("area_id")
    def add(area_id, n, era):
        nonlocal rid
        lat0, lon0 = area_lookup.loc[area_id, ["lat", "lon"]]
        for _ in range(n):
            r_rows.append(dict(retailer_id=rid, area_id=area_id,
                               segment=rng.choice(["kiosk", "minimarket"], p=[.6, .4]),
                               lat=round(lat0 + rng.normal(0, .006), 6), lon=round(lon0 + rng.normal(0, .006), 6),
                               era=era))
            rid += 1
    for a in nc_ids:
        if a == fifth_id:
            add(TAGAMOA_ID, nc_counts[a], "old")         # pre-Feb 2026 records under the old name
            add(fifth_id, nc_counts[a], "new")           # same shops, new records after the migration
        else:
            add(a, nc_counts[a], "all")
    for a, n in zip(other_ids, other_counts):
        add(a, int(n), "all")
    retailers = pd.DataFrame(r_rows)
    # copy coordinates of the old Fifth Settlement records onto the new ones (same physical shops)
    old = retailers.index[retailers.era.eq("old")]; new = retailers.index[retailers.era.eq("new")]
    retailers.loc[new, ["lat", "lon"]] = retailers.loc[old, ["lat", "lon"]].values
    # key accounts: 200 rows, 80 of them in New Cairo
    nc_mask = retailers.area_id.isin(nc_ids + [TAGAMOA_ID]) & retailers.era.ne("old")
    ka_nc = rng.choice(retailers.index[nc_mask], 80, replace=False)
    ka_other = rng.choice(retailers.index[~retailers.area_id.isin(nc_ids + [TAGAMOA_ID])], 120, replace=False)
    retailers["is_top200"] = False
    retailers.loc[np.r_[ka_nc, ka_other], "is_top200"] = True
    # old records of key-account shops are key accounts too
    ka_new_fifth = retailers.index[retailers.era.eq("new") & retailers.is_top200]
    retailers.loc[old[np.isin(new, ka_new_fifth)], "is_top200"] = True
    # exactly 212 retailers without coordinates
    miss = rng.choice(retailers.index, 212, replace=False)
    retailers.loc[miss, ["lat", "lon"]] = np.nan

    # ------------------------------------------------------------ warehouses
    warehouses = pd.DataFrame([
        dict(wh_id=1, name="Obour", lat=30.2280, lon=31.4790, monthly_rent_egp=300000, capacity_pallets=9000),
        dict(wh_id=2, name="6th of October", lat=29.9400, lon=30.9200, monthly_rent_egp=280000, capacity_pallets=8000),
    ])

    # ------------------------------------------------------------ deliveries + orders
    nc_target = nc_monthly_targets()
    rest_target = pd.Series(np.linspace(40e6, 44.8e6, len(MONTHS)), index=MONTHS)   # +12%
    VALUE_PER_DROP = {"nc": 3190.0, "rest": 3850.0}
    NC_SET = set(nc_ids + [TAGAMOA_ID])
    rest_weights = other_counts / other_counts.sum()

    d_cols = {k: [] for k in ["delivery_id", "order_id", "wh_id", "route_id", "order_date", "planned_date",
                              "area_id", "retailer_id", "value", "is_nc"]}
    did, oid = 5_000_001, 9_000_001
    for m in MONTHS:
        month_days = pd.date_range(m.start_time, m.end_time, freq="D")
        work_days = month_days[month_days.dayofweek != 4][:DAYS_PER_MONTH]   # Fridays off
        plan = []
        for a, s in zip(nc_ids, [x[1] for x in NC]):
            area_for_month = TAGAMOA_ID if (a == fifth_id and m < RENAME_MONTH) else a
            plan.append((area_for_month, nc_target[m] * s, "nc"))
        for a, w in zip(other_ids, rest_weights):
            plan.append((a, rest_target[m] * w, "rest"))
        for area_id, value, kind in plan:
            n = max(1, int(round(value / VALUE_PER_DROP[kind])))
            pool = retailers.index[retailers.area_id.eq(area_id)].to_numpy()
            rids = retailers.loc[rng.choice(pool, n), "retailer_id"].to_numpy()
            vals = rng.gamma(4.0, 1.0, n)
            vals = vals / vals.sum() * value                  # exact area-month value
            odates = rng.choice(work_days, n)
            d_cols["delivery_id"].append(np.arange(did, did + n)); did += n
            d_cols["order_id"].append(np.arange(oid, oid + n)); oid += n
            d_cols["wh_id"].append(np.full(n, int(area_lookup.loc[area_id, "served_by_wh"])))
            d_cols["route_id"].append(rng.integers(1, 120, n))
            d_cols["order_date"].append(odates)
            d_cols["planned_date"].append(odates)              # filled below
            d_cols["area_id"].append(np.full(n, area_id))
            d_cols["retailer_id"].append(rids)
            d_cols["value"].append(vals)
            d_cols["is_nc"].append(np.full(n, kind == "nc"))
    D = pd.DataFrame({k: np.concatenate(v) for k, v in d_cols.items()})
    D["order_date"] = pd.to_datetime(D.order_date)
    D = D.merge(retailers[["retailer_id", "is_top200"]], on="retailer_id", how="left")
    N = len(D)

    # promise: same-day for key accounts, next-day for everyone else
    D["planned_date"] = D.order_date + pd.to_timedelta(np.where(D.is_top200, 0, 1), unit="D")

    # status: exactly 92% delivered / 2% partial / 6% failed overall; failures higher in New Cairo
    status = np.array(["delivered"] * N, dtype=object)
    n_fail, n_part = int(round(.06 * N)), int(round(.02 * N))
    nc_idx, rest_idx = np.flatnonzero(D.is_nc), np.flatnonzero(~D.is_nc)
    n_fail_nc = int(round(.08 * len(nc_idx)))
    fail_idx = np.r_[rng.choice(nc_idx, n_fail_nc, replace=False),
                     rng.choice(rest_idx, n_fail - n_fail_nc, replace=False)]
    status[fail_idx] = "failed"
    remaining = np.setdiff1d(np.arange(N), fail_idx)
    part_idx = rng.choice(remaining, n_part, replace=False)
    status[part_idx] = "partial"
    D["status"] = status

    # cost per drop: area target with noise; failed stops cost 80%; exactly 9,800 failed stops without cost
    cost_target = D.area_id.map(area_lookup.cost_target).to_numpy(float)
    cost = cost_target * rng.lognormal(0, .18, N) / np.exp(.18 ** 2 / 2)
    cost = np.where(status == "failed", cost * .8, cost)
    # re-centre each area so its mean over recorded costs hits the target
    D["drop_cost_egp"] = cost
    fail_nc = np.intersect1d(fail_idx, nc_idx); fail_rest = np.intersect1d(fail_idx, rest_idx)
    null_idx = np.r_[rng.choice(fail_nc, 3600, replace=False), rng.choice(fail_rest, 9800 - 3600, replace=False)]
    D.loc[null_idx, "drop_cost_egp"] = np.nan
    means = D.groupby("area_id").drop_cost_egp.mean()
    D["drop_cost_egp"] = (D.drop_cost_egp * D.area_id.map(area_lookup.cost_target / means)).round(2)

    # delivered_at: on-time 81% in New Cairo, 93% elsewhere; key accounts in New Cairo get same-day 58%
    ontime_p = np.where(D.is_nc, .81, .93)
    on_time = rng.random(N) < ontime_p
    ka_nc_mask = (D.is_top200 & D.is_nc).to_numpy()
    on_time[ka_nc_mask] = rng.random(ka_nc_mask.sum()) < .58
    late_days = rng.integers(1, 3, N)
    deliv_date = D.planned_date + pd.to_timedelta(np.where(on_time, 0, late_days), unit="D")
    hours = pd.to_timedelta(rng.integers(8, 19, N), unit="h") + pd.to_timedelta(rng.integers(0, 60, N), unit="m")
    D["delivered_at"] = (deliv_date + hours).where(status != "failed")

    deliveries = D[["delivery_id", "order_id", "wh_id", "route_id", "planned_date", "delivered_at",
                    "status", "drop_cost_egp"]].copy()
    deliveries["planned_date"] = deliveries.planned_date.dt.date

    # order lines: ~3.75 lines per order, values sum to the order value
    lines_per = rng.integers(2, 6, N)                       # 2..5 -> mean 3.5
    extra = rng.random(N) < .25
    lines_per = lines_per + extra
    rep = np.repeat(np.arange(N), lines_per)
    w = rng.gamma(2.0, 1.0, len(rep))
    w_sum = np.bincount(rep, weights=w)
    line_val = w / w_sum[rep] * D.value.to_numpy()[rep]
    orders = pd.DataFrame({
        "order_id": D.order_id.to_numpy()[rep],
        "retailer_id": D.retailer_id.to_numpy()[rep],
        "order_date": D.order_date.dt.date.to_numpy()[rep],
        "sku_id": rng.integers(1, 461, len(rep)),
        "qty": rng.integers(1, 25, len(rep)),
        "value_egp": line_val.round(2),
    })

    # ------------------------------------------------------------ stock (2 x 460 SKUs x every day)
    days = pd.date_range(MONTHS[0].start_time, MONTHS[-1].end_time, freq="D")
    wh, sku, day = np.meshgrid([1, 2], np.arange(1, 461), np.arange(len(days)), indexing="ij")
    on_hand = rng.poisson(120, wh.size)
    stock = pd.DataFrame({"wh_id": wh.ravel(), "sku_id": sku.ravel(), "date": days[day.ravel()].date,
                          "on_hand": on_hand, "stockout_flag": on_hand < 95})
    stock.loc[stock.stockout_flag, "on_hand"] = 0

    # ------------------------------------------------------------ external reference data (Classes 3-4)
    sites = pd.DataFrame([
        ("A", "Logistics warehouse - Suez Road km 28", "Suez Road", 30.0870, 31.5310, 3200, 380000),
        ("B", "Industrial warehouse - Shorouk industrial zone", "Shorouk", 30.1550, 31.6200, 2800, 320000),
        ("C", "Prime warehouse - Katameya central", "Katameya", 29.9900, 31.4000, 2600, 470000),
        ("D", "Large warehouse - Badr City", "Badr City", 30.1350, 31.7300, 4000, 260000),
        ("E", "Warehouse - New Cairo investors' zone", "New Cairo", 30.0400, 31.4700, 3000, 440000),
        ("F", "Warehouse - Obour extension", "Obour", 30.2300, 31.5000, 3500, 250000),
        ("G", "Warehouse - Katameya south", "Katameya", 29.9700, 31.4200, 2700, 430000),
    ], columns=["site_id", "name", "area", "lat", "lon", "size_sqm", "rent_egp"])
    sites["hgv_access"] = True
    sites["industrial_zone"] = True
    sites["source"] = "sandbox-warehouse-listings"
    sites["retrieved_at"] = "2026-11-05"
    # which New Cairo areas each site does NOT reach within 45 min at 10 am
    uncovered = {
        "A": ["Katameya", "First Settlement"],
        "B": ["Katameya", "First Settlement", "Third Settlement"],
        "C": ["Badr City"],
        "D": ["Katameya", "First Settlement", "El Rehab", "Fifth Settlement"],
        "E": ["Shorouk"],
        "F": ["Katameya", "First Settlement", "Third Settlement", "Mostakbal City", "Badr City", "New Heliopolis"],
        "G": ["Badr City", "Mostakbal City"],
    }
    dt_rows = []
    for _, s in sites.iterrows():
        for _, a in areas.iterrows():                       # every area (incl. the old "Tagamoa 5" id)
            name = "Fifth Settlement" if a.area_id == TAGAMOA_ID else a.area_name
            if a.cluster == "New Cairo":
                far = name in uncovered[s.site_id]
                lo_hi = (48, 75)
                if far and s.site_id == "A":
                    lo_hi = (48, 58)    # reachable at 6 am (free-flow x 1.1 <= 45): A overtakes G off-peak
                if far and s.site_id == "G":
                    lo_hi = (62, 75)    # still beyond 45 min even at 6 am
                m10 = round(float(rng.uniform(*lo_hi) if far else rng.uniform(12, 44)), 1)
            else:
                m10 = round(float(rng.uniform(46, 110)), 1)  # outside New Cairo: always beyond 45 min
            dt_rows.append(dict(site_id=s.site_id, area_id=int(a.area_id),
                                minutes_free_flow=round(m10 / 1.45, 1), minutes_10am=m10))
    drive_times = pd.DataFrame(dt_rows)

    # Foursquare-style places sample: 600 grocery shops in New Cairo, 200 already served by Sanad
    unserved_per_area = {"Shorouk": 190, "Badr City": 30, "Mostakbal City": 30, "Madinaty": 40,
                         "Fifth Settlement": 30, "First Settlement": 20, "Third Settlement": 15,
                         "El Rehab": 15, "Katameya": 20, "New Heliopolis": 10}
    p_rows = []
    pid = 1
    nc_area_rows = areas[areas.area_name.isin(unserved_per_area)].set_index("area_name")
    shop_xy = retailers.loc[retailers.lat.notna(), ["lat", "lon"]].to_numpy()
    cent = areas[areas.cluster.eq("New Cairo") & areas.area_id.ne(TAGAMOA_ID)].set_index("area_name")[["lat", "lon"]]
    def km(a_lat, a_lon, b_lat, b_lon):
        return 111.0 * np.hypot(a_lat - b_lat, (a_lon - b_lon) * np.cos(np.radians(30.05)))
    for name, n in unserved_per_area.items():
        lat0, lon0 = nc_area_rows.loc[name, ["lat", "lon"]]
        made = 0
        while made < n:
            la, lo = lat0 + rng.normal(0, .006), lon0 + rng.normal(0, .006)
            if km(la, lo, shop_xy[:, 0], shop_xy[:, 1]).min() < 0.12:      # too close to a Sanad shop
                continue
            nearest = cent.index[np.argmin(km(la, lo, cent.lat.to_numpy(), cent.lon.to_numpy()))]
            if nearest != name:                                          # must fall in its own area
                continue
            p_rows.append(dict(fsq_place_id=f"sandbox_{pid:05d}", name=f"Market {pid:04d}",
                               category="Grocery Store / Supermarket",
                               latitude=round(la, 6), longitude=round(lo, 6)))
            pid += 1; made += 1
    served_pool = retailers[retailers.area_id.isin(nc_ids) & retailers.lat.notna()]
    served = served_pool.sample(200, random_state=SEED)
    for _, r in served.iterrows():
        p_rows.append(dict(fsq_place_id=f"sandbox_{pid:05d}", name=f"Market {pid:04d}",
                           category="Grocery Store / Supermarket",
                           latitude=round(r.lat + rng.normal(0, .00008), 6),
                           longitude=round(r.lon + rng.normal(0, .00008), 6)))
        pid += 1
    places = pd.DataFrame(p_rows)
    # make sure "unserved" places are not accidentally right on top of a Sanad shop
    # (checked in the notebook with a 50 m nearest-neighbour test)

    # ------------------------------------------------------------ write
    areas_out = areas[["area_id", "area_name", "zone", "cluster", "served_by_wh", "lat", "lon"]]
    retailers_out = retailers[["retailer_id", "area_id", "segment", "lat", "lon", "is_top200"]]
    for name, df in [("areas", areas_out), ("retailers", retailers_out), ("warehouses", warehouses),
                     ("orders", orders), ("deliveries", deliveries), ("stock", stock),
                     ("candidate_sites", sites), ("drive_times", drive_times),
                     ("fsq_places_sample", places)]:
        df.to_csv(os.path.join(out, f"{name}.csv"), index=False)
        print(f"{name:18s} {len(df):>9,} rows")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "sanad"))
    main(ap.parse_args().out)
