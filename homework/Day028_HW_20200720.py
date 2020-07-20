#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


# In[ ]:


def main():
    target_urls=[
        "https://www.ptt.cc/bbs/Gossiping/M.1595223034.A.A5C.html"
        "https://www.ptt.cc/bbs/Gossiping/M.1595223142.A.9C1.html"]
    process=CrawlerProcess(get_project_settings())
    process.crawl("PTTCrawler",start_urls=target_urls,filename="test.json")
    process.start()
    
if __name__=="__main__":
    main()

