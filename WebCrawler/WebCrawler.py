#!/usr/bin/python3
#! - * - coding: utf-8 - * -
# Author: Nuttapon Thanitsukkan 5710501565

import os, atexit, time, re, requests, coloredlogs, logging
from bs4 import *
from threading import Thread
import queue

NUM_THREADS = 20
MAX_PAGES = 10030
html_counter = 0
downloaded_pages = 0
html_files = queue.Queue(NUM_THREADS * 10)
page_files = queue.Queue()
MODE = False
visited_pages = set()
blacklist_ext = ['.JPG', '.jpg', '.wmv', '.pdf', '.mp4', '.mp3', '.PNG', '.png'] # in <a> tag

class WebCrawler(Thread):
    def __init__(self):
        super(WebCrawler, self).__init__()
        self.url = None
        self.baseKU = 'ku.ac.th'
        self.lenBaseKU = len(self.baseKU)
        self.compiler_file = re.compile(r".*\.html?")
        self.compiler_domain = re.compile(r"[^\/]*ku\.ac\.th")
        self.current_domain = None
        self.current_path = None

    def is_relative_path(self, url):
        try:
            if url.startswith("./") or url.startswith("/"):
                return True
            return False
        except AttributeError:
            return "#"

    def is_ku(self, url):
        _ = self.compiler_domain.search(url)
        if not _: 
            return False
        if '/' in _.group(0):
            return False
        return True

    def check_html(self, req):
        if not 'text/html' in req.headers['Content-Type']:
            return False
        return True 

    def strip_schema(self, url):
        if url.startswith("http://"):
            return url[7:]
        if url.startswith("https://"):
            return url[8:]
        return url

    def make_default_url(self, url):
        if url == '/' or url == './':
            return self.current_domain
        if self.is_relative_path(url):
            return self.current_domain + '/' + url.lstrip("./")
        return self.strip_schema(url)

    def is_root(self, filepath):
        return len(filepath.split('/')) <= 2

    def do_uncomment(self, text):
        comm = re.compile("<!--|-->")
        return comm.sub("", text)

#    def do_filter(self, url):
#        start = url.find(self.baseKU) + self.lenBaseKU
#        return self.make_default_url(url[:start]), url[start:]

    def do_analyze(self, url, req):
        # self.current_domain, self.current_path = self.do_filter(url)
        # logging.critical("enter analyze")
        if not '/' in self.current_domain:
            soup = BeautifulSoup(self.do_uncomment(req.text), 'html.parser')
            self.check_add_tag(soup.findAll('a'))
            self.check_add_meta(soup.find('meta', attrs={'http-equiv': 'refresh'}))

    def check_add_tag(self, tags):
        # logging.critical("enter check_tag")
        for link in tags:
            link = link.get('href')
            link and self.do_add(link)

    def check_add_meta(self, meta):
        # logging.critical("enter check_add_meta")
        if meta:
            link = meta.get('url')
            link and self.do_add(link)

    def do_add(self, link):
        # logging.critical("Enter do_add")
        global visited_pages, page_files, html_counter, blacklist_ext
        link = self.make_default_url(link)
        if not link in visited_pages and not any(ext in link for ext in blacklist_ext) and self.is_ku(link):
            page_files.put(link)
            visited_pages.add(link)
            if any(ext in link for ext in ['.html', '.htm']) and requests.head("http://" + link, timeout=3, allow_redirects=False).status_code == 200:
                html_counter += 1

    def check_robots(self):
        return requests.head("http://%s/robots.txt" % self.current_domain, timeout=3, allow_redirects=False).status_code == 200

    def save_robots(self):
        with open("robots.txt", "a") as f:
            f.write("%s/robots.txt" % self.current_domain + "\n")

    def put_html(self, url, content):
        global html_files, html_counter
        if any(ext in url for ext in ['.html', '.htm']):
            html_files.put((url, content))

    def run(self):
        global html_files, page_files, html_counter, visited_pages
        while True:
            try:
                # logging.critical("Enter run")
                self.url = page_files.get()
                self.current_domain = self.make_default_url(self.url[:self.url.find(self.baseKU)+self.lenBaseKU])
                self.current_path = self.url[self.url.find(self.baseKU)+self.lenBaseKU:]
                if not '/' in self.current_domain:
                    self.check_robots() and self.save_robots()
                if html_counter >= MAX_PAGES:
                    logging.critical("Stop Crawling...")
                    MODE = True
                    if any(ext in self.url for ext in ['.html', '.htm']):
                        html_files.put((self.url, requests.get("http://" + self.url, timeout=3).content))
                    page_files.task_done()
                    continue
                logging.info("Requesting %s" % self.current_domain + self.current_path)
                # logging.critical("before get")
                req = requests.get("http://" + self.url, timeout=3)
                # logging.critical("after get")
                self.put_html(self.url, req.content)
                if self.check_html(req):
                    self.do_analyze(self.url, req)
                # logging.critical("after analyze")
                page_files.task_done()
            except requests.exceptions.MissingSchema:
                logging.critical("Incorrect URL format")
            except requests.exceptions.InvalidSchema:
                logging.critical("No connection adapters were found for '%s'" % self.url)
            except requests.exceptions.ConnectionError:
                logging.critical("404 Not Found: %s" % self.url)
            except KeyboardInterrupt:
                logging.critical("Ending program...")
                exit(0)
            except Exception as e:
                logging.critical("'WebCrawler', an error occured: %s" % e)

class WebDownloader(Thread):
    def run(self):
        global html_files, downloaded_pages
        while True:
            try:
                if downloaded_pages >= MAX_PAGES:
                    break
                (url, content) = html_files.get()
                self.do_download(url, content)
                logging.warning("Downloading: %s" % url)
                html_files.task_done()
            except Exception as e:
                logging.critical("'WebDownloader', an error occured: %s" % e)

    def do_download(self, url, content):
        global downloaded_pages
        url_splitted = url.split('/')
        current_domain = url_splitted[0]
        current_path = "/" + "/".join(url_splitted[1:])
        if current_path == '':
            filepath = "html/%s/#" % current_domain
        else:
            filepath = "html/" + current_domain + current_path
        logging.critical(filepath)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(content)
        logging.warning("Saved at %s" % filepath)
        downloaded_pages += 1

class Debugger(Thread):
    def run(self):
        global html_files, page_files, html_counter, downloaded_pages
        while True:
            logging.warning("html files queuing: %d file(s)" % html_files.qsize())
            logging.warning("page files queuing: %d file(s)" % page_files.qsize())
            logging.warning("downloaded counter: %d" % downloaded_pages)
            logging.warning("html counter: %d" % html_counter)
            time.sleep(3)


def clean_robots():
    logging.warning("Cleaning robots.txt...")
    time.sleep(1)
    os.system("sort robots.txt | uniq > robots_sorted.txt")

def main():
    atexit.register(clean_robots)
    coloredlogs.install(fmt="%(asctime)-8s %(message)s", datefmt="%H:%M:%S")
    page_files.put("www.ku.ac.th")
    for _ in range(NUM_THREADS):
        WebCrawler().start()
    WebDownloader().start()
    Debugger().start()

if __name__ == '__main__':
    main()
