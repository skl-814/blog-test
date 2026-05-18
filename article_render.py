import os
import pathlib

# import platform,time
# from flask import render_template

import markdown2 as mk

mker = mk.Markdown()

article_dir = pathlib.Path("./blog_articles")
cache_dir = article_dir / '_cache'

# def cached_render(article_name:str,encoding:str='utf-8',file_type:str='text') -> str|bytes:
#     cached_article_path = cache_dir / article_name
#     if cached_article_path.exists():
#         if file_type == 'text':
#             with open(cached_article_path,'t',encoding=encoding) as f:
#                 return f.read()
        
#         else:
#             with open(cached_article_path,'rb') as f:
#                 return f.read()


def render(article_name:str,file_type='markdwon',enable_cache:bool=True,encoding:str= 'utf-8'):
    cached_article_path = cache_dir / f"{article_name}.html"
    article_path = article_dir / article_name
    if not os.path.exists(article_path):
        return {
            'content':"",
                },404
    
    # currently markdown and plain text only
    atn_l = article_name.split('-')
    article_title = atn_l[0]
    article_author = atn_l[1]

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
                'article_content':article_content,
                'article_title':article_title,
                'article_author':article_author,
                'article_update_date':article_path.stat().st_mtime,
                'article_create_date':article_path.stat().st_birthtime,

                },200
    
    elif file_type == 'txt':
        # txt format article don't need to cache
        with open(article_path,'rt',encoding=encoding) as f:
            return {
                'article_content':f.read(),
                'article_title':article_title,
                'article_author':article_author,
                'article_update_date':article_path.stat().st_mtime,
                'article_create_date':article_path.stat().st_birthtime,

                },200
    else:
        return {
            'article_content':"<br><br><h1><strong>not support format</strong><h1><br><br>",
            'article_title':article_title,
            'article_author':article_author,
            'article_update_date':article_path.stat().st_mtime,
            'article_create_date':article_path.stat().st_birthtime,

            },503