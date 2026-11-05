"""Compare the generated data with every figure quoted in the Class 1-4 scripts."""
import os, sys
import duckdb
DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "sanad")
con = duckdb.connect()
for t in ["areas", "retailers", "warehouses", "orders", "deliveries", "stock",
          "candidate_sites", "drive_times", "fsq_places_sample"]:
    con.execute(f"CREATE VIEW {t} AS SELECT * FROM read_csv_auto('{DIR}/{t}.csv')")
q = lambda sql: con.execute(sql).fetchall()
rows = []
def chk(label, target, actual, ok):
    rows.append((label, target, actual, "OK" if ok else "CHECK"))

n = q("SELECT COUNT(*) FROM orders")[0][0]; chk("order lines", "~1.5M", f"{n:,}", 1.4e6 < n < 1.6e6)
n = q("SELECT COUNT(*) FROM deliveries")[0][0]; chk("deliveries", "~400K", f"{n:,}", 3.8e5 < n < 4.2e5)
n = q("SELECT COUNT(*) FROM stock")[0][0]; chk("stock rows", "~500K", f"{n:,}", 4.8e5 < n < 5.2e5)
n = q("SELECT COUNT(*) FROM retailers")[0][0]; chk("retailers", "4,000", f"{n:,}", n == 4000)
n = q("SELECT COUNT(*) FROM areas")[0][0]; chk("areas", "60", n, n == 60)
lo, hi = q("SELECT MIN(order_date), MAX(order_date) FROM orders")[0]; chk("date range", "May 2025 - Oct 2026", f"{lo} - {hi}", str(lo)[:7] == "2025-05" and str(hi)[:7] == "2026-10")
n = q("SELECT COUNT(*) FROM retailers WHERE lat IS NULL OR lon IS NULL")[0][0]; chk("retailers without coordinates", "212", n, n == 212)
st = dict(q("SELECT status, ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (), 1) FROM deliveries GROUP BY status"))
chk("status delivered/partial/failed", "92 / 2 / 6 %", f"{st['delivered']} / {st['partial']} / {st['failed']}", round(st['failed']) == 6 and round(st['partial']) == 2)
n = q("SELECT COUNT(*) FROM deliveries WHERE status='failed' AND drop_cost_egp IS NULL")[0][0]; chk("failed deliveries without cost", "~9,800", f"{n:,}", n == 9800)
share = q("SELECT ROUND(100.0*SUM(CASE WHEN drop_cost_egp IS NULL THEN 1 END)/COUNT(*),0) FROM deliveries WHERE status='failed'")[0][0]; chk("... share of all failed", "~40%", f"{share}%", 35 <= share <= 45)
n = q("""SELECT COUNT(*) FROM deliveries d JOIN (SELECT DISTINCT order_id, retailer_id FROM orders) o USING (order_id)
         JOIN retailers r USING (retailer_id) JOIN areas a USING (area_id)
         WHERE d.status='failed' AND d.drop_cost_egp IS NULL AND a.cluster='New Cairo'""")[0][0]
chk("... of which in New Cairo", "~3,600 (> one third)", f"{n:,}", n == 3600)
last_old = q("""SELECT MAX(DATE_TRUNC('month', o.order_date)) FROM orders o JOIN retailers r USING (retailer_id)
                JOIN areas a USING (area_id) WHERE a.area_name='Tagamoa 5'""")[0][0]
first_new = q("""SELECT MIN(DATE_TRUNC('month', o.order_date)) FROM orders o JOIN retailers r USING (retailer_id)
                 JOIN areas a USING (area_id) WHERE a.area_name='Fifth Settlement'""")[0][0]
chk("rename Tagamoa 5 -> Fifth Settlement", "Feb 2026", f"last old {str(last_old)[:7]}, first new {str(first_new)[:7]}", str(first_new)[:7] == "2026-02")
nc = dict(q("""SELECT STRFTIME(DATE_TRUNC('month', o.order_date), '%Y-%m'), SUM(o.value_egp)/1e6 FROM orders o
               JOIN retailers r USING (retailer_id) JOIN areas a USING (area_id) WHERE a.cluster='New Cairo' GROUP BY 1"""))
chk("New Cairo order value May 25 -> Oct 26", "28.0 -> 41.0 M", f"{nc['2025-05']:.1f} -> {nc['2026-10']:.1f} M", abs(nc['2025-05'] - 28) < .1 and abs(nc['2026-10'] - 41) < .1)
rest = dict(q("""SELECT STRFTIME(DATE_TRUNC('month', o.order_date), '%Y-%m'), SUM(o.value_egp) FROM orders o
                 JOIN retailers r USING (retailer_id) JOIN areas a USING (area_id) WHERE a.cluster IS NULL GROUP BY 1"""))
