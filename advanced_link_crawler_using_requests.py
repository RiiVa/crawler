import re
import json
import lxml.html
from urllib import robotparser
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests
from throttle import Throttle


def download(url, user_agent='wswp', num_retries=2, proxies=None):
    """ Download a given URL and return the page content
        args:
            url (str): URL
        kwargs:
            user_agent (str): user agent (default: wswp)
            proxies (dict): proxy dict w/ keys 'http' and 'https', values
                            are strs (i.e. 'http(s)://IP') (default: None)
            num_retries (int): # of retries if a 5xx error is seen (default: 2)
    """
    print('Downloading:', url)
    headers = {'User-Agent': user_agent}
    try:
        resp = requests.get(url, headers=headers, proxies=proxies)
        html = resp.text
        
        #print(resp.title())
        #print(html.title)

        if resp.status_code >= 400:
            print('Download error:', resp.status_code)
            print(url)
            html = None
            if num_retries and 500 <= resp.status_code < 600:
                # recursively retry 5xx HTTP errors
                return download(url, num_retries - 1)
    except requests.exceptions.RequestException as e:
        print('Download error:', e)
        html = None
    return html


def get_robots_parser(robots_url):
    " Return the robots parser object using the robots_url "
    rp = robotparser.RobotFileParser()
    rp.set_url(robots_url)
    rp.read()
    return rp


def get_links(html):
    """ Return a list of links (using simple regex matching)
        from the html content """
    # a regular expression to extract all links from the webpage
    webpage_regex = re.compile("""<a[^>]+href=["'](.*?)["']""", re.IGNORECASE)
    # list of all links from the webpage
    return webpage_regex.findall(html)


def link_crawler(start_url, link_regex, robots_url=None, user_agent='wswp',
                 proxies=None, delay=3, max_depth=1):
    """ Crawl from the given start URL following links matched by link_regex.
    In the current implementation, we do not actually scrape any information.

        args:
            start_url (str): web site to start crawl
            link_regex (str): regex to match for links
        kwargs:
            robots_url (str): url of the site's robots.txt
                              (default: start_url + /robots.txt)
            user_agent (str): user agent (default: wswp)
            proxies (dict): proxy dict w/ keys 'http' and 'https', values
                            are strs (i.e. 'http(s)://IP') (default: None)
            delay (int): seconds to throttle between requests
                         to one domain (default: 3)
            max_depth (int): maximum crawl depth (to avoid traps) (default: 4)
    """
    i = 0
    crawl_queue = [start_url]
    result = []
    # keep track which URL's have seen before
    seen = {}
    if not robots_url:
        robots_url = '{}/robots.txt'.format(start_url)
    rp = get_robots_parser(robots_url)
    throttle = Throttle(delay)
    while crawl_queue:
        url = crawl_queue.pop()
        # check url passes robots.txt restrictions
        if rp.can_fetch(user_agent, url):
            depth = seen.get(url, 0)
            if depth == max_depth:
                print('Skipping %s due to depth' % url)
                continue
            throttle.wait(url)
            html = download(url, user_agent=user_agent, proxies=proxies)
            if not html:
                continue
            i+=1
            print(i)
            yield WikiItem(html, url)
            # TODO: add actual data scraping here
            # filter for links matching our regular expression
            print(crawl_queue)
            for link in get_links(html):
               # print(link,'WTF')
                if re.match('#(a-z)*', link):
                    continue
                if re.match(link_regex, link):

                    abs_link2 = urljoin(start_url, 'A/')
                    abs_link = urljoin(abs_link2, link)
                    if abs_link not in seen:
                        seen[abs_link] = depth + 1
                        crawl_queue.append(abs_link)
        else:
            print('Blocked by robots.txt:', url)

def WikiItem(html,url):
    item = {}
    item['url'] = url
    soup = BeautifulSoup(html,'lxml') 
    a = [s.extract() for s in soup(['script', 'style', 'noscript'])]
    item['content'] = soup.get_text().strip()
    
    # a = [s.extract() for s in soup(['script', 'style', 'noscript'])]
    # tree = lxml.html.fromstring(html)
    # item['content'] = tree.text_content().strip()

    return item
def open_file():
    file = open('items.jl','w')
    return file
def close_file(file):
    file.close()

def process_file(item,file):
    line = json.dumps(dict(item))+ "\n"
    file.write(line)

content = link_crawler('http://192.168.43.106:8000/wikipedia_es_all_2017-01/?', '/*',max_depth = 1)
file = open_file()

for x in content:
    process_file(x, file)
    print(x)

close_file(file)