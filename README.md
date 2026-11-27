# Precision Fermentation static site

This directory can be published directly from a GitHub Pages branch (the repository root). It needs no build step or PHP. It also works as a project site under a repository path. The home page is English; translated pages are at `/en/`, `/es/`, `/fr/`, `/it/`, `/de/`, `/zh/`, `/ja/`, `/id/`, `/pt/` and `/ru/` relative to the site root. Existing `?lang=` links redirect to the matching page when JavaScript is enabled. The original Catalan file contained Spanish text, so it is not offered as a Catalan translation.

GitHub Pages cannot execute PHP or reproduce an old `/index.php` URL or domain-specific routing. Existing domains must be configured separately with the hosting and DNS provider.

## Update the news

The pages contain a snapshot of the news, so they continue to work without a server. To refresh the RSS feeds and translated headlines locally, install Python 3 and obtain a DeepL API key. Set it in the environment (do not commit it), then run:

```sh
read -rs -p 'DeepL API key: ' DEEPL_AUTH_KEY
printf '\n'
export DEEPL_AUTH_KEY
python3 scripts/update-news.py
```

The script fetches the original feeds, translates headlines with DeepL, and updates the news sections in all language pages. Spanish uses the Spanish meat feed. It prepares all updates before writing them, so a failed feed or translation request leaves the pages unchanged. Review and commit the changed HTML files, then push them to the GitHub Pages branch. DeepL API requests may incur charges. For a DeepL Pro key, set `DEEPL_API_URL=https://api.deepl.com/v2/translate` as well. Article links in translated pages use Google Translate, as on the original site.

To preview locally, run `python3 -m http.server` in this directory and open the displayed address. To check project-path hosting, serve the directory as a subdirectory of the server root.

## Public domains and search

The search metadata expects English at `https://precisionfermentationfood.com/`, the other non-Spanish languages under that domain (for example `/fr/`), and Spanish at `https://fermentaciondeprecision.com/es/`. When the same static files are served at the Spanish domain, visitors to its root are sent to `/es/` by JavaScript. The Spanish page uses its own GoatCounter account.

These URLs must actually be served over HTTPS before search engines or social networks can use the canonical URLs, language links, sharing images, and the two sitemaps. A single GitHub Pages site can have only one custom domain; serving both domains without redirecting one away requires two separately configured Pages sites or another hosting arrangement. If a domain redirects to the other, the canonical and language metadata must be updated to match the actual destination. Verify both domains in Search Console and submit `sitemap.xml` on the English domain and `sitemap-es.xml` on the Spanish domain.

Legacy paths such as `/products`, `/benefits`, `/learn-more`, `/news`, and `/companies` use static redirect pages to reach the matching home-page sections. They preserve query parameters when JavaScript is available and include a no-JavaScript fallback. These are client-side redirects; GitHub Pages does not provide custom server-side redirect rules. Unmatched paths display `404.html`.
