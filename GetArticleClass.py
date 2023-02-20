# -*- coding: utf-8 -*-
# @Time    : 2022/11/25 11:28
# @Author  : Euclid-Jie
# @File    : GetArticleClass.py
import os
import re
import pandas as pd
from selenium.webdriver import Chrome, ChromeOptions  # 导入类库
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from time import sleep
import requests
from tqdm import tqdm


class GetArticleClass(object):
    """
    旨在建立一个下载谷歌学术文献的工具
    考虑了部分无直接下载链接的使用SCI-HUB补充下载
    同步下载谷歌学术的GB/T 7714格式引文
    """

    def __init__(self, begin, pageNums, Keywords, fileName):
        """
        :param pageNums: 需要获取的页数 int
        :param Keywords: 搜索框的关键词 str
        :param fileName: 保存文件的名称 str 例如'Euclid'
        """
        self.port = None
        self.Url = None
        self.driver = None
        self.begin = begin
        self.pageNums = pageNums
        self.Keywords = Keywords
        self.fileName = fileName

    def GetDriver(self):
        """
        新开一个chrome, 并打开谷歌学术网站 https://scholar.google.com, 如果不能访问, 请设置梯子
        此函数实现Chrome的接管
        :return: self.driver
        """
        option = ChromeOptions()  # 初始化浏览器设置
        option.add_experimental_option("debuggerAddress", "127.0.0.1:9223")  # 接管
        self.driver = Chrome(options=option)  # 模拟开浏览器

    def GetArticles_df(self):
        """
        根据Url获取当前页面上所有Article的信息
        :return:
        """
        ArticleList = self.driver.find_elements(By.CLASS_NAME, 'gs_r.gs_or.gs_scl')
        num = 0
        for Article in ArticleList:
            ArticleDetails_List = self.GetArticleDetails(Article)
            Article_df = pd.DataFrame({'ArticleTitle': [ArticleDetails_List[0]], 'ArticleType': [ArticleDetails_List[1]], 'ArticleURL': [ArticleDetails_List[2]],
                                       'ArticleDownUrl': [ArticleDetails_List[3]], 'ArticleDownUrl0': [ArticleDetails_List[4]],
                                       'ArticleDIO': [ArticleDetails_List[5]], 'ArticleRef': [ArticleDetails_List[6]]})
            Article_df.to_csv('%s.csv' % self.fileName, index=False, header=False, mode='a', encoding='utf-8-sig')
            num += 1
            self.t.set_postfix({"状态": "已写num:{}".format(num)})  # 进度条右边显示信息

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
        # 图书, PDF
        try:
            ArticleType = Article.find_element(By.CLASS_NAME, 'gs_ct1').text
        except:
            ArticleType = ''

        # 文章名+文章首页
        ArticleTitle = Article.find_element(By.TAG_NAME, "h3").text.replace(ArticleType, '')

        # url
        try:
            ArticleURL = Article.find_element(By.TAG_NAME, "h3").find_element(By.TAG_NAME, 'a').get_attribute('href')
        except:
            ArticleURL = ''

        # 从href提取文章DIO, 目前考虑几种情况
        # 1、https://www.emerald.com/insight/content/doi/10.1108/09534819910263668/full/html
        # 2、https://www.tandfonline.com/doi/abs/10.1080/09557571.2018.1508203
        # 3、https://journals.sagepub.com/doi/pdf/10.1177/0002764212463361
        # 4、
        try:
            p = re.compile('\d+\.\d+/.+')
            ArticleDIO = p.findall(ArticleURL)[0].replace('/full/html', '')
        except:
            ArticleDIO = ''

        # 获取PDF链接
        ## 自带PDF链接
        try:
            ArticleDownUrl0 = BeautifulSoup(Article.find_element(By.CLASS_NAME, 'gs_ggs.gs_fl').get_attribute('outerHTML'), features="lxml").find('a')['href']
            try:
                p = re.compile('\d+\.\d+/.+')
                ArticleDIO = p.findall(ArticleDownUrl0)[0].replace('/full/html', '')
            except:
                ArticleDIO = ''

        ## 如果没有自带的, 使用DOI获取
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
        ArticleDetails_List = [ArticleTitle, ArticleType, ArticleURL, ArticleDownUrl, ArticleDownUrl0, ArticleDIO, ArticleRef]

        return ArticleDetails_List

    def getDownUrl_SCIHUB(self, DIO):
        """
        从SCIHUB上搜索DIO，返回下载链接
        :param DIO:
        :return:
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
            # "Connection": "keep-alive",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8"}
        proxies = {'http': 'http://127.0.0.1:12345', 'https': 'http://127.0.0.1:12345'}
        response = requests.get('https://sci-hub.se/%s' % DIO, headers=headers, proxies=proxies)
        p = re.compile('//.+(?=\?download)')
        try:
            ArticleDownUrl = 'https:' + p.findall(BeautifulSoup(response.content, features="lxml").button['onclick'])[0]
        except:
            ArticleDownUrl = 'https://sci-hub.se/%s' % DIO
        return ArticleDownUrl

    def MainGet(self):
        self.GetDriver()
        ArticleDetails_df = pd.DataFrame({'ArticleTitle': [], 'ArticleType': [], 'ArticleURL': [], 'ArticleDownUrl': [],
                                          'ArticleDownUrl0': [], 'ArticleDIO': [], 'ArticleRef': []})
        # 不存在文件则创建
        if not os.path.exists('%s.csv' % self.fileName):
            ArticleDetails_df.to_csv('%s.csv' % self.fileName, index=False, encoding='utf-8-sig')
        with tqdm(range(self.begin, self.pageNums)) as self.t:
            for page in self.t:
                self.t.set_description("page:{}".format(page))  # 进度条左边显示信息
                self.GetArticles_df()
                sleep(3)
                self.driver.find_elements(By.LINK_TEXT, "下一页")[0].click()


if __name__ == '__main__':
    # GetArticleClass(26, 'SHRM OR "strategic HRM" OR "strategic HR" OR"strategic human resource management" AND source:"Academy of Management Journal"',
    # 'AcademyOfManagementJournal').MainGet() 'SHRM OR "strategic HRM" OR "strategic HR" OR"strategic human resource management" AND source:"Journal of Applied Psychology"'
    GetArticleClass(6, 100, 'allintitle: climate for change', 'climate for change_2').MainGet()
