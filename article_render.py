import os
import pathlib

# import platform,time
# from flask import render_template
import time
import markdown2 as mk
import markupsafe
import re
mker = mk.Markdown(extras=["fenced-code-blocks","task_list","tables","strike","latex","mermaid","metadata","toc"])

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

def extract_metadata_from_file(article_path:pathlib.Path,tpe:str='md')-> tuple[dict[str,str|bool],int]:
    if not article_path.exists():
        raise FileNotFoundError(f"cannot found file {article_path} while extract metadata")
    if tpe in ("markdown","md"):
        ptn = re.compile(
            r"^---\s*\n"
            r"(.*?)"
            r"\n---\s*$",
            re.DOTALL | re.MULTILINE
            )
        with open(article_path,'rt',encoding='utf-8-sig') as f:
            t = f.read()

        rt = ptn.search(t)
        if not rt:
            return {},0
    
        rt_dict = {}
        for x in rt.group(1).splitlines():
            if ':' in x:
                k,v = x.split(':',maxsplit=1)
                if k and v:
                    rt_dict[k.strip()] = v.strip()

                else:
                    key = x.replace(":",'').strip()
                    if key:
                        rt_dict[key] = "unknown"

            else:
                rt_dict[x.strip()] = True
        if rt.end() >= len(t):
            return rt_dict,0
        return rt_dict,rt.end()
    
    elif tpe in ("html",):
        ptn = re.compile(r"\<\!\-\-(.*?)\-\-\>",re.DOTALL)
        with open(article_path,'rt',encoding='utf-8-sig') as f:
            t = f.read()
        
        rt = ptn.search(t)
        if not rt:
            return {},0
        
        rt_dict = {}
        for x in rt.group(1).splitlines():
            if ':' in x:
                k,v = x.split(':',maxsplit=1)
                if k and v:
                    rt_dict[k.strip()] = v.strip()
                
                else:
                    key = x.replace(":",'').strip()
                    if key:
                        rt_dict[key] = "unknown"
            
            else:
                rt_dict[x.strip()] = True
        
        return rt_dict,rt.end()
    
    else:
        # the condition that we get 'other' file format.assumed to plain text
        ptn = re.compile(r"^\s*(.+?)\s*(?:=\s*(.*?))?\s*$")

        rt_dict = {}
        endpos = 0
        ic = 0
        with open(article_path,'rt',encoding='utf-8-sig') as f:
            for line in f:
                match = re.match(ptn,line)
                if match:
                    key = match.group(1).strip()
                    value = match.group(2)
                    if not value:
                        value = True
            
                    else:
                        value = value.strip()
                        if len(value) >=2 and value[0]==value[-1] in ("'","\""):
                            value = value[1:-1]
            
                    rt_dict[key] = value
                    endpos += len(line)
                    ic += 1
                
                else:
                    break

        return rt_dict,endpos

def extract_metadata_from_text(editor_content:str):
    rt = re.match(r"<h1>(\w.)</h1>",editor_content)
    if rt:
        article_title = rt.groups()[0]
    else:
        article_title = f"new_article_{time.asctime(time.localtime())}".replace(" ","_").replace(":","_")

    store_file_name = article_dir /article_title
    return {
        "article_title": article_title,
        
    }

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
    atn_l = article_path.name.split(".")[0].split('-',maxsplit=1)
    
    metadata,metadata_end = extract_metadata_from_file(article_path,)
    article_title = metadata.get("author",atn_l[0]) # using result from filename if no relevant info in metadata
    article_author = metadata.get("author",atn_l[-1])


    if file_type == 'markdown':
        if enable_cache:
            if cached_article_path.exists() and article_path.stat().st_mtime < cached_article_path.stat().st_mtime:
                with open(cached_article_path,'rt',encoding=encoding) as f:
                    f.seek(metadata_end)
                    article_content = f.read()[metadata_end:]
            else:
                with open(article_path,'rt',encoding=encoding) as f:
                    with open(cached_article_path,'wt',encoding=encoding) as cache_f:
                        article_content = mker.convert(f.read()[metadata_end:])
                        cache_f.write(article_content)
                        
        else:
            with open(article_path,'rt',encoding=encoding) as f:
                article_content = mker.convert(f.read()[metadata_end:])

        return {
                'article_content':markupsafe.Markup(article_content),
                'article_title':article_title,
                'article_author':article_author,
                'article_update_date':time.asctime(time.localtime(article_path.stat().st_mtime)),
                'article_update_time':article_path.stat().st_mtime,
                #'article_create_date':article_path.stat().st_birthtime,

                },200
    
    elif file_type == 'txt':
        # txt format article don't need to cache
        with open(article_path,'rt',encoding=encoding) as f:
            return {
                'article_content':markupsafe.Markup(f.read()[metadata_end:]),
                'article_title':article_title,
                'article_author':article_author,
                'article_update_date':time.asctime(time.localtime(article_path.stat().st_mtime)),
                'article_update_time':article_path.stat().st_mtime,
                #'article_create_date':article_path.stat().st_birthtime,

                },200
    
    elif file_type == 'html':
        with open(article_path,'rt',encoding=encoding) as f:
            # t = f.read()
            # tp = markupsafe.Markup(t)
            return {
                'article_content':markupsafe.Markup(f.read()[metadata_end:]),
                'article_title':article_title,
                'article_author':article_author,
                'article_update_date':time.asctime(time.localtime(article_path.stat().st_mtime)),
                'article_update_time':article_path.stat().st_mtime,
                #'article_create_date':article_path.stat().st_birthtime,

                },200
    else:
        return {
            'article_content':markupsafe.Markup("<br><br><h1><strong>not support format</strong><h1><br><br>"),
            'article_title':article_title,
            'article_author':article_author,
            'article_update_date':time.asctime(time.localtime(article_path.stat().st_mtime)),
            'article_update_time':article_path.stat().st_mtime,
            #'article_create_date':article_path.stat().st_birthtime,

            },503
    
