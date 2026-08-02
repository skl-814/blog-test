import sys,time
import random as r
sys.path.append("./")

import hash

def randstr(n: int) ->str:
    ml = r"abcdefghijklmnopqrstuvwxuz1234567890`[]\\ \;',./~!@#$%^&*()_+{}|:\"<>?"
    rt = ""
    for i in range(n):
        rt += r.choice(ml)
    
    return rt

if 'argon2' in hash.hash_method_available:
    hasher = hash.Hasher('argon2')
    length = 1000_1000_00
    test = randstr(length)
    print(f"generated test text: length={length}")
    t1 = time.time()
    h = hasher.hash_str(test)
    t2 = time.time()
    print(f"{h}\n{t2-t1}s")