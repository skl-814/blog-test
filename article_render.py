import os
import pathlib

import markdown2 as mk

from flask import render_template
mker = mk.Markdown()

article_dir = pathlib.Path("./blog_articles")

def render(article_name,file_type='markdwon',encoding:str= 'utf-8'):
    article_path = article_dir / article_name
    if not os.path.exists(article_path):
        return "",404
    
    # currently markdown only
    if file_type == 'markdown':
        with open(article_path,'rt',encoding=encoding) as f:
            return mker.convert(f.read()),200
    
    elif file_type == 'txt':
        with open(article_path,'rt',encoding=encoding) as f:
            return f.read(),200
    else:
        return "not support format",503