class Post_article:
    def __init__(self,title:str,author:str,date:str|float,file_path:pathlib.Path,ctime:float=0,mtime:float=0):
        self.title:str = self.title_strip(title)
        self.author:str = author

        self.time :float
        self.date :str
        if type(date) == float:
            self.time= date
            self.date= time.asctime(time.localtime(date))

        else:
            self.date= str(date)
            self.time= time.mktime(time.strptime(str(date)))

        self.create_time = ctime or self.time# the create time
        self.modify_time = mtime or self.time# last modified time

        self.file_path:pathlib.Path = file_path
        self.guessed_file_type:str = self.guess_filetype(self.file_path)
        self.file_type:str = self.guessed_file_type

        self.render_result,self.render_status = render(article_name=self.file_path.name,file_type=self.file_type,enable_cache=False)
        self.abstract = self.render_result['article_content']
        if len(self.abstract) > 200:
            self.abstract = self.abstract[:200] + "..."

    def guess_filetype(self,file_path:pathlib.Path):
        if file_path.suffix in ('.md','.markdown'):
            return "markdown"
        elif file_path.suffix in ('.txt'):
            return "txt"
        elif file_path.suffix in (".html",".htm"):
            return "html"
        else:
            return "txt"
    
    def title_strip(self,title=None):
        title = title or self.title
        title = title.strip()
        while title[0] in "_-!@#$%^&*,./\\|":
            title = title[1:]
        
        while title[-1] in "_-!@#$%^&*,./\\|":
            title = title[:-1]
        
        self.title = title
        return self.title

post_article = Post_article(title="_about-skl.md",author="skl",date=(article_dir / "_about-skl.md").stat().st_mtime,file_path=article_dir / "_about-skl.md")
# empty_article = Post_article(title="empty.txt",author=)

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
    if num == -1:
        return sorted(article_list,key=lambda x:x.date,reverse=True)

    if len(article_list) < num:
        return sorted(article_list,key=lambda x:x.date,reverse=True)
        
    return sorted(article_list,key=lambda x:x.date,reverse=True)[:num]

article_list:list = get_article_list()

def get_article(article_filename:str) -> tuple[Post_article,int]:
    article_path = article_dir / article_filename

    atn_l = article_path.name.split(".")[0].split('-')
    article_title = atn_l[0]
    article_author = atn_l[-1]
    article = Post_article(
        title=article_title,
        author=article_author,
        date=time.asctime(time.localtime(article_path.stat().st_mtime)),
        file_path=article_path
    )
    return article,article.render_status
    
def save_new_post_by_text(article_name:str,article_text:str,article_author:str,metadata:dict={},tpe='html'):
    suffix = tpe
    new_article_path = article_dir / f"{article_name}-{article_author}.{suffix}"
    if new_article_path.exists():
        return 1 # fail:already exists
    try:
        if tpe in ("markdown","md"):
            with open(new_article_path,"wt",encoding='utf-8') as f:
                f.write("---\n")
                for k,v in metadata.items():
                    f.write(f"{k}:{v:>4}\n") 

                f.write("---\n")
            
                f.write(article_text)
        
        elif tpe in ("html",):
            # insert metadata into comment
            with open(new_article_path,"wt",encoding='utf-8') as f:
                for k,v in metadata.items():
                    f.write(f"<!--{k}:{v:>4}-->\n")
                
                f.write(article_text)
        else:
            with open(new_article_path,"wt",encoding='utf-8') as f:
                for k,v in metadata.items():
                    f.write(f"{k} = {v:>4}\n")
                
                f.write(article_text)

    except OSError as e:
        raise RuntimeError(f"while saving file {new_article_path}: {e}")
        return 2
    else:
        return 0 #succeed
    
errcode_table = {
    "save_new_post_by_text": {
        0: "sucessful",
        1: "already exists",
        2: "OSError"
    }
}