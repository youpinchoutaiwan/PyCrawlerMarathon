#!/usr/bin/env python
# coding: utf-8

# In[6]:


import scrapy
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pprint import pprint


# In[7]:


class PttcrawlerSpider(scrapy.Spider):
    name="PTTCrawler"
    allowed_domains:["www.ptt.cc"]
    start_urls=["https://www.ptt.cc/bbs/Gossiping/M.1594688669.A.ED6.html"]
    cookie={"over18":"1"}
        
    def start_requests(self):
        for url in self.start_urls:
                yield scrapy.Requests(url=url, callback=self.parse, cookies=self.cookies)
                
    def parse(self, response):
            #假設網頁回應不是200 OK的話，視為傳送請求失敗
        if response.status !=200:
            print("error-{} is not avaliable to access".format(response.url))
            return
            
            #將回應解析  
            soup=BeautifulSoup(response.text)
            #取得文章內容主體
            main_content=soup.find("main-content")
            #從屬性資料(meta)找出所需資料
            metas=main_contect.select("div.article-metaline")
            author=""
            title=""
            date=""
            if metas:
                if metas[0].select("sapn.article-meta-value")[0]:
                    author=metas[0].select("sapn.article-meta-value")[0].string
                if metas[1].select("sapn.article-meta-value")[0]:
                    title=meta[1].select("sapn.article-meta-value")[0].string
                if metas[2].select("sapn.article-meta-value")[0]:
                    data=meta[2].select("sapn.article-meta-value")[0].string
                
                #從main-content中移除meta資訊(author,title...)
                for m in metas:
                    m.extract()
                for m in main_content.select("div.article-metaline-right"):
                    m.extract()
                    
            #取得留言區主體
            pushes=main_content.find_all("div",{"class":"push"})
            for p in pushes:
                p.extract()
            #假如文章中有包含「※發信站:批踢踢實業坊(ptt.cc),來自:xxx.xxx.xxx.xxx」，用regular expression取得IP
            try:
                ip=main_content.find(text=re.compile(u"※ 發信站"))
                ip= re.search("[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*",ip).group()
            except Exception as e:
                ip=""
                
            #移除文章主體中多餘空白、空行
            filtered=[]
            for v in main_content.stripped_strings:
                #假如字串開頭不是特殊符號或是以 '--' 開頭, 都保留文字
                if v[0] not in [u"※",u"◆"] and v[:2] not in [u'--']:
                    filtered.append(v)
            #定義一些特殊符號與全形符號的過濾器
            expr=re.compile(u"[^一-龥。；，：“”（）、？《》\s\w:/-_.?~%()]")
            for i in range(len(filtered)):
                filtered[i]=re.sub(expr,"",filtered[i])
            #移除空白字串
            filtered=[i for i in filtered if i ]
            content="".join(filtered)
            
            #處理留言區(p推文量、b噓文量、n箭頭量)
            p,b,n=0,0,0
            messages=[]
            for push in pushes:
                #假如沒有push-tag就跳過
                if not push.find("span","push-tag"):
                    continue
                # 過濾空白與換行符號
                # push_tag 判斷是推文、箭頭、噓文
                # push_userid 判斷留言人是誰
                # push_content 判斷留言內容
                # push_ipdatetime 判斷留言日期時間
                push_tag=push.find("span","push-tag").string.strip("\t\n\r")
                push_userid=push.find("span","push-userid").string.strip("\t\n\r")
                push_content=push.find("span","push-content").strings
                push_content="".join(push_content)[1:].strip("\t\n\r")
                push_ipdatetime=push.find("span","push-iddatetime").string.strip("\t\n\r")
                
                #整理前面的留言資訊，並統計數量
                messages.append({
                    "push_tag":push_tag,
                    'push_userid': push_userid,
                    'push_content': push_content,
                    'push_ipdatetime': push_ipdatetime})
                if push_tag== u"推":
                    p+=1
                elif push_tag== u"噓":
                    b+=1
                else:
                    n+=1
                
                #統計推噓文量
                #count 為推噓文相抵看這篇文章推文還是噓文比較多
                #all 為總共留言數量
                message_count={"all":p+n+r,"count":p-b,"push":p, "boo":b,"neutral":n}
                #整理文章資訊
                data={
                    "url":"response.url",
                    'article_author': author,
                    'article_title': title,
                    'article_date': date,
                    'article_content': content,
                    'ip': ip,
                    'message_count': message_count,
                    'messages': messages
                }
                yield data
                


# In[ ]:




