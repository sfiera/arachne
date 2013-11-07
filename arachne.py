#!/usr/bin/env python

import bs4
import collections
import itertools
import os
import utils


def is_last_page(url, doc):
    this_kind, this_n, this_page = utils.url_to_page(url)
    for link in doc.find_all("a"):
        href = link.get("href")
        if not href:
            continue
        that_kind, that_n, that_page = utils.url_to_page(href)
        if (this_kind, this_n) != (that_kind, that_n):
            continue
        if that_page > this_page:
            return False
    return True


def fix_links(doc):
    links = doc.find_all("a")
    for link in links:
        href = link.get("href")
        if not href:
            continue
        kind, n, page = utils.url_to_page(href)
        if kind is not None:
            link["href"] = "../../%s/%d/%d.html" % (kind, n, page)


def save(url, doc):
    path = "out/%s/%d/%d.html" % utils.url_to_page(url)
    try:
        os.makedirs(os.path.dirname(path))
    except OSError:
        pass
    with open(path, "w") as f:
        f.write(str(doc))


def all_topic_urls(doc):
    links = doc.find_all("a")
    for link in links:
        href = link.get("href")
        if not href:
            continue
        kind, n, page = utils.url_to_page(href)
        if kind == "topic":
            yield n, page


def should_fix_links(url):
    page = utils.url_to_page(url)
    old = utils.cache_url(page)
    new = "out/%s/%d/%d.html" % page
    try:
        st_old = os.stat(old)
        st_new = os.stat(new)
    except OSError:
        return True
    return st_old.st_mtime > st_new.st_mtime


def all_forum_pages(forum):
    for i in itertools.count(1):
        url = utils.page_to_url("forum", forum, i)
        doc = bs4.BeautifulSoup(utils.fetch(url))
        last = is_last_page(url, doc)
        yield i, url, doc
        if last:
            break


def main():
    for forum in [17, 64, 90]:
        topics = collections.defaultdict(lambda: 1)

        for i, url, doc in all_forum_pages(forum):
            for n, page in all_topic_urls(doc):
                topics[n] = max(topics[n], page)
            if should_fix_links(url):
                fix_links(doc)
                save(url, doc)

        for topic, page in sorted(topics.iteritems()):
            for i in xrange(1, page + 1):
                url = utils.page_to_url("topic", topic, i)
                data = utils.fetch(url)
                if should_fix_links(url):
                    doc = bs4.BeautifulSoup(data)
                    fix_links(doc)
                    save(url, doc)


if __name__ == "__main__":
    main()
