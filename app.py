from flask import Flask,render_template,request,jsonify,redirect,url_for,session
import sqlite3 as sl
import json
import hashlib,uuid
import os,pathlib,logging
import sys,time
import datetime

admin_email_addr = "skl2007814@163.com"

sys.path.append("./")
import article_render

app = Flask(__name__)

app.secret_key = "fbc8b0c6046c8702bc0c5661807655425a52d991315f4f357a47a4c257aa47ea"
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=1)

log_dir = pathlib.Path("./log")
if not os.path.exists(log_dir):
    os.makedirs(log_dir,exist_ok=True)


logger = logging.getLogger("logger")
logger.setLevel(logging.DEBUG)
log_formator = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logging_file = logging.FileHandler(log_dir / "log.txt")
logging_file.setLevel(logging.DEBUG) #logging.INFO)
logging_file.setFormatter(log_formator)

logging_console = logging.StreamHandler()
logging_console.setLevel(logging.WARN)
logging_console.setFormatter(log_formator)

logger.addHandler(logging_file)
logger.addHandler(logging_console)
# logging.basicConfig(
#     level="Debug",
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     filename=log_dir / "log.txt"
#     )

data_dir = pathlib.Path("./data")
user_info_dir = data_dir / "users"
if not os.path.exists(data_dir):
    logger.warning(f"create missing dir {data_dir}")
    os.makedirs(data_dir,exist_ok=True)
if not os.path.exists(user_info_dir):
    logger.warning(f"create missing dir {user_info_dir}")
    os.makedirs(user_info_dir,exist_ok=True)


default_files = {
    data_dir / "statistics.json":{
        "visitor_counter":0
        },
    # user_info_dir / "user.json":[
    #     {
    #         "user_name":"pi_test",
    #         "password_sha256":"unknown",
    #         "last_login_ip":"unknown",
    #         "login":False
    #         }
    #     ]
}
for x in default_files:
    if not os.path.exists(x) or x.stat().st_size == 0:
        logger.warning(f"create missing file:{x}")

        os.makedirs(os.path.dirname(x),exist_ok=True)
        with open(x,'w',encoding='utf-8') as f:
            json.dump(default_files[x],f)

statistic_path=data_dir / "statistics.json"
def get_statistics(statistic_path=data_dir / "statistics.json"):
    try:
        with open(statistic_path,'rt',encoding='utf-8') as f:
            statistics_j = json.load(f)
    except json.JSONDecodeError:
        x = statistic_path
        with open(x,'w',encoding='utf-8') as f:
            json.dump(default_files[x],f)
            statistics_j = default_files[x]
    
    return statistics_j

statistics_j = get_statistics()

def update_statistics(statistics_j,statistics_path=statistic_path):
    with open(statistics_path,'w',encoding='utf-8') as f:
        json.dump(statistics_j,f)

# statistics_f = open("data/statistics.json","w")
# users_f = open("data/users/user.json","a+")
# users_j = json.load(users_f)

user_db_path = user_info_dir / "users.db"
def init_db():
    db_con = sl.connect(user_db_path)
    db_cur = db_con.cursor()
    db_cur.execute('''CREATE TABLE IF NOT EXISTS USERS(
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        USER_NAME TEXT     NOT NULL,
        PASSWORD_SHA256 TEXT NOT NULL,
        LAST_LOGIN_IP   TEXT         ,
        LOGIN BOOLEAN DEFAULT 0      ,
        UUID TEXT UNIQUE NOT NULL    );
                       ''')
    db_con.commit()

allow_field = ("ID","USER_NAME","PASSWORD_SHA256","LAST_LOGIN_IP","LOGIN","UUID")

# need to be delete
# db_con = sl.connect(user_info_dir / "users.db")
# db_cur = db_con.cursor()

