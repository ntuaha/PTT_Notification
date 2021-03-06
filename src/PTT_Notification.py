import requests
from bs4 import BeautifulSoup
import time
import re
import os
import sys
import subprocess
import json

def get_web_page(url):
    headers = {
        'cache-control': "no-cache"
    }
    r = requests.request("GET", url, headers=headers, cookies={'over18': '1'})
    if r.status_code != 200:
        print('Invalid url:', r.url)
        return None
    else:
        return r.text

def get_articles(html, date):
    articles = []  # 儲存取得的文章資料
    soup = BeautifulSoup(html, 'html.parser')
    divs = soup.find_all('div', 'r-ent')
    go_prev = True 
    print(len(divs))
    for d in divs:
        if d.find('div', 'date').string.lstrip() == date:  # 發文日期正確
            # 取得推文數
            push_count = 0
            if d.find('div', 'nrec').string:
                try:
                    push_count = int(d.find('div', 'nrec').string)  # 轉換字串為數字
                except ValueError:  # 若轉換失敗，不做任何事，push_count 保持為 0
                    pass

            # 取得文章連結及標題
            if d.find('a'):  # 有超連結，表示文章存在，未被刪除
                href = d.find('a')['href']
                title = d.find('a').string
                articles.append({
                    'title': title,
                    'href': href,
                    'push_count': push_count
                })
        else:
           go_prev = False
        
    #if(go_prev):
    #    a = soup.find_all("a",string=re.compile("‹ 上頁"))
    #    page = get_web_page("https://www.ptt.cc/"+a[0]['href'])
    #    articles.extend(get_articles(page,date))
    
    print(len(articles))    
    return articles


def send(recipient,post):
    sendToFacebook(recipient,"PTT訊息- %s\n%s"%(time.strftime("%H:%M:%S"),post['title']),"https://www.ptt.cc/"+post['href'])


def sendToFacebook(recipient,text,link):
    api_url = 'https://graph.facebook.com/v2.10/me/messages?access_token=%s'%token
    #print(api_url)
    headers = {'Content-Type': 'application/json'}
    payload = {
      'recipient': {'id':recipient},
      'tag':'TICKET_UPDATE',
      'message':{
       'attachment':{
         "type":"template",
         "payload":{
            "template_type":"button",
            "text":text,
            "buttons":[
              {
                "type":"web_url",
                "url":link,
                "title":"由此去"
              }
            ]
          }
       }  
      }
      
      
    }
    #print(payload)
    #r = requests.post(api_url,json=payload)
    cmd = "curl -X POST %s -H 'content-type: application/json' -d '%s' " % (
        api_url, json.dumps(payload))
    print(cmd)
    subprocess.call(cmd,shell=True)
    #os.system("curl -X -H 'content-type: application/json'  POST -''"%)
    #print(r.text)
    return True

def sendText(recipient, text):
    messageData = {'text':text}
    sendToFacebook(recipient,messageData)

    
if __name__ == "__main__":    
    token = os.environ['fb_token']
    recipient = os.environ['recipient']
    board = "Drama-Ticket"
    base = sys.argv[1]
    url = "https://www.ptt.cc/bbs/%s/index.html"%board    
    page = get_web_page(url)
    with open(sys.argv[1]+"/work.log","a+") as f:
        f.write("[check] %s\n"%time.strftime("%Y-%m-%d %H:%M:%S"))

    if page:
        date = time.strftime("%m/%d").lstrip('0')  # 今天日期, 去掉開頭的 '0' 以符合 PTT 網站格式
        current_articles = get_articles(page, date)
    #    for post in current_articles:
    #        print(post)
        fname = "%s/%s.log"%(base,date.replace("/","_"))
        links = []
        if os.path.exists(fname):
            with open(fname,'r') as f:
                links = f.readlines()
                links = [link[:-1] for link in links]

        for post in current_articles:
            if "[售票]" in post['title'] and "綺貞" in post['title']:                
            #if "綺貞" in post['title']: 
            #if "[售票]" in post['title']:           
                jump = False
                for link in links:
                    if link == post['title']:
                        print("已經出現過")
                        jump = True
                    if(jump):
                        break
                if(jump):
                    continue
                with open(fname,"a+") as f:
                    f.write("%s\n"%post['title'])
                send(recipient,post)

