import pathlib

log_dir = pathlib.Path("./log")
init_log_dir = log_dir / "init_log"
data_dir = pathlib.Path("./data")
user_info_dir = data_dir / "users"

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

user_db_path = user_info_dir / "users.db"