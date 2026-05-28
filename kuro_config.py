import json
import os
from typing import Dict, Optional
from astrbot.api import logger
from astrbot.core.utils.astrbot_path import get_astrbot_data_path


class KuroConfig:
    def __init__(self):
        self.data_dir = os.path.join(get_astrbot_data_path(), "plugins", "astrbot_plugin_kjqqd")
        self.token_file = os.path.join(self.data_dir, "tokens.json")
        self._ensure_data_dir()
        self._tokens: Dict[str, str] = self._load_tokens()

    def _ensure_data_dir(self):
        try:
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir, exist_ok=True)
                logger.info(f"创建数据目录: {self.data_dir}")
        except Exception as e:
            logger.error(f"创建数据目录失败: {e}")

    def _load_tokens(self) -> Dict[str, str]:
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"解析 tokens.json 失败: {e}，使用空字典")
            return {}
        except Exception as e:
            logger.error(f"加载 tokens.json 失败: {e}")
            return {}

    def _save_tokens(self):
        try:
            with open(self.token_file, "w", encoding="utf-8") as f:
                json.dump(self._tokens, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存 tokens.json 失败: {e}")

    def get_token(self, user_id: str) -> Optional[str]:
        return self._tokens.get(user_id)

    def set_token(self, user_id: str, token: str):
        self._tokens[user_id] = token
        self._save_tokens()
        logger.debug(f"已设置用户 {user_id} 的 token")

    def remove_token(self, user_id: str):
        if user_id in self._tokens:
            del self._tokens[user_id]
            self._save_tokens()
            logger.debug(f"已删除用户 {user_id} 的 token")

    def get_all_tokens(self) -> Dict[str, str]:
        return self._tokens.copy()