def add_user(user_name:str,password:str,ip:str|None,login_st:bool=False):
    pwd_sha256 = hashlib.sha256(password.encode("utf-8")).hexdigest()
    usr_uuid = uuid.uuid4().hex
    db_con = sl.connect(user_db_path)
    db_cur = db_con.cursor()
    try:
        db_cur.execute(f'''INSERT INTO USERS (USER_NAME,PASSWORD_SHA256,LAST_LOGIN_IP,LOGIN,UUID)
                   VALUES (?,?,?,?,?)
                   ''',(user_name,pwd_sha256,ip,login_st,str(usr_uuid),))
        db_con.commit()

    except sl.IntegrityError:
        logger.warning(f"add user {user_name} failed")
        return False
    else:
        logger.info(f"add user:{user_name},ip:{ip}")
        return True
    
    finally:
        
        db_con.close()

def search_user(**kw):
    if not kw:
        logger.debug("disastrous error:use nothing to call func 'search_user(**kw)'.will return nothing")
        return ()
    db_con = sl.connect(user_db_path)
    db_con.row_factory = sl.Row
    db_cur = db_con.cursor()

    conditions = []
    params = []
    
    for field,values in kw.items():
        if field not in allow_field:
            logger.info(f"not allowed search key word:{field}. Might meet sql injection")
            return ()
        
        conditions.append(f"{field} = ?")
        params.append(values)

    where = ' AND '.join(conditions)
    sql = f"SELECT id,user_name,password_sha256,last_login_ip,login,uuid FROM USERS WHERE {where}"
    db_cur.execute(sql,params)
    rows = db_cur.fetchall()
    db_con.close()
    return [dict(x) for x in rows]

def modify_user(user:dict,**new_kv) -> int:
    if not new_kv:
        logger.debug(f"called modify_user() without specify what of user {user} to change")
        return 1

    db_con = sl.connect(user_db_path)
    db_cur = db_con.cursor()
    set_keys = []
    params = []
    for k,v in new_kv.items():
        if k not in allow_field:
            logger.info(f"modify_user(): not allowed key word:{k}. Might meet sql injection")
            continue

        set_keys.append(f"{k} = ?")
        params.append(v)
    if not set_keys:
        logger.info(f"call modify_user() wihthout valid key")
        return -1
        
    
    params.append(user["UUID"])
    sql = f"UPDATE USERS SET {','.join(set_keys)} WHERE UUID = ?"
    try:
        db_cur.execute(sql,params)
        if new_kv.get("LOGIN",-1) != -1: # log for login and logout
            if new_kv.get("LOGIN",-1) == True:#len(new_kv) == 1:
                logger.info(f"user {user['USER_NAME']} log in at {time.asctime(time.localtime())}")
            elif new_kv.get("LOGIN",-1) == False:#len(new_kv) == 1:
                logger.info(f"user {user['USER_NAME']} log out at {time.asctime(time.localtime())}")
            
        logger.info(f"modified user {user}: {new_kv}")
        
    except Exception as e:
        db_con.rollback()
        try:
            rt = search_user(**user)
            if not rt:
                logger.debug(f"cannot reach an inexistent user: {user}")
            
        except:
            logger.error(f"E:cannot search user {user} in database,it might be some disastrous error")
            return -1

        else:
            logger.warning(f"cannot modify user :{e}")
            return 1
        
    else:
        db_con.commit()

    finally:
        db_con.close()

    return 0

def if_user_login(user_ip:str) -> tuple[bool,str]:
    if not session.get("LOGIN", False):
        return False, "Guest"
    
    rt = search_user(LAST_LOGIN_IP=user_ip,LOGIN=True)
    if rt:
        user = rt[0]
        user_name = user["USER_NAME"]

        if user_name != session.get("USER_NAME"):
            return False, "Guest"
        
        login_status = True
        return login_status,user_name
    
    return False, "Guest"

