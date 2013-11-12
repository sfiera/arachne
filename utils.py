#!/usr/bin/python

import datetime
import os
import re
import sys
import time
import urllib2
import urlparse

CACHE_SECONDS = datetime.timedelta(days=30).total_seconds()
URLS = {
    "forum": u"http://www.ambrosiasw.com/forums/index.php?showforum=%s&st=%s&prune_day=100",
    "topic": u"http://www.ambrosiasw.com/forums/index.php?showtopic=%s&st=%s",
    "addons": u"http://www.ambrosiasw.com/games/%s/addons?page=%s",
    "addon": u"http://www.ambrosiasw.com/assets/modules/addonfiles/download.php?addon=%s",
}


def page_to_url(kind, n, page=1):
    if kind == "topic":
        st = (page - 1) * 25
    elif kind == "forum":
        st = (page - 1) * 30
    elif kind == "addons":
        st = page
    else:
        return URLS[kind] % n
    return URLS[kind] % (n, st)


def url_to_page(url):
    url = urlparse.urlparse(url)
    qs = urlparse.parse_qs(url.query)

    if url.netloc and not url.netloc.endswith("ambrosiasw.com"):
        return None, None, None
    if url.path == "/forums/index.php":
        st = int(qs.get("st", [0])[-1])
        if "showtopic" in qs:
            return "topic", int(qs["showtopic"][-1]), 1 + (st / 25)
        elif "showuser" in qs:
            return "user", int(qs["showuser"][-1]), 1
        else:
            return "forum", int(qs.get("showforum", [0])[-1]), 1 + (st / 30)
    elif re.match("^/games/.*/addons/?$", url.path):
        game = url.path.split("/")[2]
        page = int(qs.get("page", [0])[-1])
        return "addons", game, page
    elif url.path == "/assets/modules/addonfiles/download.php":
        return "addon", int(qs["addon"][-1]), 1
    return None, None, None


def local_path(page):
    kind, n, st = page
    if kind == "addon":
        return "addon/%s.bin" % n
    else:
        return "%s/%s/%s.html" % page


def cache_url(page):
    return "cache/%s" % local_path(page)


def fetch(url):
    start = time.time()
    page = url_to_page(url)
    path = cache_url(page)
    sys.stdout.write("fetching %s %s (%s)..." % page)
    try:
        st = os.stat(path)
    except OSError:
        pass
    else:
        if st.st_mtime > (time.time() - CACHE_SECONDS):
            with open(path) as f:
                sys.stdout.write(" cached\n")
                return f.read()

    sys.stdout.write(" downloading...")
    sys.stdout.flush()
    data = urllib2.urlopen(url).read()
    try:
        os.makedirs(os.path.dirname(path))
    except OSError:
        pass
    with open(path, "w") as f:
        f.write(data)

    # Be nice to their servers--rate limit to 56k
    duration = time.time() - start
    rate_lim = len(data) / 56320.0
    if duration < rate_lim:
        time.sleep(rate_lim - duration)

    sys.stdout.write(" done\n")
    return data


def is_last_page(url, doc):
    this_kind, this_n, this_page = url_to_page(url)
    for link in doc.find_all("a"):
        href = link.get("href")
        if not href:
            continue
        that_kind, that_n, that_page = url_to_page(href)
        if (this_kind, this_n) != (that_kind, that_n):
            continue
        if that_page > this_page:
            return False
    return True
