import sqlite3 as sl
import hashlib,uuid


class User_mgr:
    def __init__(self):
        pass
    def add_user(self,user_name:str,password:str,ip:str|None,login_st:bool=False):
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

    def search_user(self,**kw):
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

    def modify_user(self,user:dict,**new_kv) -> int:
        if not new_kv:
            logger.debug(f"called modify_user() without specify what of user {user} to change")
            return 1

        db_con = sl.connect(user_db_path)
        db_cur = db_con.cursor()
        set_keys = []
        params = []
        for k,v in new_kv.items():
            if k not in allow_field:
                logger.info(f"midify_user(): not allowed key word:{k}. Might meet sql injection")
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
            if new_kv.get("LOGIN",-1) != -1 and len(new_kv) == 1:
                logger.info(f"user {user['USER_NAME']} log in at {time.asctime(time.localtime())}")

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


class User:
    def __init__(self,):
        pass

    