@app.route("/")
def index():
    user_ip = request.remote_addr or 'unknown'
    # login_status = False
    # user_name = "Guest"
    # welcome_txt = ""

    # statistics 
    visitor_counter = statistics_j.get("visitor_counter",0) +1
    statistics_j["visitor_counter"] = visitor_counter
    update_statistics(statistics_j=statistics_j)

    # for user in db_cur.execute("SELECT USER_NAME,IP,LOGIN FROM USERS"):
    # for user in search_user(LAST_LOGIN_IP=user_ip,LOGIN=1):
    #     login_status = True
    #     user_name = user["USER_NAME"]
    login_status,user_name = if_user_login(user_ip=user_ip)
    welcome_txt = f"welcome, {user_name}"


    posts = article_render.article_list

    
    return render_template("index.html",login_status=login_status,user_name=user_name,welcome_txt=welcome_txt,visitor_counter=visitor_counter,posts=posts)

@app.route("/signup", methods=["POST","GET"])
def signup():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        if username and password:
            # users_j.append(
            #     {"user_name":username,
            #     "password_sha256":hashlib.sha256(password.encode('utf-8')).hexdigest(),
            #     "last_login_ip":request.remote_addr,
            #     "login":False
            #     }
            # )
            # json.dump(users_j,users_f)
            # users_f.flush()
            rt = search_user(USER_NAME=username)
            if rt:
                return redirect(url_for("status_info_page", status_code="signup_failed_samename")), 302
            db_st = add_user(user_name=username,password=password,ip=request.remote_addr,login_st=False)
            if not db_st:
                logger.info(f"someone failed to sign up.username={username} , db returned with {db_st}")
                logger.debug(f"someone failed to sign up.username={username} , password={password} , db returned with {db_st}")

                return jsonify({
                    "message":"sign up failed.It might be that you used the same username as others"
                }),400
            # redirect to a signup success info page which will auto-redirect again
            return redirect(url_for("status_info_page", status_code="signup_success")), 302
    
        else:
            return jsonify({
                "message":"sign up failed.It might be that you hadn't provide both username and password"
            }),400
    
    elif request.method == 'GET':
        # username = request.form.get("username")
        # password = request.form.get("password")

        # if username and password:
        #    users_j.append(
        #        {"user_name":username,
        #        "password_sha256":hashlib.sha256(password.encode('utf-8')).hexdigest(),
        #        "last_login_ip":request.remote_addr,
        #        "login":False
        #        }
        #    )
           return render_template("signup.html"),200
    else:
        return jsonify({"message":"unsupport http method"}),405


@app.route("/signin",methods=["POST","GET"])
def signin():
    if request.method == 'POST':
        user_name = request.form.get("username")
        password = request.form.get("password") or ""
        pwd_sha256 = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if user_name and password:
            rt = search_user(USER_NAME=user_name)
            if rt:
                user = rt[0]
                if user["PASSWORD_SHA256"] == pwd_sha256:
                    st = modify_user(user,LAST_LOGIN_IP=request.remote_addr,LOGIN=True)
                    if st:
                        return jsonify({"message":"sign in failed.Please get in touch with admin and report it"}),500

                    # successed to login
                    session["USER_NAME"] = user["USER_NAME"]
                    session["UUID"] = user["UUID"]
                    session["LOGIN"] = True
                    ####debug
                    # logger.info(f"INFO: {user["USER_NAME"]} logged in.session:{session}")
                     
                    return redirect(url_for("index"),code=301)
                
                else:
                    return jsonify({"message":"cannot login.your password might be wrong"}),403
                # jsonify({"message":"sign in sucessfully.will redirect to index page soon"})

            logger.info(f"someone login failed.username={user_name},ip={request.remote_addr}")    
            return jsonify({"message":"cannot find this user.your username or password might be wrong"}),403

        else:
            logger.info(f"someone login failed.username={user_name},ip={request.remote_addr}")    
            return jsonify({"message":"cannot find this user.miss username or password"}),403
        
    elif request.method == 'GET':
        return render_template("signin.html"),200
    
    else:
        return jsonify({"message":"unsupport http method"}),405


