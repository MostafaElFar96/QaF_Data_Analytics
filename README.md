# QaF Data Analytics — Module 4 practice data

## Sandbox Warehouse Listings

A small static website used in Class 3 to practise responsible web scraping.
It looks like a real warehouse-listings site, but every listing, broker and phone number is fictional.

- Live site (GitHub Pages): https://mostafaelfar96.github.io/QaF_Data_Analytics/
- Listings: `warehouses/page-1.html` … `page-5.html` (37 listings, 8 per page)
- `robots.txt`: disallows `/contacts/` and asks for a 2-second crawl delay

Run it locally if the live site is unavailable:

```bash
# from the repo folder
python -m http.server 8000
# then use BASE = "http://localhost:8000"
```

Everyone scraping this site gets exactly the same data, so results match across teams and the course videos.
