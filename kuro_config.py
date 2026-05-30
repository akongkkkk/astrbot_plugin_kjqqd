import json
import os
from typing import Dict, Optional, Any
from astrbot.api import logger
from astrbot.core.utils.astrbot_path import get_astrbot_data_path


class KuroConfig:
    def __init__(self):
        self.data_dir = os.path.join(get_astrbot_data_path(), "plugins", "astrbot_plugin_kjqqd")
        self.token_file = os.path.join(self.data_dir, "tokens.json")
        self.config_file = os.path.join(self.data_dir, "config.json")
        self._ensure_data_dir()
        self._tokens: Dict[str, str] = self._load_tokens()
        self._config: Dict[str, Any] = self._load_config()

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

    def _load_config(self) -> Dict[str, Any]:
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"解析 config.json 失败: {e}")
        except Exception as e:
            logger.error(f"加载 config.json 失败: {e}")
        return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        return {
            "auto_sign_enabled": True,
            "auto_sign_time": "07:00",
            "timezone": "Asia/Shanghai"
        }

    def _save_config(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存 config.json 失败: {e}")

    def get_auto_sign_enabled(self) -> bool:
        return self._config.get("auto_sign_enabled", True)

    def set_auto_sign_enabled(self, enabled: bool):
        self._config["auto_sign_enabled"] = enabled
        self._save_config()
        logger.debug(f"自动签到已{'启用' if enabled else '禁用'}")

    def get_auto_sign_time(self) -> str:
        return self._config.get("auto_sign_time", "07:00")

    def set_auto_sign_time(self, time_str: str):
        if self._validate_time_format(time_str):
            self._config["auto_sign_time"] = time_str
            self._save_config()
            logger.debug(f"自动签到时间已设置为: {time_str}")
        else:
            logger.error(f"无效的时间格式: {time_str}")

    def _validate_time_format(self, time_str: str) -> bool:
        try:
            hours, minutes = map(int, time_str.split(":"))
            return 0 <= hours < 24 and 0 <= minutes < 60
        except (ValueError, AttributeError):
            return False

    def get_config(self) -> Dict[str, Any]:
        return self._config.copy()

    def update_config(self, config: Dict[str, Any]):
        if "auto_sign_enabled" in config:
            self.set_auto_sign_enabled(config["auto_sign_enabled"])
        if "auto_sign_time" in config:
            self.set_auto_sign_time(config["auto_sign_time"])

    def get_last_sign_date(self) -> str:
        return self._config.get("last_sign_date", "")

    def set_last_sign_date(self, date_str: str):
        self._config["last_sign_date"] = date_str
        self._save_config()