@app.route("/logout")
def logout():
    user_ip = request.remote_addr or 'unknown'
    rt = search_user(LAST_LOGIN_IP=user_ip,LOGIN=True)
    if not ( rt 
            and ("USER_NAME" in session) 
            and session.get("LOGIN",False) 
            and (session.get("USER_NAME") == rt[0]["USER_NAME"]) 
            ):
        
        return jsonify({
            "message": "You haven't logged in yet.",
        }),400
    
    user = rt[0]
    user_name = user["USER_NAME"]
    st = modify_user(user,LOGIN=False)
    session["LOGIN"] = False
    del session["UUID"]
    del session["USER_NAME"]
    ####debug
    # logger.info(f"{user_name} logged out {session}")
    return redirect(url_for("index")),302

@app.route("/profile")
def profile():
    user_ip = request.remote_addr or "unknown"
    rt = search_user(LAST_LOGIN_IP=user_ip,LOGIN=True)
    if not ( rt 
            and ("USER_NAME" in session) 
            and session.get("LOGIN",False) 
            and (session.get("USER_NAME") == rt[0]["USER_NAME"]) 
            ):
        
        return redirect(url_for("signin")),302

    visitor_counter = statistics_j.get("visitor_counter",0) +1
    statistics_j["visitor_counter"] = visitor_counter
    update_statistics(statistics_j=statistics_j)

    user = rt[0]
    avatar_img = user.get("AVATAR_IMG","/static/default_avatar_512x512.png")
    posts = article_render.article_list
    return render_template("profile.html",user_name=user["USER_NAME"],email="unknown",login_status=user["LOGIN"],avatar_img=avatar_img,posts=posts,visitor_counter=visitor_counter),200

@app.route("/craft")
def craft():
    user_ip = request.remote_addr or "unknown"
    rt = search_user(LAST_LOGIN_IP=user_ip,LOGIN=True)
    if not ( rt 
            and ("USER_NAME" in session) 
            and session.get("LOGIN",False) 
            and (session.get("USER_NAME") == rt[0]["USER_NAME"]) 
            ):
        
        return redirect(url_for("signin")),302

    visitor_counter = statistics_j.get("visitor_counter",0) +1
    statistics_j["visitor_counter"] = visitor_counter
    update_statistics(statistics_j=statistics_j)

    user = rt[0]
    avatar_img = user.get("AVATAR_IMG","/static/default_avatar_512x512.png")
    posts = article_render.article_list
    return render_template("craft.html",user_name=user["USER_NAME"],email="unknown",login_status=user["LOGIN"],avatar_img=avatar_img,posts=posts,visitor_counter=visitor_counter),200


@app.route("/infopage_404")
def page_404():
    return render_template("status_info_page/404.html"), 404

@app.route("/articles")
def articles():
    # user_ip = request.remote_addr or 'unknown'

    # statistics 
    visitor_counter = statistics_j.get("visitor_counter",0) +1
    statistics_j["visitor_counter"] = visitor_counter
    update_statistics(statistics_j=statistics_j)

    # login_status,user_name = if_user_login(user_ip=user_ip)

    login_status = session.get("LOGIN", False)
    user_name = session.get("USER_NAME", "Guest")

    welcome_txt = f"welcome, {user_name}"

    article_list = article_render.article_list
    posts = article_list #[{"title":x.title,"author":x.author,"date":x.date} for x in article_list]
    return render_template("articles.html",posts=posts,visitor_counter=visitor_counter,login_status=login_status,welcome_txt=welcome_txt)


# @app.route("/article/<article_name>")
# def article(article_name):
#     arti,st = article_render.render(article_name)#enable_cache=False)
#     posts = article_render.article_list
    
