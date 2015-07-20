#!/usr/bin/env python

import bs4
import collections
import itertools
import os
import sys
import utils
import urlparse


def fix_links(url, doc):
    for tag in doc.find_all("base"):
        url = tag["href"]
        tag.extract()

    links = doc.find_all("a") + doc.find_all("link")
    for link in links:
        href = link.get("href")
        if not href:
            continue
        kind, n, page = utils.url_to_page(href)
        if kind is not None:
            link["href"] = "../../%s" % utils.local_path((kind, n, page))
        else:
            link["href"] = urlparse.urljoin(url, link["href"])


def save(url, doc):
    path = "out/%s" % utils.local_path(utils.url_to_page(url))
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


def all_addon_ids(doc):
    links = doc.find_all("a")
    for link in links:
        href = link.get("href")
        if not href:
            continue
        kind, n, page = utils.url_to_page(href)
        if kind == "addon":
            yield n


def should_fix_links(url):
    page = utils.url_to_page(url)
    old = utils.cache_url(page)
    new = "out/%s" % utils.local_path(page)
    try:
        st_old = os.stat(old)
        st_new = os.stat(new)
    except OSError:
        return True
    return st_old.st_mtime > st_new.st_mtime


def all_forum_pages(forum):
    for i in itertools.count(1):
        url = utils.page_to_url("forum", forum, i)
        doc = bs4.BeautifulSoup(utils.fetch(url), "lxml")
        last = utils.is_last_page(url, doc)
        yield i, url, doc
        if last:
            break


def all_addon_pages(game):
    for i in itertools.count(1):
        url = utils.page_to_url("addons", game, i)
        doc = bs4.BeautifulSoup(utils.fetch(url), "lxml")
        last = utils.is_last_page(url, doc)
        yield i, url, doc
        if last:
            break


def main():
    assert sys.argv[2:]
    kind, n = sys.argv[1], sys.argv[2:]

    if kind == "forum":
        for forum in n:
            topics = collections.defaultdict(lambda: 1)

            for i, url, doc in all_forum_pages(forum):
                for n, page in all_topic_urls(doc):
                    topics[n] = max(topics[n], page)
                if should_fix_links(url):
                    fix_links(url, doc)
                    save(url, doc)

            for topic, page in sorted(topics.iteritems()):
                for i in xrange(1, page + 1):
                    url = utils.page_to_url("topic", topic, i)
                    data = utils.fetch(url)
                    if should_fix_links(url):
                        doc = bs4.BeautifulSoup(data, "lxml")
                        fix_links(url, doc)
                        save(url, doc)
    elif kind == "addons":
        for game in n:
            addons = []
            for i, url, doc in all_addon_pages(game):
                if should_fix_links(url):
                    fix_links(url, doc)
                    save(url, doc)
                for n in all_addon_ids(doc):
                    addons.append(n)
            for n in sorted(addons):
                url = utils.page_to_url("addon", n, None)
                _ = utils.fetch(url)
                path = utils.local_path(utils.url_to_page(url))
                try:
                    os.unlink("out/%s" % path)
                except OSError:
                    pass
                try:
                    os.makedirs(os.path.dirname("out/%s" % path))
                except OSError:
                    pass
                os.link("cache/%s" % path, "out/%s" % path)
    else:
        assert False


if __name__ == "__main__":
    main()
