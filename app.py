from flask import Flask,render_template,request,jsonify
import sqlite3 as sl
import json,hashlib
import os,pathlib,logging
app = Flask(__name__)

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
        ID INT PRIMARY KEY AUTOINCREMENT,
        USER_NAME TEXT     NOT NULL,
        PASSWORD_SHA256 TEXT NOT NULL,
        LAST_LOGIN_IP   TEXT         ,
        LOGIN BOOLEAN DEFAULT 0         );
                       ''')
    db_con.commit()

# need to be delete
# db_con = sl.connect(user_info_dir / "users.db")
# db_cur = db_con.cursor()

def add_user(user_name:str,password:str,ip:str|None,login_st:bool=False):
    pwd_sha256 = hashlib.sha256(password.encode("utf-8")).hexdigest()
    db_con = sl.connect(user_db_path)
    db_cur = db_con.cursor()
    try:
        db_cur.execute(f'''INSERT INTO USERS (USER_NAME,PASSWORD_SHA256,LAST_LOGIN_IP,LOGIN)
                   VALUES (?,?,?,?)
                   ''',(user_name,pwd_sha256,ip,login_st))
        db_con.commit()

    except sl.IntegrityError:
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
    allow_field = ("user_name","password_sha256","last_login_ip","login","id")

    conditions = []
    params = []
    
    for field,values in kw.items():
        if field not in allow_field:
            logger.info(f"not allowed search key word:{field}. Might meet sql injection")
            return ()
        
        conditions.append(f"{field} = ?")
        params.append(values)

    where = ' AND '.join(conditions)
    sql = f"SELECT id,user_name,password_sha256,last_login_ip,login FROM USERS WHERE {where}"
    db_cur.execute(sql,params)
    rows = db_cur.fetchall()
    db_con.close()
    return [dict(x) for x in rows]

@app.route("/")
def index():
    user_ip = request.remote_addr
    login_status = False
    user_name = "Guest"
    welcome_txt = ""

    # statistics 
    visitor_counter = statistics_j.get("visitor_counter",0) +1
    statistics_j["visitor_counter"] = visitor_counter
    update_statistics(statistics_j=statistics_j)

    # for user in db_cur.execute("SELECT USER_NAME,IP,LOGIN FROM USERS"):
    for user in search_user(last_login_ip=user_ip,login=True):
        login_status = True
        user_name = user["user_name"]
        welcome_txt = f"{user_name}"
    
    return render_template("index.html",login_status=login_status,user_name=user_name,welcome_txt=welcome_txt,visitor_counter=visitor_counter)

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
            db_st = add_user(user_name=username,password=password,ip=request.remote_addr,login_st=False)
            if not db_st:
                logger.info(f"someone failed to sign up.username={username} , db returned with {db_st}")
                logger.debug(f"someone failed to sign up.username={username} , password={password} , db returned with {db_st}")

                return jsonify({
                    "message":"sign up failed.It might be that you used the same username as others"
                }),400
            return jsonify({
                "message":"sign up sucessfully.Please login now"
                }),201
    
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

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

# json.dump(statistics_j,statistics_f)
# statistics_f.close()

# users_f.close()
# db_con.close()