#     # statistics 
#     visitor_counter = statistics_j.get("visitor_counter",0) +1
#     statistics_j["visitor_counter"] = visitor_counter
#     update_statistics(statistics_j=statistics_j)
    
#     if st == 200:
#         login_status,user_name = if_user_login(request.remote_addr or 'unknown')
#         return render_template("article.html",**arti,login_status=login_status,welcome_txt=f"welcome, {user_name}",posts=posts)
    
#     elif st == 404:
#         return render_template("status_info_page/404.html"), 404
#     elif st == 503:
#         return redirect(url_for("status_info_page", status_code=503)),503
#     else:
#         return redirect(url_for("status_info_page", status_code=503)),503

@app.route("/article/<article_name>")
def article(article_name):
    arti,st = article_render.get_article(article_name)#enable_cache=False)
    posts = article_render.article_list
    artiinfo = {
                'article_content':article_render.markupsafe.Markup(arti.render_result),
                'article_title':arti.title,
                'article_author':arti.author,
                'article_update_date':arti.date,
                'article_update_time':arti.date,
                #'article_create_date':article_path.stat().st_birthtime,
        }
    # statistics 
    visitor_counter = statistics_j.get("visitor_counter",0) +1
    statistics_j["visitor_counter"] = visitor_counter
    update_statistics(statistics_j=statistics_j)
    arti_render_result = arti.render_result
    if st == 200:
        login_status,user_name = if_user_login(request.remote_addr or 'unknown')
        return render_template("article.html",**arti_render_result,login_status=login_status,welcome_txt=f"welcome, {user_name}",posts=posts)
    
    elif st == 404:
        return render_template("status_info_page/404.html"), 404
    elif st == 503:
        return redirect(url_for("status_info_page", status_code=503)),503
    else:
        return redirect(url_for("status_info_page", status_code=503)),503

@app.route("/status_info_page/<status_code>")
def status_info_page(status_code):
    posts = article_render.article_list
    # args = dict(request.args)
    super_page = request.args.get("super_page",'/')
    super_page_name = request.args.get("super_page_name",'index')

    tpl_path = pathlib.Path(f"./templates/status_info_page/{status_code}.html")

    if tpl_path.exists():
        try:
            code = int(status_code)
        except ValueError:
            # named page (like signup_success) — return 200
            visitor_counter = statistics_j.get("visitor_counter",0) +1
            statistics_j["visitor_counter"] = visitor_counter
            update_statistics(statistics_j=statistics_j)
            return render_template(f"status_info_page/{status_code}.html",posts=posts,visitor_counter=visitor_counter,super_page=super_page,super_page_name=super_page_name),200
        else:
            return render_template(f"status_info_page/{status_code}.html",posts=posts,super_page=super_page,super_page_name=super_page_name),code

    else:
        if status_code == 404:
            logger.error("ERROR:cannot found 404 page on server!")
            return f"""<!DOCTYPE html>
            <html>
            <head>
              <title>disastrous 404 error</title>
              <meta charset='utf-8'>
            </head>
            <body>
              <h1>CANNOT FOUND 404 PAGE ON SERVER</h1>
              <p>please <a href="mailto:{admin_email_addr}">contact the admin</a></p>
            </body>
            </html>"""
        
        return redirect(url_for("status_info_page", status_code=404)),404

@app.route("/componets/<comp_id>")
def componets(comp_id:str):
    comp_ids = comp_id.split('-')
    comp_file_path = pathlib.Path('./templates') / 'componets' /comp_ids[0] / (comp_ids[1]+'.html')
    if not comp_file_path.exists():
        logger.debug(f"error:could not get componet: {comp_file_path}")
        return redirect(url_for("status_info_page", status_code=404)),404
        
    
    return render_template(f"componets/{comp_ids[0]}/{comp_ids[1]+'.html'}"),200

