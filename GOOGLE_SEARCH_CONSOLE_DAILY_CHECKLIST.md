# Daily Search Console Checklist

Use this after the daily BetLegendPicks publish finishes and the discovery audit passes.

1. Submit or refresh `https://www.betlegendpicks.com/sitemap.xml` in Google Search Console.
2. Inspect the latest Featured Game URL and confirm Google sees the canonical public URL.
3. Inspect the latest MLB, NBA, and NHL preview URLs.
4. Request indexing only for the most important daily URLs, not every archive URL.
5. Monitor the Pages report for:
   - Crawled - currently not indexed
   - Discovered - currently not indexed
   - Duplicate without user-selected canonical
   - Not found (404)
   - Page with redirect
   - Blocked by robots.txt
6. If a latest page is missing from the sitemap or internal links, fix the publishing workflow before requesting indexing.
7. Do not use Google's Indexing API for ordinary betting previews, picks, or articles. Use sitemaps, internal links, Search Console inspection, and the RSS feed.
