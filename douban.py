# coding-utf-8

import os
import time
import requests
import datetime
from multiprocessing import Pool,cpu_count
import urllib.request
import sqlite3
from bs4 import BeautifulSoup
import sys
import webbrowser

import Config

__version__ = '0.0.1'
__author__ = 'leeewl'

class Utils(object):
    @staticmethod
    def isInBalckList(blacklist, toSearch):
        if blacklist:
            return False
        for item in blacklist:
            if toSearch.find(item) != -1:
                return True
        return False

    @staticmethod
    def getTimeFromStr(timeStr):
        if '-' in timeStr and ':' in timeStr:
            return datetime.datetime.strptime(timeStr, "%Y-%m-%d %H:%M:%S")
        elif '-' in timeStr:
            return datetime.datetime.strptime(timeStr, "%Y-%m-%d")
        elif ':' in timeStr:
            date_today = datetime.date.today();
            date = datetime.datetime.strptime(timeStr, "%H:%M:%S")
            return date.replace(year=date_today.year, month=date_today.month, day=date_today.day)
        else:
            return datetime.date.today()


class Main(object):
    def __init__(self, config):
        self.config = config
        self.douban_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,en-GB;q=0.2,zh-TW;q=0.2',
            'Connection': 'keep-alive',
            'DNT': '1',
            'HOST': 'www.douban.com',
            'Cookie': ''
        }
        self.ok = True

    def getUrl(self, group, begin_num, keyword):
        group_in_url = str(group)
        num_in_url = str(begin_num * 50)
        douban_url = 'https://www.douban.com/group/search?start=' + num_in_url +'&group=' + group_in_url + '&cat=1013&sort=time&q=' + keyword
        return douban_url

    def crawl(self, cursor, douban_url, douban_headers, start_time):
        print("url_link",douban_url)
        print('douban_headers',douban_headers)
        r = requests.get(douban_url, headers = douban_headers)
        if r.status_code == 200:
            try:
                with open('douban_2.txt', 'wb+') as f:
                    f.write(r.content)
                soup = BeautifulSoup(r.text, "html.parser")
                with open('douban_soup.txt', 'wb+') as f:
                    b = soup.prettify()
                    f.write(b.encode("utf-8"))
                #print(soup.prettify())
                table = soup.find_all(attrs={'class': 'olt'})[0]
                with open('douban_table.txt', 'wb+') as f:
                    #b = soup.prettify()
                    f.write(table.encode("utf-8"))
                for tr in table.find_all('tr'):
                    td = tr.find_all('td')
                    title_element = td[0].find_all('a')[0]
                    print("title_element", title_element)
                    title_text = title_element.get('title')
                    time_text = td[1].get('title')
                    link_text = title_element.get('href');
                    reply_count = td[2].find_all('span')[0].text
                    print(title_text)
                    print(time_text)
                    print(link_text)
                    if Utils.isInBalckList(self.config.custom_black_list, title_text):
                        continue
                    if Utils.getTimeFromStr(time_text) < start_time:
                        continue
                    try:
                        print("old_link begin")
                        #old_link = cursor.execute('SELECT * FROM rent WHERE rent.url = ?',[link_text])
                        old_link = cursor.execute("SELECT * FROM rent WHERE rent.url = '%s'"%(link_text)).fetchall()
                        print("old_link :", old_link)
                        if len(old_link) < 1:
                            print("............new link..........................")
                            webbrowser.open(link_text)
                            cursor.execute(
                                'INSERT INTO rent(id, title, url, itemtime, crawtime, note) VALUES(NULL, ?, ?, ?, ?, ?)',
                                [title_text, link_text, Utils.getTimeFromStr(time_text),datetime.datetime.now() , reply_count])
                            print ('add new data:', title_text, time_text,)
                            time.sleep(self.config.douban_sleep_time)
                    except Exception as e:
                        print("error crawl db ", str(e))
               
            except Exception as e:
                print("error crawl ", str(e))

        time.sleep(self.config.douban_sleep_time)
                            
    def run(self):
        try:
            key_list = self.config.key_search_word_list
            group_list = self.config.group_list
            start_time = Utils.getTimeFromStr(self.config.start_time)
            begin_num = 0

            try:
                print('open database ...')
                conn = sqlite3.connect('douban.sqlite')
                conn.text_factory = str
                cursor = conn.cursor()
                cursor.execute('CREATE TABLE IF NOT EXISTS rent(id INTEGER PRIMARY KEY, title TEXT, url TEXT UNIQUE, itemtime timestamp, crawtime timestamp, note TEXT)')
                cursor.close()
                cursor = conn.cursor()
            except Exception as e:
                print('connect database error',str(e))

            print("begin .......")
            for i in range(len(group_list)):
                for j in range(len(key_list)):
                    group = group_list[i]
                    keyword = key_list[j]
                    douban_url = self.getUrl(group, begin_num, keyword)
                    self.crawl(cursor, douban_url, self.douban_headers, start_time)
                    conn.commit()
            
            cursor.close()
                
        except Exception as e:
            print('Error: ',str(e))
        finally:
            conn.commit()
            conn.close()
            print('=====end========')

class Spider(object):
    def __init__(self):
        this_file_dir = os.path.split(os.path.realpath(__file__))[0]
        config_file_path = os.path.join(this_file_dir, 'config.ini')
        
        self.ok = True
        self.config = Config.Config(config_file_path)
        print(self.config.group_list)

    def run(self):
        main =Main(self.config)
        main.run()

if __name__ == '__main__':
    spider = Spider()
    var = 1
    while var ==1:
        spider.run()
