from datetime import datetime
from typing import Dict, Any
from zoneinfo import ZoneInfo
from .kuro_config import KuroConfig
from .kuro_api import KuroAPI
from astrbot.api import logger


class KuroSign:
    def __init__(self, config: KuroConfig, api: KuroAPI):
        self.config = config
        self.api = api

    def _get_beijing_month(self) -> str:
        """获取北京时间当前月份（两位）"""
        beijing_tz = ZoneInfo("Asia/Shanghai")
        beijing_time = datetime.now(beijing_tz)
        return f"{beijing_time.month:02d}"

    async def check_status(self, token: str) -> str:
        """查询签到状态（简化版，先验证 token 有效性）"""
        try:
            # 先验证 token 有效性
            mine_info = await self.api.get_mine_info(token)
            if mine_info.get("code") != 200:
                return f"❌ Token 无效或已过期: {mine_info.get('msg', '请重新绑定 token')}"

            user_name = mine_info.get("data", {}).get("mine", {}).get("userName", "未知用户")
            return f"☆ {user_name} ☆\n✅ Token 有效，可以使用 /kjq sign 签到"

        except Exception as e:
            logger.error(f"查询状态失败: {e}")
            return f"❌ 查询失败: {str(e)}\n\n请检查 token 是否有效。"

    async def do_sign(self, user_id: str, token: str) -> str:
        """执行完整签到流程"""
        result = []
        success_count = 0

        try:
            result.append("☆ 开始签到 ☆")

            # 1. 获取用户信息
            mine_info = await self.api.get_mine_info(token)
            if mine_info.get("code") != 200:
                return f"❌ Token 无效或已过期: {mine_info.get('msg', '请重新绑定 token')}"

            mine_data = mine_info.get("data", {}).get("mine", {})
            kuro_user_id = mine_data.get("userId", 0)
            user_name = mine_data.get("userName", "未知用户")
            result.append(f"👤 用户: {user_name}")

            # 2. 社区签到
            try:
                sign_result = await self.api.user_sign_in(token)
                if sign_result.get("code") == 200 and sign_result.get("success"):
                    result.append("🏠 社区签到: ✅ 成功")
                    success_count += 1
                else:
                    msg = sign_result.get("msg", "未知错误")
                    if "重复签到" in msg or "已签到" in msg:
                        result.append("🏠 社区签到: ℹ️ 今日已签到")
                        success_count += 1
                    else:
                        result.append(f"🏠 社区签到: ❌ 失败 - {msg}")
            except Exception as e:
                logger.error(f"社区签到异常: {e}")
                result.append(f"🏠 社区签到: ❌ 异常 - {str(e)}")

            # 3. 获取游戏角色列表
            try:
                game_list = await self.api.get_user_game_list(token, kuro_user_id)
                if game_list.get("code") != 200:
                    result.append(f"🎮 获取角色列表失败: {game_list.get('msg')}")
                else:
                    role_list = game_list.get("data", {}).get("defaultRoleList", [])
                    if not role_list:
                        result.append("🎮 未找到绑定的游戏角色")
                    else:
                        # 对每个角色进行游戏签到
                        req_month = self._get_beijing_month()
                        for role in role_list:
                            game_id = role.get("gameId", 2)
                            server_id = role.get("serverId", "")
                            role_id = role.get("roleId", 0)
                            role_name = role.get("roleName", "未知角色")

                            try:
                                sign_result = await self.api.encourage_sign_in(
                                    token, game_id, server_id, role_id, kuro_user_id, req_month
                                )
                                if sign_result.get("code") == 200 and sign_result.get("success"):
                                    result.append(f"🎮 {role_name}: ✅ 签到成功")
                                    success_count += 1
                                else:
                                    msg = sign_result.get("msg", "未知错误")
                                    if "重复签到" in msg or "已签到" in msg:
                                        result.append(f"🎮 {role_name}: ℹ️ 今日已签到")
                                        success_count += 1
                                    else:
                                        result.append(f"🎮 {role_name}: ❌ 失败 - {msg}")
                            except Exception as e:
                                logger.error(f"角色 {role_name} 签到异常: {e}")
                                result.append(f"🎮 {role_name}: ❌ 异常 - {str(e)}")
            except Exception as e:
                logger.error(f"获取游戏角色列表异常: {e}")
                result.append(f"🎮 获取角色列表异常: {str(e)}")

            result.append(f"\n✅ 完成！成功 {success_count} 项")
            return "\n".join(result)

        except Exception as e:
            logger.error(f"签到流程异常: {e}")
            return f"❌ 签到失败: {str(e)}"

    async def do_sign_all(self) -> Dict[str, str]:
        """为所有已绑定用户执行签到（用于定时任务）"""
        tokens = self.config.get_all_tokens()
        results = {}

        for user_id, token in tokens.items():
            try:
                result = await self.do_sign(user_id, token)
                results[user_id] = result
            except Exception as e:
                logger.error(f"用户 {user_id} 签到失败: {e}")
                results[user_id] = f"❌ 签到异常: {str(e)}"

        return results
