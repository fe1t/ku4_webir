#!/usr/bin/python
# Author: Nuttapon Thanitsukkan 5710501565

from collections import OrderedDict
from bs4 import *
import os

def normalize_link(absPath, link):
    absPath = absPath.split('/')
    try:
        if link.startswith('https://'):
            return link[8:]
        if link.startswith('http://'):
            return link[7:]
        if link.startswith('/'):
            return absPath[0] + link
        if link.startswith('../'):
            return "/".join(absPath[:-(link.count("../") + 1)]) + "/" + link
    except:
        return "NOT FOUND"
    return "/".join(absPath[:-1]) + "/" + link

def create(urls):
    urls = OrderedDict(sorted({value: index + 1 for index, value in enumerate(urls)}.items(), key=lambda t: t[1]))
    for url, index in urls.iteritems():
        graph = set()
        filtered_url = url[7:]
        with open("../html/" + filtered_url) as f:
            soup = BeautifulSoup(f.read())
            for anchor in soup.findAll('a'):
                link = "http://" + normalize_link(filtered_url, anchor.get('href'))
                if link in urls:
                    graph.add(urls[link])
        if len(graph) == 0:
            fw.write("-\n")
        else:
            fw.write(",".join(map(str, list(graph))) + "\n")

if __name__ == '__main__':
    with open('urlmap.txt') as fr:
        urls = fr.read().split('\n')[:-1]
    fw = open('webgraph.txt', 'wb')
    create(urls)
    fw.close()

