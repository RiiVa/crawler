import re
import json
import lxml.html
from urllib import robotparser
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests
from throttle import Throttle


def download(url, user_agent='wswp', num_retries=2, proxies=None):
    """ Trata de cargar la pagina y si lo logra guarda el texto de la pagina 
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
    
    # Usando una expresion regular para coger los link
    webpage_regex = re.compile("""<a[^>]+href=["'](.*?)["']""", re.IGNORECASE)
    
    return webpage_regex.findall(html)


def link_crawler(start_url, link_regex, robots_url=None, user_agent='wswp',
                 proxies=None, delay=0.0001, max_depth=999999, max_count = 10000):
    """ 
    Recorre los link en profundidad 
    """
    i = 0
    crawl_queue = [start_url]
    result = []
    # Dict donde guardare las url visitadas para no volver a parsearlas
    seen = {}
    if not robots_url:
        robots_url = '{}/robots.txt'.format(start_url)
    rp = get_robots_parser(robots_url)
    throttle = Throttle(delay)
    while crawl_queue and i <= 10000:
        url = crawl_queue.pop()
        
        if rp.can_fetch(user_agent, url):
            depth = seen.get(url, 0)
            if depth == max_depth:
                print('Skipping %s due to depth' % url)
                continue
            if i > max_count:
                print('Skipping %s due to exceed limit count' % url)
                continue
            throttle.wait(url)
            html = download(url, user_agent=user_agent, proxies=proxies)
            if not html:
                continue
            i+=1
            print(i)
            #Devuelve un item parecido a scrapy donde guardo la url y el texto plano, ademas de 
            ##guardarlo en un fichero
            yield WikiItem(html, url)
            
            # Filtramos los link a usar 
            for link in get_links(html):
                if re.match('#(a-z)*', link):
                    continue
                if re.match(link_regex, link):
                    # Un pequeno parche que la wiki local al pedirle los link no me ponia esta A
                    # en una pagina online no tuve problema al quitarlo
                    #abs_link2 = urljoin(start_url, 'A/')
                    # abs_link = urljoin(abs_link2, link)
                    abs_link = urljoin(start_url, link)
                    if abs_link not in seen and len(abs_link) < 200:
                        seen[abs_link] = depth + 1
                        crawl_queue.append(abs_link)
        else:
            print('Blocked by robots.txt:', url)

def WikiItem(html, url):
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
    file = open('items.json','w')
    return file
def close_file(dictItem,file):
    json.dump(dictItem, file,indent = 4)
    file.close()

def process_file(item,file,dictItem):
    
    dictItem['item'].append(item)

content = link_crawler('http://localhost/D%3A', '/*',max_depth = 2)
#print(len(content))
file = open_file()
dictItem = {}
dictItem['item'] = []
i = 0
for x in content:
    process_file(x, file, dictItem)
    i+=1
print(i)

close_file(dictItem,file)


