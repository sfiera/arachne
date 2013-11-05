#!/usr/bin/env python

import bs4
import collections
import datetime
import itertools
import os
import sys
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
    start = time.time()
    page = url_to_page(url)
    path = "cache/%s/%d/%d.html" % page
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
        if ((this_kind, this_n) == (that_kind, that_n)) and (that_page > this_page):
            return False
    return True


def all_forum_pages(forum):
    for i in itertools.count():
        url = page_to_url("forum", forum, i * 30)
        doc = bs4.BeautifulSoup(fetch(url))
        last = is_last_page(url, doc)
        yield i, url, doc
        if last:
            break


def main():
    for forum in [17, 64]:
        topics = collections.defaultdict(int)

        for i, url, doc in all_forum_pages(forum):
            links = doc.find_all("a")
            for link in links:
                href = link.get("href")
                if not href:
                    continue
                kind, n, st = url_to_page(href)
                if kind == "topic":
                    topics[n] = max(topics[n], st)
                if kind is not None:
                    link["href"] = "../../%s/%d/%d.html" % (kind, n, st)
            path = "out/%s/%d/%d.html" % url_to_page(url)
            try:
                os.makedirs(os.path.dirname(path))
            except OSError:
                pass
            with open(path, "w") as f:
                f.write(str(doc))

        for topic, st in sorted(topics.iteritems()):
            for i in xrange(0, st + 25, 25):
                url = page_to_url("topic", topic, i)
                doc = bs4.BeautifulSoup(fetch(url))
                links = doc.find_all("a")
                for link in links:
                    href = link.get("href")
                    if not href:
                        continue
                    kind, n, st = url_to_page(href)
                    if kind is not None:
                        link["href"] = "../../%s/%d/%d.html" % (kind, n, st)
                path = "out/%s/%d/%d.html" % url_to_page(url)
                try:
                    os.makedirs(os.path.dirname(path))
                except OSError:
                    pass
                with open(path, "w") as f:
                    f.write(str(doc))


if __name__ == "__main__":
    main()
