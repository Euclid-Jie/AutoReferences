# -*- coding: utf-8 -*-
# @Time    : 2023/2/18 22:05
# @Author  : Euclid-Jie
# @File    : DownloadPaper_from_DOI.py
import os.path
import time

import pandas as pd
import requests
from selenium.webdriver import Chrome, ChromeOptions  # 导入类库
from tqdm import tqdm

from tkinter import filedialog
import tkinter as tk


def getLocalFile():
    root = tk.Tk()
    root.withdraw()
    filePath = filedialog.askopenfilename()
    print('文件路径：', filePath)
    return filePath


def Down_PDF_from_DOI(DOI):
    option = ChromeOptions()  # 初始化浏览器设置
    option.add_experimental_option("debuggerAddress", "127.0.0.1:9222")  # 接管
    driver = Chrome(options=option)  # 模拟开浏览器
    Url = 'https://libgen.rocks/ads.php?doi=' + DOI
    driver.get(Url)
    time.sleep(10)


def Down_PDF_from_pdfUrl(Url, filename, proxies):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.50",
        "cookie": "__ddg1_=UbfVMRuQq3XePdUrSsBk; session=060c469634156ae7ca21bd5a33aa0daf; __ddgid_=vpXuRK6ItgnZOgyR; __ddgmark_=vuLD0vqTueBvybyj; __ddg2_=VkBAKD5eG6fIKP2o; refresh=1676817564.2403"
    }
    r = requests.get(Url, headers=headers, timeout=60, proxies=proxies)
    filename = (filename + '.pdf').replace(' ', '_').replace(':', '_').replace('?', '_')
    with open(os.path.join('PDF', filename), 'wb+') as f:
        f.write(r.content)


filePath = getLocalFile()
# filePath = 'D:/Euclid_Jie/AutoReferences/climate for change_2.csv'
proxies = {'http': 'http://127.0.0.1:12345', 'https': 'http://127.0.0.1:12345'}
# proxies = None
df = pd.read_csv(filePath)
log = open("log_{}.txt".format(int(time.time())), mode="a", encoding="utf-8-sig")
pbar = tqdm(total=len(df))
for index, row in df.iterrows():
    # m默认不下载图书
    if row['ArticleType'] == '[图书]':
        print('图书暂不下载', file=log)
    elif isinstance(row['ArticleDownUrl'], str) and '.pdf' in row['ArticleDownUrl']:
        pdf_name = row['ArticleTitle']
        pdf_url = row['ArticleDownUrl']
        try:
            Down_PDF_from_pdfUrl(pdf_url, pdf_name, proxies)
            print('Down with Url1:{}'.format(pdf_url), file=log)
        except:
            print('Url1无法下载: {}'.format(pdf_name), file=log)
    elif isinstance(row['ArticleDownUrl0'], str) and '.pdf' in row['ArticleDownUrl0']:
        pdf_name = row['ArticleTitle']
        pdf_url = row['ArticleDownUrl0']
        try:
            Down_PDF_from_pdfUrl(pdf_url, pdf_name, proxies)
            print('Down with Url0: {}'.format(pdf_url), file=log)
        except:
            print('Url0无法下载: {}'.format(pdf_name), file=log)
    elif isinstance(row['ArticleDIO'], str):
        DIO = row['ArticleDIO']
        Down_PDF_from_DOI(DIO)
        print('Down with DIO: {}'.format(DIO), file=log)
    else:
        pdf_name = row['ArticleTitle']
        print('无法下载: {}'.format(pdf_name), file=log)
    pbar.update(1)
log.close()