g = 100 * (rest['2026-10'] / rest['2025-05'] - 1); chk("rest of network growth", "+12%", f"+{g:.0f}%", abs(g - 12) < 1)
cpd = dict(q("""SELECT CASE WHEN a.area_name='Tagamoa 5' THEN 'Fifth Settlement' ELSE a.area_name END, AVG(d.drop_cost_egp)
                FROM deliveries d JOIN (SELECT DISTINCT order_id, retailer_id FROM orders) o USING (order_id)
                JOIN retailers r USING (retailer_id) JOIN areas a USING (area_id) GROUP BY 1"""))
for name, t in [("Madinaty", 191), ("Shorouk", 186), ("Fifth Settlement", 178), ("Nasr City", 121), ("Heliopolis", 115),
                ("Giza", 112), ("Downtown", 109), ("Sheikh Zayed", 104), ("6th of October", 98)]:
    chk(f"cost per drop - {name}", t, round(cpd[name]), abs(cpd[name] - t) < 1)
m = sum(cpd.values()) / len(cpd); chk("network average cost per drop (mean of areas)", 118, round(m, 1), abs(m - 118) < 1)
pct = dict(q("""SELECT COALESCE(a.cluster, 'Rest'), 100*SUM(d.drop_cost_egp)/SUM(o.v) FROM deliveries d
               JOIN (SELECT order_id, ANY_VALUE(retailer_id) retailer_id, SUM(value_egp) v FROM orders GROUP BY 1) o USING (order_id)
               JOIN retailers r USING (retailer_id) JOIN areas a USING (area_id) GROUP BY 1"""))
tot = q("""SELECT 100*SUM(d.drop_cost_egp)/SUM(o.v) FROM deliveries d JOIN (SELECT order_id, SUM(value_egp) v FROM orders GROUP BY 1) o USING (order_id)""")[0][0]
chk("delivery cost % of order value - New Cairo", "5.4%", f"{pct['New Cairo']:.1f}%", abs(pct['New Cairo'] - 5.4) < .2)
chk("delivery cost % of order value - network", "3.9%", f"{tot:.1f}%", abs(tot - 3.9) < .2)
ot = dict(q("""SELECT COALESCE(a.cluster,'Rest'), 100*AVG(CASE WHEN CAST(d.delivered_at AS DATE) <= d.planned_date THEN 1 ELSE 0 END)
              FROM deliveries d JOIN (SELECT DISTINCT order_id, retailer_id FROM orders) o USING (order_id)
              JOIN retailers r USING (retailer_id) JOIN areas a USING (area_id)
              WHERE d.status <> 'failed' AND NOT r.is_top200 GROUP BY 1"""))
chk("on-time next-day - New Cairo", "81%", f"{ot['New Cairo']:.0f}%", abs(ot['New Cairo'] - 81) < 1.5)
chk("on-time next-day - rest of network", "93%", f"{ot['Rest']:.0f}%", abs(ot['Rest'] - 93) < 1.5)
sd = q("""SELECT 100*AVG(CASE WHEN CAST(d.delivered_at AS DATE) = o.order_date THEN 1 ELSE 0 END)
          FROM deliveries d JOIN (SELECT DISTINCT order_id, retailer_id, order_date FROM orders) o USING (order_id)
          JOIN retailers r USING (retailer_id) JOIN areas a USING (area_id)
          WHERE d.status <> 'failed' AND r.is_top200 AND a.cluster='New Cairo'""")[0][0]
chk("same-day for key accounts - New Cairo", "58%", f"{sd:.0f}%", abs(sd - 58) < 3)
n = q("""SELECT COUNT(*) FROM retailers r JOIN areas a USING (area_id) WHERE a.cluster='New Cairo' AND a.area_name <> 'Tagamoa 5'""")[0][0]
chk("New Cairo shops", "~800", n, 780 <= n <= 820)
cov = dict(q("""WITH dmd AS (SELECT r.area_id, SUM(o.value_egp)/6 AS v FROM orders o JOIN retailers r USING (retailer_id)
                 WHERE o.order_date >= DATE '2026-05-01' GROUP BY 1)
             SELECT s.site_id, ROUND(100*SUM(CASE WHEN t.minutes_10am <= 45 THEN d.v ELSE 0 END)/SUM(d.v))
             FROM candidate_sites s JOIN drive_times t USING (site_id) JOIN dmd d USING (area_id) JOIN areas a USING (area_id)
             WHERE a.cluster='New Cairo' GROUP BY 1"""))
for k, t in dict(A=78, B=71, C=92, D=55, E=88, F=49, G=84).items():
    chk(f"45-min coverage - site {k}", f"{t}%", f"{cov[k]:.0f}%", cov[k] == t)
n = q("SELECT COUNT(*) FROM retailers r JOIN drive_times t ON t.area_id = r.area_id")[0][0]
chk("fan-out join rows", "28,000", f"{n:,}", n == 28000)
width = max(len(r[0]) for r in rows)
for r in rows:
    print(f"{r[3]:6s} {r[0]:<{width}}  target {str(r[1]):<22} actual {r[2]}")
bad = [r for r in rows if r[3] != "OK"]
print(f"\n{len(rows) - len(bad)}/{len(rows)} figures match the scripts.")
