import os
import pathlib

# import platform,time
# from flask import render_template
import time
import markdown2 as mk
import markupsafe

mker = mk.Markdown(extras=["fenced-code-blocks"])

article_dir = pathlib.Path("./blog_articles")
cache_dir = article_dir / '_cache'

if not article_dir.exists():
    os.makedirs(article_dir,exist_ok=True)

# def cached_render(article_name:str,encoding:str='utf-8',file_type:str='text') -> str|bytes:
#     cached_article_path = cache_dir / article_name
#     if cached_article_path.exists():
#         if file_type == 'text':
#             with open(cached_article_path,'t',encoding=encoding) as f:
#                 return f.read()
        
#         else:
#             with open(cached_article_path,'rb') as f:
#                 return f.read()

class Post_article:
    def __init__(self,title:str,author:str,date:str,file_path:pathlib.Path):
        self.title = title
        self.author = author
        self.date = date
        self.file_path = file_path
        self.guessed_file_type = self.guess_filetype(file_path)
        self.file_type = self.guessed_file_type
        self.abstract = render(article_name=file_path.name,file_type=self.file_type,enable_cache=False)[0]['article_content']
        if len(self.abstract) > 200:
            self.abstract = self.abstract[:200] + "..."

    def guess_filetype(self,file_path:pathlib.Path):
        if file_path.suffix in ('.md','.markdown'):
            return "markdown"
        elif file_path.suffix in ('.txt'):
            return "txt"
        elif file_path.suffix in (".html",".html"):
            return "html"
        else:
            return "txt"

def render(article_name:str,file_type='markdown',enable_cache:bool=True,encoding:str= 'utf-8'):
    if enable_cache and not cache_dir.exists():
        os.makedirs(cache_dir,exist_ok=True)
    cached_article_path = cache_dir / f"{article_name}.html"
    article_path = article_dir / article_name
    if not os.path.exists(article_path):
        return {
            'content':"",
                },404
    
    # currently markdown and plain text only
    atn_l = article_path.name.split(".")[0].split('-')
    article_title = atn_l[0]
    article_author = atn_l[-1]

    if file_type == 'markdown':
        if enable_cache:
            if cached_article_path.exists() and article_path.stat().st_mtime < cached_article_path.stat().st_mtime:
                with open(cached_article_path,'rt',encoding=encoding) as f:
                    article_content = f.read()
            else:
                with open(article_path,'rt',encoding=encoding) as f:
                    with open(cached_article_path,'wt',encoding=encoding) as cache_f:
                        article_content = mker.convert(f.read())
                        cache_f.write(article_content)
                        
        else:
            with open(article_path,'rt',encoding=encoding) as f:
                article_content = mker.convert(f.read())

        return {
                'article_content':markupsafe.Markup(article_content),
                'article_title':article_title,
                'article_author':article_author,
                'article_update_date':article_path.stat().st_mtime,
                #'article_create_date':article_path.stat().st_birthtime,

                },200
    
    elif file_type == 'txt':
        # txt format article don't need to cache
        with open(article_path,'rt',encoding=encoding) as f:
            return {
                'article_content':markupsafe.Markup(f.read()),
                'article_title':article_title,
                'article_author':article_author,
                'article_update_date':article_path.stat().st_mtime,
                #'article_create_date':article_path.stat().st_birthtime,

                },200
    
    elif file_type == 'html':
        with open(article_path,'rt',encoding=encoding) as f:
            return {
                'article_content':markupsafe.Markup(f.read()),
                'article_title':article_title,
                'article_author':article_author,
                'article_update_date':article_path.stat().st_mtime,
                #'article_create_date':article_path.stat().st_birthtime,

                },200
    else:
        return {
            'article_content':markupsafe.Markup("<br><br><h1><strong>not support format</strong><h1><br><br>"),
            'article_title':article_title,
            'article_author':article_author,
            'article_update_date':article_path.stat().st_mtime,
            #'article_create_date':article_path.stat().st_birthtime,

            },503
    

def get_article_list(num:int = 4):
    article_list = []
    for article in article_dir.iterdir():
        if article.is_file() and not article.name.startswith('_'):
            atn_l = article.name.split(".")[0].split('-')
            article_title = atn_l[0]
            article_author = atn_l[-1]
            article_list.append(Post_article(
                title=article_title,
                author=article_author,
                date=time.asctime(time.localtime(article.stat().st_mtime)),
                file_path=article
            ))
    if len(article_list) < num:
        return sorted(article_list,key=lambda x:x.date,reverse=True)
    return sorted(article_list,key=lambda x:x.date,reverse=True)[:num]

article_list:list = get_article_list()


