import os,pathlib
import sys,logging
import json
import sqlite3 as sl

sys.path.append("./")
from config import *
# init the logger of init.py

logger = logging.getLogger("init_logger")
logger.setLevel(logging.DEBUG)
log_formator = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logging_file = logging.FileHandler(init_log_dir / "log.txt")
logging_file.setLevel(logging.DEBUG) #logging.INFO)
logging_file.setFormatter(log_formator)

logging_console = logging.StreamHandler()
logging_console.setLevel(logging.WARN)
logging_console.setFormatter(log_formator)

logger.addHandler(logging_file)
logger.addHandler(logging_console)

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

init_db()