import sys
import pathlib,os
import logging

sys.path.append("./")
from config import *



########################
# firstly,call init.py #
########################
from init import *

###########################
# then,init pubilc logger #
###########################

# log_dir = pathlib.Path("./log")
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