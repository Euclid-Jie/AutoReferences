# 谷歌学术-一键下载

项目初心：为伍女士学术之铺下第一块砖

涉及到主要技术为selenium、需要能够科学上网

- 使用谷歌学术，传入模糊的文献引用，自动获取正确的引文格式。只为采彩而做！
- 指定关键词，下载符合条件论文的数据

## 代码结构

```python
GetRef.py  ## 匹配引用
GetArticleClass.py  ## 指定关键词下载论文
```

## 示例数据

```python
OldRef.csv  # 传入的模糊论文引用
out.csv  # 自动获取的正确的引文格式
HumanRelations.csv  # 下载的论文数据
```

# 输出内容

| 名称            | 含义                                   |
| --------------- | -------------------------------------- |
| ArticleTitle    | 文章的名字                             |
| ArticleURL      | 文章的主页                             |
| ArticleDownUrl  | 文章的下载链接（SCIHUB）               |
| ArticleDownUrl0 | 文章的下载链接（备选，谷歌学术、cdn1） |
| ArticleDIO      | 文章的DIO号                            |
| ArticleRef      | 文章的GB/T 7714格式引文                |

## 调用方式

- GetRef直接运行，选择输入文件（表头与例子相符）

- GetArticleClass传入参数，需要设置代理端口（科学上网）

  | 参数名   | 含义                         |
  | -------- | ---------------------------- |
  | begin    | 开始页                       |
  | pageNums | 需要的总页数                 |
  | Keywords | 搜索的关键词（可以为表达式） |
  | fileName | 输出的文件名（含后缀）       |

  

