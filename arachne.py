#!/usr/bin/env python

import bs4
import itertools
import urllib2
import urlparse

URLS = {
    "forum": u"http://www.ambrosiasw.com/forums/index.php?showforum=%d&st=%d&prune_day=100",
    "topic": u"http://www.ambrosiasw.com/forums/index.php?showtopic=%d&st=%d",
}

def page_to_url(kind, n, page=0):
    return URLS[kind] % (n, page * 30)

def url_to_page(url):
    url = urlparse.urlparse(url)
    qs = urlparse.parse_qs(url.query)
    return int(qs.get("st", [0])[-1])

def is_last_page(url, soup):
    page = url_to_page(url)
    for link in soup.find_all("a"):
        href = link.get("href")
        if href and (page_kind(url) == page_kind(href)) and (url_to_page(href) > page):
            return False
    return True

def page_kind(url):
    url = urlparse.urlparse(url)
    qs = urlparse.parse_qs(url.query)
    if "showtopic" in qs:
        return "topic", int(qs["showtopic"][-1])
    else:
        return "forum", int(qs.get("showforum", [0])[-1])

def is_cythera(url):
    url = urlparse.urlparse(url)
    qs = urlparse.parse_qs(url.query)
    return "17" in qs.get("showforum", [])

for i in itertools.count():
    print "Page %d:" % i
    url = page_to_url("forum", 17, i)
    f = urllib2.urlopen(url)
    soup = bs4.BeautifulSoup(f.read())
    links = soup.find_all("a")
    topics = set()
    for link in links:
        href = link.get("href")
        if not href:
            continue
        kind, n = page_kind(href)
        if kind == "topic":
            topics.add(n)
    for topic in sorted(topics):
        print "    %d" % topic
    if is_last_page(url, soup):
        break
