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
import requests
from tqdm import tqdm


class GetArticleClass(object):
    """
    旨在建立一个下载谷歌学术文献的工具
    考虑了部分无直接下载链接的使用SCI-HUB补充下载
    同步下载谷歌学术的GB/T 7714格式引文
    """

    def __init__(self, pageNums, Keywords, fileName):
        """
        :param pageNums: 需要获取的页数 int
        :param Keywords: 搜索框的关键词 str
        :param fileName: 保存文件的名称 str 例如'Euclid'
        """
        self.port = None
        self.Url = None
        self.driver = None
        self.pageNums = pageNums
        self.Keywords = Keywords
        self.fileName = fileName

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

        for Article in ArticleList:
            ArticleDetails_List = self.GetArticleDetails(Article)
            Article_df = pd.DataFrame({'ArticleTitle': [ArticleDetails_List[0]], 'ArticleURL': [ArticleDetails_List[1]],
                                       'ArticleDownUrl': [ArticleDetails_List[2]], 'ArticleDownUrl0': [ArticleDetails_List[3]],
                                       'ArticleDIO': [ArticleDetails_List[4]], 'ArticleRef': [ArticleDetails_List[5]]})
            Article_df.to_csv('%s.csv' % self.fileName, index=False, header=False, mode='a', encoding='utf-8-sig')

    def GetArticleDetails(self, Article):
        """
        :param: Article每一篇文章，selenium对象
        根据每一篇文章，获取其详细信息
        :return: ArticleDetails_List具体包括：
                ArticleTitle: 文章标题
                ArticleURL: 文章首页
                ArticleDownUrl: SCIHUB下载链接
                ArticleDownUrl0: 谷歌学术下载链接
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
            ArticleDIO = ''

        # 获取PDF链接
        ## 自带PDF链接
        try:
            ArticleDownUrl0 = BeautifulSoup(Article.find_element(By.CLASS_NAME, 'gs_ggs.gs_fl').get_attribute('outerHTML'), features="lxml").find('a')['href']
        except:
            if ArticleDIO == '':
                ArticleDownUrl0 = ''
            else:
                ArticleDownUrl0 = 'https://cdn1.booksdl.org/index.php?req=' + ArticleDIO

        ## SCIHUB下载链接
        if ArticleDIO == '':
            ArticleDownUrl = ''
        else:
            ArticleDownUrl = self.getDownUrl_SCIHUB(ArticleDIO)

        # 处理引用
        sleep(0.5)
        Article.find_elements(By.CLASS_NAME, 'gs_or_cit.gs_or_btn.gs_nph')[0].click()  # 点击引用
        sleep(0.5)
        soup = BeautifulSoup(self.driver.find_elements(By.ID, 'gs_cit-bdy')[0].find_elements(By.TAG_NAME, 'tr')[0].get_attribute('outerHTML'), features="lxml")
        ArticleRef = soup.text.split('GB/T 7714')[1]
        # 关闭引用
        sleep(0.5)
        try:
            self.driver.find_elements(By.XPATH, '//*[@id="gs_cit-x"]/span[1]')[0].click()
        except:
            pass
        ArticleDetails_List = [ArticleTitle, ArticleURL, ArticleDownUrl, ArticleDownUrl0, ArticleDIO, ArticleRef]

        return ArticleDetails_List

    def getDownUrl_SCIHUB(self, DIO):
        """
        从SCIHUB上搜索DIO，返回下载链接
        :param DIO:
        :return:
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
            "Connection": "keep-alive",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8"}
        proxies = {'http': 'http://127.0.0.1:%s' % self.port, 'https': 'http://127.0.0.1:%s' % self.port}
        response = requests.get('https://sci-hub.se/%s' % DIO, headers=headers, proxies=proxies)
        p = re.compile('//.+(?=\?download)')
        try:
            ArticleDownUrl = 'https:' + p.findall(BeautifulSoup(response.content, features="lxml").button['onclick'])[0]
        except:
            ArticleDownUrl = 'https://sci-hub.se/%s' % DIO
        return ArticleDownUrl

    def MainGet(self):
        self.GetDriver('12345')
        ArticleDetails_df = pd.DataFrame({'ArticleTitle': [], 'ArticleURL': [], 'ArticleDownUrl': [],
                                          'ArticleDownUrl0': [], 'ArticleDIO': [], 'ArticleRef': []})
        try:
            ArticleDetails_df.to_csv('%s.csv' % self.fileName, index=False, header=False, mode = 'a', encoding='utf-8-sig')
        except:
            ArticleDetails_df.to_csv('%s.csv' % self.fileName, index=False, header=True, mode = 'w', encoding='utf-8-sig')

        for page in tqdm(range(self.pageNums)):
            self.Url = f"https://scholar.google.com.hk/scholar?start={page * 10}&q={self.Keywords}&hl=zh-CN&as_sdt=0,5"
            self.GetArticles_df()



if __name__ == '__main__':
    # GetArticleClass(26, 'SHRM OR "strategic HRM" OR "strategic HR" OR"strategic human resource management" AND source:"Academy of Management Journal"',
    #                 'AcademyOfManagementJournal').MainGet()
    # 'SHRM OR "strategic HRM" OR "strategic HR" OR"strategic human resource management" AND source:"Journal of Applied Psychology"'
    GetArticleClass(16, 'SHRM OR "strategic HRM" OR "strategic HR" OR"strategic human resource management" AND source:"Human Relations"', 'HumanRelations').MainGet()
