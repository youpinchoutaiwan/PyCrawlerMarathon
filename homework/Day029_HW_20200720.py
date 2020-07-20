#!/usr/bin/env python
# coding: utf-8

# In[9]:


import scrapy
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
from pprint import pprint
#from items import PTTArticleItem


# In[10]:


class PttcrawlerSpider(scrapy.Spider):
    name="PTTCrawler"
    def __init__(self, board="Gossiping"):
        self.cookies={"over18":"1"}
        self.host="https://www.ptt.cc"
        self.board=board
        self.start_urls="https://www.ptt.cc/bbs/{}/index.html".format(board)
        super().__init__()
        
    def satrt_requests(self):
        yield scrapy.Requests(url=self.start_urls, callback=self.parse, cookies=self.cookies)
    
    def parse(self, response):
        soup=BeautifulSoup(response.text)
        main_list=soup.find("div",{"class":"bbs-screen"})  #取得列表中的清單主體
        
        #依序檢查文章列表中的tag，遇到分隔線就結束，忽略這之後的文章
        for div in main_list.findChildren("div",recursive=False):
            class_name=div.attrs["class"]
            
            #遇到分隔線要處理的情況
            if class_name and "r-list-sep" in class_name:
                self.log("reach the last article")
                break
            #遇到目標文章
            if class_name and "r-ent" in class_name:
                div_title=div.find("div",{"class":"title"})
                a_title=div_title.find("a",href=True)
                #如果文章已被刪除則跳過
                if not a_title or not a_title.has_attr("href"):
                    continue
                article_URL=urljoin(self.host, a_title["href"])
                article_title=a_title.text
                self.log("Parse article{}".format(article_title))
                yield scrapy.Requests(url=article_URL,
                                     callback=self.parse_article,
                                     cookies=self.cookies)
        
        def parse_article(self, response):
        #假設網頁回應不是200 Ok，設定視為請求失敗
            if response.status !=200:
                print("error-{} is not avaliable to acsess".format(response.url))
                return
        
            soup=BeautifulSoup(response.text)
            main_content=soup.find("main-content")  #取得文章主體內容
            #假如文章有屬性資料metas，從屬性區塊中爬出author、title、date
            metas=main_content.select("div.article-metaline")
            author=""
            title=""
            date=""
            if metas:
                if meats[0].select("span.article-meta-value")[0]:
                    author=metas[0].select("span.article-meta-value")[0].string
                if metas[1].select('span.article-meta-value')[0]:
                    title=metas[1].select('span.article-meta-value')[0].string
                if metas[2].select('span.article-meta-value')[0]:
                    date=meats[2].select('span.article-meta-value')[0].string

                #從main_content中移除metas資訊
                for m in metas:
                    m.extract()
                for m in main_content.select(div.article-metaline-right):
                    m.extract()

            #取得留言區主體
            pushes=main_content.find_all("div",{"class":"push"})
            for p in pushes:
                p.extract()

            #假如文章中含「※ 發信站: 批踢踢實業坊(ptt.cc), 來自: xxx.xxx.xxx.xxx」的字樣
            #用regular expression取得IP
            try:
                ip=main_content.find(text=re.compile(u"※ 發信站:"))
                ip=re.search("[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*", ip).group()
            except Exception as e:
                ip=""

            #移除文章主體中多餘的空白、空行
            filtered=[]
            for v in main_content.stripped_strings:
                #假如字首不是特殊符號或"--"都保留
                if v[0] not in [u"※", u"◆"] and v[:2] not in [u"--"]:
                    filtered.append(v)
            #定義一些特殊符號與全形符號過濾器
            expr=re.compile(u"[^一-龥。；，：“”（）、？《》\s\w:/-_.?~%()]")
            for i in range(len(filtered)):
                filtered[i]=re.sub(expr,"",filtered[i])
            #移除空白字串，過濾後的文字即為文章本文
            filtered=[i for i in filtered if i]
            content="".join(filtered)

            #處理留言板 p推蚊數量、b噓文數量、n箭頭數量
            p,b,n=0,0,0
            messages=[]
            for push in pushes:
                if not push.find("span","push-tag"):
                    continue
                push_tag=push.find("span","push-tag").string.strip("\t\n\r") #推文還噓文
                push_userid=push.find("span","push-userid").string.strip("\t\n\r")  #留言人是誰
                push_content=push.find("span","push-content").strings #留言內容
                push_content="".join(push_content)[1:].strip("\t\n\r")
                push_ipdatetime=push.find("span","push-ipdatetime").string.strip("\t\n\r")  #留言日期時間

                #整理打包留言資訊，統計推噓文數量
                messages.append({
                    "push_tag":push_tag,
                    "push_userid":push_userid,
                    "push_content":push_content,
                    "push_ipdatetime":push_ipdatetime})
                if push_tag== u"推":
                    p+=1
                elif push_tag == u"噓":
                    b+=1
                else:
                    n+=1

            #統計推噓文 count為推噓文誰較多、all總留言數量
            message_count={"all":p+b+n,"count":p-b, "push":p,"boo":b,"neutral":n}

            # 整理文章資訊
            data = PTTArticleItem()
            article_id = str(Path(urlparse(response.url).path).stem)
            data['url'] = response.url
            data['article_id'] = article_id
            data['article_author'] = author
            data['article_title'] = title
            data['article_date'] = date
            data['article_content'] = content
            data['ip'] = ip
            data['message_count'] = message_count
            data['messages'] = messages
            yield data

