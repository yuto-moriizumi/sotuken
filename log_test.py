import os
import sys
from datetime import datetime
import logging
from logging import StreamHandler, FileHandler, Formatter
from logging import INFO, DEBUG, NOTSET

# ストリームハンドラの設定
stream_handler = StreamHandler()
stream_handler.setLevel(INFO)
stream_handler.setFormatter(Formatter("%(message)s"))

# 保存先の有無チェック
if not os.path.isdir('./Log'):
    os.makedirs('./Log', exist_ok=True)

# ファイルハンドラの設定
file_handler = FileHandler(
    f"./Log/log{datetime.now():%Y%m%d%H%M%S}.log"
)
file_handler.setLevel(DEBUG)
file_handler.setFormatter(
    Formatter(
        "%(asctime)s@ %(name)s [%(levelname)s] %(funcName)s: %(message)s")
)

# ルートロガーの設定
logging.basicConfig(level=NOTSET, handlers=[stream_handler, file_handler])

logger = logging.getLogger(__name__)

logger.debug("debug")
logger.info("info")
logger.warn("warn")
logger.error("error")
logger.critical("critical")
