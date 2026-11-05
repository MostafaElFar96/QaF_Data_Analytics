-- Runs automatically the first time the container starts. Generate the CSVs first:
--   python data/generate_sanad_data.py
CREATE TABLE areas (area_id INT PRIMARY KEY, area_name TEXT, zone TEXT, cluster TEXT, served_by_wh INT, lat DOUBLE PRECISION, lon DOUBLE PRECISION);
CREATE TABLE retailers (retailer_id INT PRIMARY KEY, area_id INT, segment TEXT, lat DOUBLE PRECISION, lon DOUBLE PRECISION, is_top200 BOOLEAN);
CREATE TABLE warehouses (wh_id INT PRIMARY KEY, name TEXT, lat DOUBLE PRECISION, lon DOUBLE PRECISION, monthly_rent_egp INT, capacity_pallets INT);
CREATE TABLE orders (order_id BIGINT, retailer_id INT, order_date DATE, sku_id INT, qty INT, value_egp NUMERIC(12,2));
CREATE TABLE deliveries (delivery_id BIGINT PRIMARY KEY, order_id BIGINT, wh_id INT, route_id INT, planned_date DATE, delivered_at TIMESTAMP, status TEXT, drop_cost_egp NUMERIC(10,2));
CREATE TABLE stock (wh_id INT, sku_id INT, date DATE, on_hand INT, stockout_flag BOOLEAN);
CREATE TABLE candidate_sites (site_id TEXT PRIMARY KEY, name TEXT, area TEXT, lat DOUBLE PRECISION, lon DOUBLE PRECISION, size_sqm INT, rent_egp INT, hgv_access BOOLEAN, industrial_zone BOOLEAN, source TEXT, retrieved_at DATE);
CREATE TABLE drive_times (site_id TEXT, area_id INT, minutes_free_flow NUMERIC(6,1), minutes_10am NUMERIC(6,1));
CREATE TABLE fsq_places_sample (fsq_place_id TEXT PRIMARY KEY, name TEXT, category TEXT, latitude DOUBLE PRECISION, longitude DOUBLE PRECISION);

COPY areas FROM '/data/areas.csv' CSV HEADER;
COPY retailers FROM '/data/retailers.csv' CSV HEADER;
COPY warehouses FROM '/data/warehouses.csv' CSV HEADER;
COPY orders FROM '/data/orders.csv' CSV HEADER;
COPY deliveries FROM '/data/deliveries.csv' CSV HEADER;
COPY stock FROM '/data/stock.csv' CSV HEADER;
COPY candidate_sites FROM '/data/candidate_sites.csv' CSV HEADER;
COPY drive_times FROM '/data/drive_times.csv' CSV HEADER;
COPY fsq_places_sample FROM '/data/fsq_places_sample.csv' CSV HEADER;
