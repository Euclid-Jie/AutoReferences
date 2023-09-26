# -*- coding: utf-8 -*-
# @Time    : 2022/11/23 17:39
# @Author  : Euclid-Jie
# @File    : GetRef.py
import time
import os
import pandas as pd
from bs4 import BeautifulSoup  # 导入类库
import re
from selenium.webdriver import Chrome, ChromeOptions  # 导入类库
from selenium.webdriver.common.by import By
from selenium import webdriver
import tkinter as tk
from tkinter import filedialog


def getLocalFile():
    root = tk.Tk()
    root.withdraw()
    filePath = filedialog.askopenfilename()
    print('文件路径：', filePath)
    return filePath


def getNewRef(driver, OldRef_str):
    baseUrl = "https://scholar.google.com.hk/scholar?hl=zh-CN&q="
    try:
        p = re.compile("(?<=\.).+(?=\[)")
        Url = baseUrl + p.findall(OldRef_str)[0]
    except:
        Url = baseUrl + OldRef_str
    driver.get(Url)  # 跳转网址
    driver.find_elements(By.CLASS_NAME, "gs_or_cit.gs_or_btn.gs_nph")[0].find_elements(
        By.TAG_NAME, "span"
    )[0].click()
    time.sleep(1)
    html = (
        driver.find_elements(By.ID, "gs_cit-bdy")[0]
        .find_elements(By.TAG_NAME, "tr")[2]
        .get_attribute("outerHTML")
    )
    soup = BeautifulSoup(html, features="lxml")
    if "APA" in soup.text:
        NewRef_str = soup.text.split("APA")[1]
        return NewRef_str
    else:
        return ""


if __name__ == "__main__":
    options = webdriver.ChromeOptions()
    ip = "127.0.0.1"
    port = "12345"
    # 设置代理
    options.add_argument("--proxy-server=http://{}:{}".format(ip, port))
    driver = Chrome(options=options)  # 模拟开浏览器

    filePath = getLocalFile()
    df = pd.read_csv(filePath)
    out_df = df.copy()
    for index in df.index:
        refi = df.iloc[index].values[0]
        NewRef = getNewRef(driver, refi)
        out_df['NewRef'][index] = NewRef
    out_df.to_csv('out.csv', index=False, encoding='utf-8-sig')
