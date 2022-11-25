# -*- coding: utf-8 -*-
# @Time    : 2022/11/25 11:28
# @Author  : Euclid-Jie
# @File    : GetArticleClass.py
import re

import pandas as pd
from selenium.webdriver import Chrome, ChromeOptions  # 导入类库
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait
from time import sleep
import io
import requests


class GetArticleClass(object):
    """
    旨在建立一个下载谷歌学术文献的工具
    考虑了部分无直接下载链接的使用SCI-HUB补充下载
    同步下载谷歌学术的GB/T 7714格式引文
    """

    def __init__(self, pageNums, Keywords, savePath):
        """
        :param pageNums: 需要获取的页数 int
        :param Keywords: 搜索框的关键词 str
        :param savePath: 下载文件保存的文件夹路径, 例如'D:\Euclid_Jie\AutoReferences'
        """
        self.port = None
        self.Url = None
        self.driver = None
        self.pageNums = pageNums
        self.Keywords = Keywords
        self.savePath = savePath

    def GetDriver(self, port):
        """
        新建一个浏览器窗口，需要指定代理端口
        :param port: 代理的端口，从代理软件查看
        :return: self.driver
        """
        self.port = port
        option = ChromeOptions()  # 初始化浏览器设置
        option.add_experimental_option("excludeSwitches", ['enable-automation', 'enable-logging'])  # 添加参数
        ip = "127.0.0.1"
        # 设置代理
        option.add_argument("--proxy-server=http://{}:{}".format(ip, self.port))
        self.driver = Chrome(options=option)  # 模拟开浏览器

    def GetArticles_df(self):
        """
        根据Url获取当前页面上所有Article的信息
        :return:
        """
        self.driver.get(self.Url)  # 跳转该页文章
        ArticleList = self.driver.find_elements(By.CLASS_NAME, 'gs_r.gs_or.gs_scl')
        Articles_df = pd.DataFrame({'ArticleTitle': [], 'ArticleURL': [], 'ArticleDIO': [], 'ArticleRef': []})
        for Article in ArticleList:
            ArticleDetails_List = self.GetArticleDetails(Article)
            Article_df = pd.DataFrame({'ArticleTitle': [ArticleDetails_List[0]], 'ArticleURL': [ArticleDetails_List[1]],
                                       'ArticleDIO': [ArticleDetails_List[2]], 'ArticleRef': [ArticleDetails_List[3]]})
            Articles_df = pd.concat([Articles_df, Article_df])

        return Articles_df.reset_index(drop=True)

    def GetArticleDetails(self, Article):
        """
        :param: Article每一篇文章，selenium对象
        根据每一篇文章，获取其详细信息
        :return: ArticleDetails_List具体包括：
                ArticleTitle: 文章标题
                ArticleURL: 文章首页
                ArticleDIO: 文章的DIO
                ArticleRef: 文章的引文格式
        """
        # 文章名+文章首页
        ArticleTitle = BeautifulSoup(Article.find_element(By.TAG_NAME, 'h3').get_attribute('outerHTML'), features="lxml").text
        ArticleURL = BeautifulSoup(Article.find_element(By.TAG_NAME, 'h3').get_attribute('outerHTML'), features="lxml").a['href']

        # 文章DIO
        try:
            p = re.compile('\d+\.\d+/.+')
            ArticleDIO = p.findall(BeautifulSoup(Article.find_element(By.TAG_NAME, 'h3').get_attribute('outerHTML'), features="lxml").a['href'])[0]
        except:
            print('DIO提取报错')
            ArticleDIO = '缺失'

        # 获取PDF链接，并下载
        ## 自带PDF链接
        try:
            ArticleDownUrl = BeautifulSoup(Article.find_element(By.CLASS_NAME, 'gs_ggs.gs_fl').get_attribute('outerHTML'), features="lxml").find('a')['href']
        except:  # 使用SCI-HUB替代
            # TODO 可以尝试更多替代方式
            ArticleDownUrl = 'https://sci-hub.se/%s' % ArticleDIO
        self.DownLoad(ArticleDownUrl, ArticleTitle)

        # 处理引用
        sleep(0.5)
        Article.find_elements(By.CLASS_NAME, 'gs_or_cit.gs_or_btn.gs_nph')[0].click()  # 点击引用
        sleep(0.5)
        soup = BeautifulSoup(self.driver.find_elements(By.ID, 'gs_cit-bdy')[0].find_elements(By.TAG_NAME, 'tr')[0].get_attribute('outerHTML'), features="lxml")
        ArticleRef = soup.text.split('GB/T 7714')[1]
        # 关闭引用
        sleep(0.5)
        self.driver.find_elements(By.XPATH, '//*[@id="gs_cit-x"]/span[1]')[0].click()
        ArticleDetails_List = [ArticleTitle, ArticleURL, ArticleDIO, ArticleRef]

        return ArticleDetails_List

    def DownLoad(self, ArticleDownUrl, ArticleTitle):
        """
        将文件下载至保存目录，且以文章标题命名
        :param: ArticleDownUrl 以pdf结尾的Url
        :param: ArticleTitle   文章标题将成为下载文件的名字
        :return: PDF文件
        """
        send_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
            "Connection": "keep-alive",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8"}
        proxies = {'http': 'http://127.0.0.1:%s' % self.port, 'https': 'http://127.0.0.1:%s' % self.port}
        response = requests.get(ArticleDownUrl, headers=send_headers, proxies=proxies)
        bytes_io = io.BytesIO(response.content)
        with open(self.savePath + "\\" + "%s.PDF" % ArticleTitle, mode='wb') as f:
            f.write(bytes_io.getvalue())
            print('%s.PDF,下载成功！' % ArticleTitle)

    def MainGet(self):
        self.GetDriver('3948')
        ArticleDetails_df = pd.DataFrame({'ArticleTitle': [], 'ArticleURL': [], 'ArticleDIO': [], 'ArticleRef': []})
        for page in range(self.pageNums):
            self.Url = f"https://scholar.google.com.hk/scholar?start={page * 10}&q={self.Keywords}&hl=zh-CN&as_sdt=0,5"
            Articles_df = self.GetArticles_df()
            ArticleDetails_df = pd.concat([ArticleDetails_df, Articles_df])
        ArticleDetails_df = ArticleDetails_df.reset_index(drop=True)
        ArticleDetails_df.to_csv('%s.csv' % self.Keywords, index=False, encoding='utf-8-sig')


if __name__ == '__main__':
    GetArticleClass(1, 'Academy+of+Management+Journal', 'D:\Euclid_Jie\AutoReferences\PDF').MainGet()
