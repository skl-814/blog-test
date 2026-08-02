import hashlib
import argon2

import inspect

hash_method_available: set[str]= set()
hash_method_available.add("argon2")
for x in hashlib.algorithms_guaranteed:
    hash_method_available.add(x)


def is_hash_func(func) -> bool:
    if not callable(func):
        return False
    
    try:
        sig = inspect.signature(func)
        params = sig.parameters.values()
        if any([p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD) for p in params]):
            return True
        
        return len(params) > 1
    
    except (ValueError, TypeError):
        return True


class Hasher():
    def __init__(self,
                 hash_alg='argon2',
                 hasher=argon2.PasswordHasher(),
                 fn_hash=argon2.PasswordHasher().hash,
                 fn_hash_str=argon2.PasswordHasher().hash,
                 fn_verify=argon2.PasswordHasher().verify
                 ):
        
        # if hash_alg not in hash_method_available:
        #     raise RuntimeError(
        #         f'''err: using a not support hash algorithm: `{hash_alg}`.
        #         please use {__file__}.hash_method_available to get available algorithms'''
        #         )
        
        if hash_alg in hashlib.algorithms_guaranteed:
            self.hash_alg = hash_alg
            self._hasher = hashlib.new(hash_alg,usedforsecurity=True)
            if not fn_hash:
                def uhash(bstr: bytes|bytearray):
                    h = hashlib.new(hash_alg,bstr,usedforsecurity=True)
                    return h.hexdigest()
                self.hash = uhash
            else:
                self.hash = fn_hash
            
            if not fn_hash_str:
                def uhash_str(s: str,encoding='utf-8'):
                    bstr = s.encode(encoding)
                    h = hashlib.new(hash_alg,bstr,usedforsecurity=True)
                    return h.hexdigest()
                self.hash_str = uhash_str
            else:
                self.hash_str = fn_hash_str
            
            if not fn_verify:
                def uhash_verify(hashhex:str,data,encoding='utf-8'):

                    if type(data) == str:
                        bstr = data.encode(encoding)

                    elif type(data) in (bytes,bytearray):
                        bstr = data
                    
                    new_hash = self.hash(bstr)

                    return (new_hash == hash)
                

        elif hash_alg == 'argon2':
            self.hash_alg = hash_alg
            self._hasher = argon2.PasswordHasher()

            if not fn_hash:
                self.hash = argon2.PasswordHasher().hash
            else:
                self.hash = fn_hash

            if not fn_hash_str:
                self.hash_str = self.hash
            else:
                self.hash_str = fn_hash_str
                
            if not fn_verify:
                self.verify = fn_verify
            else:
                self.verify = argon2.PasswordHasher().verify
        else:
            # user added hash algorithms
            self.hash_alg = hash_alg
            self._hasher = None

            if not fn_hash:
                try:
                    self.hash = self._hasher.__getattribute__("hash")

                except:
                    raise RuntimeError(f"It seems that you haven't provide function for calculate hash,and we cannot get it from hasher object.\
                                    Please give parameter `fn_hash` a function")
                
            if not callable(fn_hash): 
                raise TypeError(f"you haven't provide function or suitable callable object for calculate hash but type of {type(fn_hash)}")
                
            
            self.hash = fn_hash

            if not fn_hash_str:
                self.hash_str = self.hash

            else:
                self.hash_str = fn_hash_str
                
            if not fn_verify:
                self.verify = fn_verify

            else:
                self.verify = argon2.PasswordHasher().verify



# argon2

