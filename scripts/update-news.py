#!/usr/bin/env python3
"""Refresh the news embedded in the static pages. See README.md."""
import datetime as dt
import email.utils
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
LANGUAGES = ('en', 'it', 'fr', 'es', 'de', 'zh', 'ja', 'id', 'pt', 'ru')
FEEDS = (
    'https://vegconomist.com/category/cultivated-cell-cultured-biotechnology/fermentation/feed/',
    'https://vegconomist.com/category/cultivated-meat/feed/',
    'https://vegconomist.com/category/cultivated-cell-cultured-biotechnology/cultivated-seafood/feed/',
    'https://gfi.org/blog/topic/science/feed/',
)
SPANISH_MEAT = 'https://vegconomist.es/category/carne-cultivada/feed/'
MEAT_MATTERS_FEED = 'https://meatmatters.substack.com/feed'
WEBEGREEN_ARTICLES = (
    'https://webegreen.substack.com/p/humbird-or-humbug-cultivated-meats',
    'https://webegreen.substack.com/p/renewables-ai-and-alt-proteins',
    'https://webegreen.substack.com/p/we-need-to-talk-about-precision-fermentation',
    'https://webegreen.substack.com/p/what-past-disruptions-tell-us-about',
    'https://webegreen.substack.com/p/cultivate-your-palate-for-a-new-type',
    'https://webegreen.substack.com/p/precision-fermentation',
)
MEAT_MATTERS_START, MEAT_MATTERS_END = '<!-- MEAT-MATTERS:START -->', '<!-- MEAT-MATTERS:END -->'
START, END = '<!-- NEWS:START -->', '<!-- NEWS:END -->'


def request(url, data=None, headers=None):
    headers = {'User-Agent': 'PrecisionFermentationNewsUpdater/1.0', **(headers or {})}
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers), timeout=30) as response:
        return response.read()


def fetch_feed(url):
    root = ET.fromstring(request(url))
    entries = root.findall('./channel/item')
    if not entries:
        raise ValueError(f'No RSS items found in {url}')
    items = []
    for entry in entries[:4]:
        title = ''.join(entry.findtext('title', default='').splitlines()).strip()
        link = entry.findtext('link', default='').strip()
        date = entry.findtext('pubDate', default='').strip()
        if not title or urllib.parse.urlsplit(link).scheme not in ('http', 'https') or not date:
            raise ValueError(f'Invalid item in {url}')
        parsed = email.utils.parsedate_to_datetime(date)
        items.append((parsed.strftime('%d/%m/%y'), title, link))
    return items


def translate(titles, lang, key):
    if lang == 'en':
        return titles
    url = os.environ.get('DEEPL_API_URL', 'https://api-free.deepl.com/v2/translate')
    data = json.dumps({'text': titles, 'target_lang': lang.upper()}).encode()
    response = json.loads(request(url, data, {'Content-Type': 'application/json', 'Authorization': 'DeepL-Auth-Key ' + key}))
    translations = [item['text'] for item in response['translations']]
    if len(translations) != len(titles):
        raise ValueError('DeepL returned an unexpected number of translations')
    return translations


def render(items, titles, lang, direct=False):
    lines = ['<ul>']
    for (date, _, link), title in zip(items, titles):
        if lang != 'en' and not direct:
            link = 'https://translate.google.com/translate?' + urllib.parse.urlencode({'sl': 'auto', 'tl': lang, 'u': link})
        lines.append(f'<li>{html.escape(date)} : <a href="{html.escape(link, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(title)}</a></li>')
    return ''.join(lines) + '</ul>'


def render_meat_matters(items, titles, lang, image_prefix, previews):
    lines = ['<ul class="article-links">']
    for (date, _, link), title in zip(items, titles):
        image_url = previews.get(link) or image_prefix + 'burger.jpg'
        if lang != 'en':
            link = 'https://translate.google.com/translate?' + urllib.parse.urlencode({'sl': 'auto', 'tl': lang, 'u': link})
        lines.append(
            f'<li><img src="{html.escape(image_url, quote=True)}" alt="" loading="lazy" referrerpolicy="no-referrer">'
            f'<a href="{html.escape(link, quote=True)}" target="_blank" rel="noopener noreferrer">'
            f'{html.escape(title)}</a></li>'
        )
    return ''.join(lines) + '</ul>'


class PreviewImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.image = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'meta':
            return
        values = dict(attrs)
        if (values.get('property') or values.get('name', '')).lower() in ('og:image', 'twitter:image'):
            image = values.get('content', '').strip()
            if urllib.parse.urlsplit(image).scheme == 'https' and not self.image:
                self.image = image