@app.route("/submit_article_text", methods=["POST"])
def submit_article_text():
    user_ip = request.remote_addr or "unknown"
    if user_ip == "unknown" or "USER_NAME" not in session:
        return jsonify({
            "msg": "you cannot submit your text as we cannot know who are you according to the ip_address",
            "status": "failed"
        })
    
    rt = search_user(LAST_LOGIN_IP=user_ip)
    if not ( rt 
            and ("USER_NAME" in session) 
            and session.get("LOGIN",False) 
            and (session.get("USER_NAME") == rt[0]["USER_NAME"]) 
            ):
        
        logger.debug(f"err: unknown user tried to submit text edited by the embeded text editor. ip={user_ip}")
        return jsonify({
            "msg": "you cannot submit your text as we cannot know who are you",
            "status": "failed"
        })
    
    user = rt[0]
    editor_content = request.form.get("content")
    if not editor_content:
        return jsonify({
        "msg":"cannot submit empty text",
        "status": "failed"
        })
    
    # get metadata
    article_metadata = article_render.extract_metadata_from_text(editor_content)
    article_metadata["article_title"] = request.form.get("article_title") or article_metadata["article_title"] # try to replace auto gennerated title with user given title

    # save article
    stcode = article_render.save_new_post_by_text(article_name=article_metadata["article_title"],article_text=editor_content,article_author=user["USER_NAME"],metadata=article_metadata,tpe='html')
    if stcode != 0:
        return jsonify({
            "msg":"cannot submit",
            "status": "failed",
            "err_code": stcode,
            "desc": article_render.errcode_table["save_new_post_by_text"].get(stcode,"undefined")
        })
    return redirect(url_for("status_info_page", status_code="submit_article_successful", super_page='/craft', super_page_name='craft')), 302
    # return jsonify({
    #     "msg":"sucessfully submitted text",
    #     "status": "succeeded"
    #     })


@app.route("/upload",methods=["GET", "POST"])
def upload():
    user_ip = request.remote_addr or "unknown"
    rt = search_user(LAST_LOGIN_IP=user_ip,LOGIN=True)
    if not ( rt 
            and ("USER_NAME" in session) 
            and session.get("LOGIN",False) 
            and (session.get("USER_NAME") == rt[0]["USER_NAME"]) 
            ):
        
        return redirect(url_for("signin")),302

    visitor_counter = statistics_j.get("visitor_counter",0) +1
    statistics_j["visitor_counter"] = visitor_counter
    update_statistics(statistics_j=statistics_j)

    user = rt[0]
    avatar_img = user.get("AVATAR_IMG","/static/default_avatar_512x512.png")
    user_upload_dir = data_dir / "user_uploads" / user.get("USER_NAME", "unknown")
    os.makedirs(user_upload_dir, exist_ok=True)

    if request.method == "GET":
        return render_template("upload.html",user_name=user["USER_NAME"],email="unknown",login_status=user["LOGIN"],avatar_img=avatar_img,visitor_counter=visitor_counter),200

    elif request.method == "POST":
        upload_file = request.files.get("file")
        if not upload_file:
            return jsonify({
            "msg":"cannot submit empty file",
            "status": "failed"
            })

        filename = upload_file.filename
        upload_file.save(user_upload_dir / filename)

    else:
        return jsonify({"mesage":"unsupport http method"}),405
    
    return redirect(url_for("status_info_page", status_code="submit_file_successful", super_page='/upload', super_page_name='upload file')), 302

# this part is for wechat link verification only
@app.route("/c3f7f7f887b6468bf55102f1b6f8621d.txt")
def c3f7f7f887b6468bf55102f1b6f8621d_txt():
    return "2158aedb7ac5f7a8fa26ff739e025d3a0bbdb102",200


if __name__ == '__main__':
    init_db()
    app.run(debug=True,port=2000,host='0.0.0.0')

# json.dump(statistics_j,statistics_f)
# statistics_f.close()

# users_f.close()
# db_con.close()
