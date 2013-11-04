#!/usr/bin/env python

import bs4
import collections
import datetime
import itertools
import os
import time
import urllib2
import urlparse

CACHE_SECONDS = datetime.timedelta(days=14).total_seconds()
URLS = {
    "forum": u"http://www.ambrosiasw.com/forums/index.php?showforum=%d&st=%d&prune_day=100",
    "topic": u"http://www.ambrosiasw.com/forums/index.php?showtopic=%d&st=%d",
}


def page_to_url(kind, n, st=0):
    return URLS[kind] % (n, st)


def url_to_page(url):
    url = urlparse.urlparse(url)
    qs = urlparse.parse_qs(url.query)
    st = int(qs.get("st", [0])[-1])
    if not url.path.endswith("/index.php"):
        return None, None, None
    elif "showtopic" in qs:
        return "topic", int(qs["showtopic"][-1]), st
    else:
        return "forum", int(qs.get("showforum", [0])[-1]), st


def fetch(url):
    page = url_to_page(url)
    path = "%s/%d/%d.html" % page
    print "fetching %s %s (%s)" % page
    try:
        st = os.stat(path)
    except OSError:
        pass
    else:
        if st.st_mtime > (time.time() - CACHE_SECONDS):
            with open(path) as f:
                return f.read()

    data = urllib2.urlopen(url).read()
    try:
        os.makedirs(os.path.dirname(path))
    except OSError:
        pass
    with open(path, "w") as f:
        f.write(data)
    time.sleep(len(data) / 56320.0)  # Be nice to their servers.
    return data


def is_last_page(url, doc):
    this_kind, this_n, this_page = url_to_page(url)
    for link in doc.find_all("a"):
        href = link.get("href")
        if not href:
            continue
        that_kind, that_n, that_page = url_to_page(href)
        if ((this_kind, this_n) == (that_kind, that_n)) and (that_page > this_page):
            return False
    return True


def all_forum_pages(forum):
    for i in itertools.count():
        url = page_to_url("forum", forum, i * 30)
        doc = bs4.BeautifulSoup(fetch(url))
        yield i, url, doc
        if is_last_page(url, doc):
            break


def main():
    topics = collections.defaultdict(int)
    for i, url, doc in all_forum_pages(17):
        links = doc.find_all("a")
        for link in links:
            href = link.get("href")
            if not href:
                continue
            kind, n, st = url_to_page(href)
            if kind == "topic":
                topics[n] = max(topics[n], st)
    for topic, st in sorted(topics.iteritems()):
        for i in xrange(0, st + 25, 25):
            fetch(page_to_url("topic", topic, i))


if __name__ == "__main__":
    main()