def fetch_previews(urls):
    previews = {}
    for url in urls:
        try:
            parser = PreviewImageParser()
            parser.feed(request(url).decode('utf-8', errors='replace'))
            if parser.image:
                previews[url] = parser.image
        except (OSError, ValueError) as exc:
            print(f'Article preview unavailable for {url}: {exc}', file=sys.stderr)
    return previews


def update_webegreen_images(page, previews):
    start = page.index('data-section="articles"')
    end = page.index('</section>', start)
    section = page[start:end]
    heading = re.search(r'<h3>WeBeGreen[^<]*</h3>', section)
    if not heading:
        raise ValueError('Missing WeBeGreen heading')
    first_list = re.search(r'<ul class="article-links">.*?</ul>', section[heading.end():], re.S)
    if first_list:
        first_list_start = heading.end() + first_list.start()
        first_list_end = heading.end() + first_list.end()
    if not first_list:
        raise ValueError('Missing WeBeGreen article list')
    article_list = first_list.group()
    images = iter(WEBEGREEN_ARTICLES)
    def replace_image(match):
        url = next(images, None)
        if not url or url not in previews:
            return match.group()
        return '<img src="' + html.escape(previews[url], quote=True) + '" alt="" loading="lazy" referrerpolicy="no-referrer">'
    article_list = re.sub(r'<img\b[^>]*>', replace_image, article_list)
    section = section[:first_list_start] + article_list + section[first_list_end:]
    return page[:start] + section + page[end:]


def main():
    key = os.environ.get('DEEPL_AUTH_KEY')
    if not key:
        raise ValueError('Set DEEPL_AUTH_KEY to translate the news before running this script.')
    feeds = {url: fetch_feed(url) for url in (*FEEDS, SPANISH_MEAT)}
    try:
        meat_matters = fetch_feed(MEAT_MATTERS_FEED)
    except (ValueError, OSError, ET.ParseError) as exc:
        # A Substack outage should not prevent the other news feeds updating.
        print(f'Meat Matters feed unavailable; keeping existing articles: {exc}', file=sys.stderr)
        meat_matters = None
    preview_urls = list(WEBEGREEN_ARTICLES) + ([item[2] for item in meat_matters] if meat_matters else [])
    previews = fetch_previews(preview_urls)
    updates = {}
    for lang in LANGUAGES:
        paths = [ROOT / lang / 'index.html']
        if lang == 'en':
            paths.append(ROOT / 'index.html')
        urls = list(FEEDS)
        if lang == 'es':
            urls[1] = SPANISH_MEAT
        sections = []
        for url in urls:
            items = feeds[url]
            direct = lang == 'es' and url == SPANISH_MEAT
            titles = [item[1] for item in items]
            if not direct:
                titles = translate(titles, lang, key)
            sections.append(render(items, titles, lang, direct))
        meat_matters_html = None
        if meat_matters is not None:
            meat_matters_titles = translate([item[1] for item in meat_matters], lang, key)
            meat_matters_html = meat_matters_titles
        for path in paths:
            page = path.read_text(encoding='utf-8')
            if page.count(START) != 1 or page.count(END) != 1:
                raise ValueError(f'Missing or duplicate news markers in {path}')
            before, rest = page.split(START)
            old, after = rest.split(END)
            headings = re.findall(r'<h4><strong>.*?</strong></h4>', old, re.S)
            if len(headings) != len(sections):
                raise ValueError(f'Expected {len(sections)} news headings in {path}, got {len(headings)}')
            news = ''.join(h + content for h, content in zip(headings, sections))
            page = before + START + news + END + after
            if page.count(MEAT_MATTERS_START) != 1 or page.count(MEAT_MATTERS_END) != 1:
                raise ValueError(f'Missing or duplicate Meat Matters markers in {path}')
            if meat_matters_html is not None:
                before, rest = page.split(MEAT_MATTERS_START)
                _, after = rest.split(MEAT_MATTERS_END)
                image_prefix = 'imgs/' if path.parent == ROOT else '../imgs/'
                article_list = render_meat_matters(meat_matters, meat_matters_html, lang, image_prefix, previews)
                page = before + MEAT_MATTERS_START + article_list + MEAT_MATTERS_END + after
            page = update_webegreen_images(page, previews)
            updates[path] = page
    for path, page in updates.items():
        path.write_text(page, encoding='utf-8')
    print(f'Updated news in {len(updates)} pages.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, ET.ParseError) as exc:
        print(f'News update failed; pages were not updated: {exc}', file=sys.stderr)
        sys.exit(1)
