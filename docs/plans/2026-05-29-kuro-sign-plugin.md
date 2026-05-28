# 库街区签到插件 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 开发一个完整的 AstrBot 插件，实现库街区（社区 + 游戏）的手动和自动签到功能

**Architecture:** 采用三层架构 - 配置层(kuro_config) → API层(kuro_api) → 业务层(kuro_sign) → 集成层(main.py)

**Tech Stack:** Python 3.9+, aiohttp, AstrBot SDK

**重要更新:** 基于新参考项目 https://github.com/leeezep/kurobbs_auto_checkin 更新了 API 实现

---

## 项目状态

**位置:** `D:\code\astrbot_plugin_kjqqd\data\plugins\astrbot_plugin_kjqqd\`

**Git:** 已连接 https://github.com/AKONG-z/astrbot_plugin_kjqqd.git，权限正常

**已完成:**
- ✅ metadata.yaml
- ✅ requirements.txt (aiohttp>=3.8.0)
- ✅ main.py 骨架（指令组已定义）

---

## 关键发现（来自新参考项目）

1. **API 端点不同**：
   - 社区签到: `/user/signIn` (POST)
   - 游戏签到: `/encourage/signIn/v2` (POST)
   - 用户信息: `/user/mineV2` (POST)
   - 角色列表: `/gamer/role/default` (POST)

2. **Content-Type**: `application/x-www-form-urlencoded` 而不是 JSON

3. **请求头更完整**，包含 osversion, devcode, countrycode, ip, model, version, versioncode 等

4. **无需固定 gameId**，从用户绑定的角色列表自动获取

---

## 文件结构

```
astrbot_plugin_kjqqd/
├── metadata.yaml          # 插件元数据（已完成）
├── main.py                # 插件入口（骨架已完成）
├── requirements.txt       # 依赖（已完成）
├── kuro_config.py         # 用户 token 配置管理（待创建）
├── kuro_api.py            # 库街区 API 封装（待创建）
├── kuro_sign.py           # 签到核心逻辑（待创建）
├── logo.png               # 插件图标（待创建）
└── docs/
    └── plans/
        └── 2026-05-29-kuro-sign-plugin.md (本文件)
```

---

## 开发顺序

我重新安排的开发顺序（从底层到上层）：

1. **kuro_config.py** - 用户配置管理（基础，其他模块依赖）
2. **kuro_api.py** - API 封装层（基于新参考项目更新）
3. **kuro_sign.py** - 签到核心逻辑
4. **完善 main.py** - 集成所有模块
5. **定时自动签到** - 使用 AstrBot cron_manager
6. **发布准备** - logo、代码格式化等

---

## Task 1: 实现 kuro_config.py - 用户配置管理

**Files:**
- Create: `D:\code\astrbot_plugin_kjqqd\data\plugins\astrbot_plugin_kjqqd\kuro_config.py`

**设计:**
- 使用 JSON 文件存储 token 映射: `{user_id: token}`
- 文件路径: `data/plugins/astrbot_plugin_kjqqd/tokens.json` (相对于 AstrBot 数据目录)
- KuroConfig 类提供增删改查接口

- [ ] **Step 1: 创建 kuro_config.py**

```python
import os
import json
from typing import Dict, Optional
from astrbot.core.utils.astrbot_path import get_astrbot_data_path
from astrbot.api import logger


class KuroConfig:
    def __init__(self):
        self.data_dir = os.path.join(
            get_astrbot_data_path(),
            "plugins",
            "astrbot_plugin_kjqqd"
        )
        os.makedirs(self.data_dir, exist_ok=True)
        self.token_file = os.path.join(self.data_dir, "tokens.json")
        self._tokens: Dict[str, str] = self._load_tokens()

    def _load_tokens(self) -> Dict[str, str]:
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载 token 文件失败: {e}")
                return {}
        return {}

    def _save_tokens(self):
        try:
            with open(self.token_file, "w", encoding="utf-8") as f:
                json.dump(self._tokens, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存 token 文件失败: {e}")

    def get_token(self, user_id: str) -> Optional[str]:
        return self._tokens.get(user_id)

    def set_token(self, user_id: str, token: str):
        self._tokens[user_id] = token
        self._save_tokens()

    def remove_token(self, user_id: str):
        if user_id in self._tokens:
            del self._tokens[user_id]
            self._save_tokens()

    def get_all_tokens(self) -> Dict[str, str]:
        return self._tokens.copy()
```

- [ ] **Step 2: 提交代码**

```bash
cd "D:\code\astrbot_plugin_kjqqd\data\plugins\astrbot_plugin_kjqqd"
git add kuro_config.py
git commit -m "feat: 实现用户配置管理模块 kuro_config.py"
```

---

## Task 2: 实现 kuro_api.py - API 封装层（基于新参考项目）

**Files:**
- Create: `D:\code\astrbot_plugin_kjqqd\data\plugins\astrbot_plugin_kjqqd\kuro_api.py`

**设计:**
- 封装 aiohttp 请求
- 使用 application/x-www-form-urlencoded 格式
- 完整的请求头（基于参考项目）

- [ ] **Step 1: 创建 kuro_api.py**

```python
import aiohttp
import random
import string
from datetime import datetime
from typing import Dict, Any, Optional
from zoneinfo import ZoneInfo
from astrbot.api import logger


class KuroAPI:
    BASE_URL = "https://api.kurobbs.com"

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    def _generate_devcode(self) -> str:
        """生成随机 devcode"""
        return ''.join(random.choices(string.hexdigits.lower(), k=32))

    def _get_headers(self, token: str) -> Dict[str, str]:
        return {
            "osversion": "Android",
            "devcode": self._generate_devcode(),
            "countrycode": "CN",
            "ip": "10.0.2.233",
            "model": "2211133C",
            "source": "android",
            "lang": "zh-Hans",
            "version": "1.0.9",
            "versioncode": "1090",
            "token": token,
            "content-type": "application/x-www-form-urlencoded; charset=utf-8",
            "accept-encoding": "gzip",
            "user-agent": "okhttp/3.10.0",
        }

    async def _request(
        self,
        method: str,
        path: str,
        token: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        session = await self._get_session()
        url = f"{self.BASE_URL}{path}"
        headers = self._get_headers(token)

        try:
            logger.debug(f"请求 {method} {url}")
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                result = await resp.json()
                logger.debug(f"响应: {result}")
                return result
        except Exception as e:
            logger.error(f"请求失败: {e}")
            raise

    async def get_mine_info(self, token: str, type: int = 1) -> Dict[str, Any]:
        """获取用户信息"""
        return await self._request(
            "POST",
            "/user/mineV2",
            token,
            data={"type": type},
        )

    async def get_user_game_list(self, token: str, user_id: int) -> Dict[str, Any]:
        """获取用户绑定的游戏列表"""
        return await self._request(
            "POST",
            "/gamer/role/default",
            token,
            data={"queryUserId": user_id},
        )

    async def user_sign_in(self, token: str, game_id: int = 2) -> Dict[str, Any]:
        """社区签到"""
        return await self._request(
            "POST",
            "/user/signIn",
            token,
            data={"gameId": game_id},
        )

    async def encourage_sign_in(
        self,
        token: str,
        game_id: int,
        server_id: str,
        role_id: int,
        user_id: int,
        req_month: str,
    ) -> Dict[str, Any]:
        """游戏签到（奖励签到）"""
        return await self._request(
            "POST",
            "/encourage/signIn/v2",
            token,
            data={
                "gameId": game_id,
                "serverId": server_id,
                "roleId": role_id,
                "userId": user_id,
                "reqMonth": req_month,
            },
        )
```

- [ ] **Step 2: 提交代码**

```bash
cd "D:\code\astrbot_plugin_kjqqd\data\plugins\astrbot_plugin_kjqqd"
git add kuro_api.py
git commit -m "feat: 实现 API 封装模块 kuro_api.py（基于新参考项目）"
```

---

## Task 3: 实现 kuro_sign.py - 签到核心逻辑

**Files:**
- Create: `D:\code\astrbot_plugin_kjqqd\data\plugins\astrbot_plugin_kjqqd\kuro_sign.py`

**设计:**
- KuroSign 类接收 KuroConfig 和 KuroAPI 实例
- 实现 do_sign(user_id, token) - 执行完整签到流程
- 实现 check_status(token) - 查询签到状态
- 基于参考项目的签到流程

- [ ] **Step 1: 创建 kuro_sign.py**

```python
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
```

- [ ] **Step 2: 提交代码**

```bash
cd "D:\code\astrbot_plugin_kjqqd\data\plugins\astrbot_plugin_kjqqd"
git add kuro_sign.py
git commit -m "feat: 实现签到核心逻辑模块 kuro_sign.py"
```

---

## Task 4: 完善 main.py 集成

**Files:**
- Modify: `D:\code\astrbot_plugin_kjqqd\data\plugins\astrbot_plugin_kjqqd\main.py`

**修改内容:**
- 更新 KuroConfig 初始化
- 添加错误处理和更好的用户体验
- 在 terminate 中关闭 API session

- [ ] **Step 1: 修改 main.py**

```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

from .kuro_config import KuroConfig
from .kuro_api import KuroAPI
from .kuro_sign import KuroSign


@register("astrbot_plugin_kjqqd", "AKONG-z", "库街区自动签到插件", "0.1.0")
class KuroPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.kuro_config = KuroConfig()
        self.kuro_api = KuroAPI()
        self.kuro_sign = KuroSign(self.kuro_config, self.kuro_api)

    async def initialize(self):
        logger.info("库街区签到插件已加载")

    @filter.command_group("kjq")
    def kjq(self):
        pass

    @kjq.command("help")
    async def kjq_help(self, event: AstrMessageEvent):
        yield event.plain_result(
            "☆ 库街区签到助手 ☆\n"
            "指令列表：\n"
            "/kjq bind <token> - 绑定库街区 token\n"
            "/kjq unbind - 解除绑定\n"
            "/kjq sign - 手动执行签到\n"
            "/kjq status - 验证 token 状态\n"
            "/kjq help - 显示这条帮助信息"
        )

    @kjq.command("bind")
    async def kjq_bind(self, event: AstrMessageEvent, token: str = ""):
        if not token:
            yield event.plain_result("请提供 token，用法：/kjq bind <你的token>\n\n获取 token 方法：登录库街区 APP，通过抓包获取请求头中的 token 字段。")
            return
        user_id = event.get_sender_id()
        self.kuro_config.set_token(user_id, token)
        logger.info(f"用户 {user_id} 已绑定 token")
        yield event.plain_result("✅ token 绑定成功！可以使用 /kjq sign 进行签到。")

    @kjq.command("unbind")
    async def kjq_unbind(self, event: AstrMessageEvent):
        user_id = event.get_sender_id()
        self.kuro_config.remove_token(user_id)
        yield event.plain_result("✅ 已解除绑定。")

    @kjq.command("sign")
    async def kjq_sign(self, event: AstrMessageEvent):
        user_id = event.get_sender_id()
        token = self.kuro_config.get_token(user_id)
        if not token:
            yield event.plain_result("你还没有绑定 token，请先使用 /kjq bind <token> 绑定。")
            return
        yield event.plain_result("⏳ 正在执行签到，请稍候...")
        try:
            result = await self.kuro_sign.do_sign(user_id, token)
            yield event.plain_result(result)
        except Exception as e:
            logger.error(f"签到异常: {e}")
            yield event.plain_result(f"❌ 签到失败: {str(e)}")

    @kjq.command("status")
    async def kjq_status(self, event: AstrMessageEvent):
        user_id = event.get_sender_id()
        token = self.kuro_config.get_token(user_id)
        if not token:
            yield event.plain_result("你还没有绑定 token，请先使用 /kjq bind <token> 绑定。")
            return
        try:
            result = await self.kuro_sign.check_status(token)
            yield event.plain_result(result)
        except Exception as e:
            logger.error(f"查询状态异常: {e}")
            yield event.plain_result(f"❌ 查询失败: {str(e)}")

    async def terminate(self):
        await self.kuro_api.close()
        logger.info("库街区签到插件已卸载")
```

- [ ] **Step 2: 提交代码**

```bash
cd "D:\code\astrbot_plugin_kjqqd\data\plugins\astrbot_plugin_kjqqd"
git add main.py
git commit -m "feat: 完善 main.py 模块集成和错误处理"
```

---

## Task 5: 添加定时自动签到功能

**Files:**
- Modify: `D:\code\astrbot_plugin_kjqqd\data\plugins\astrbot_plugin_kjqqd\main.py`

**设计:**
- 使用 AstrBot 的 cron_manager
- 每天 7:00 自动为所有已绑定用户执行签到

- [ ] **Step 1: 修改 main.py 添加定时任务**

```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

from .kuro_config import KuroConfig
from .kuro_api import KuroAPI
from .kuro_sign import KuroSign


@register("astrbot_plugin_kjqqd", "AKONG-z", "库街区自动签到插件", "0.1.0")
class KuroPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.kuro_config = KuroConfig()
        self.kuro_api = KuroAPI()
        self.kuro_sign = KuroSign(self.kuro_config, self.kuro_api)
        self.cron_job = None

    async def initialize(self):
        logger.info("库街区签到插件已加载")
        
        # 注册定时任务：每天 7:00 自动签到
        try:
            self.cron_job = self.context.cron_manager.add_cron_job(
                func=self._auto_sign,
                cron="0 7 * * *",  # 每天 7:00
                name="kuro_auto_sign",
                misfire_grace_time=3600,  # 1小时内的 misfire 仍执行
            )
            logger.info("已注册每日自动签到任务（7:00）")
        except Exception as e:
            logger.error(f"注册定时任务失败: {e}")

    async def _auto_sign(self):
        """自动签到任务"""
        logger.info("开始执行每日自动签到...")
        results = await self.kuro_sign.do_sign_all()
        
        for user_id, result in results.items():
            try:
                logger.info(f"用户 {user_id} 签到结果: {result[:100]}...")
            except Exception as e:
                logger.error(f"处理用户 {user_id} 签到结果失败: {e}")

    @filter.command_group("kjq")
    def kjq(self):
        pass

    @kjq.command("help")
    async def kjq_help(self, event: AstrMessageEvent):
        yield event.plain_result(
            "☆ 库街区签到助手 ☆\n"
            "指令列表：\n"
            "/kjq bind <token> - 绑定库街区 token\n"
            "/kjq unbind - 解除绑定\n"
            "/kjq sign - 手动执行签到\n"
            "/kjq status - 验证 token 状态\n"
            "/kjq help - 显示这条帮助信息"
        )

    @kjq.command("bind")
    async def kjq_bind(self, event: AstrMessageEvent, token: str = ""):
        if not token:
            yield event.plain_result("请提供 token，用法：/kjq bind <你的token>\n\n获取 token 方法：登录库街区 APP，通过抓包获取请求头中的 token 字段。")
            return
        user_id = event.get_sender_id()
        self.kuro_config.set_token(user_id, token)
        logger.info(f"用户 {user_id} 已绑定 token")
        yield event.plain_result("✅ token 绑定成功！可以使用 /kjq sign 进行签到。")

    @kjq.command("unbind")
    async def kjq_unbind(self, event: AstrMessageEvent):
        user_id = event.get_sender_id()
        self.kuro_config.remove_token(user_id)
        yield event.plain_result("✅ 已解除绑定。")

    @kjq.command("sign")
    async def kjq_sign(self, event: AstrMessageEvent):
        user_id = event.get_sender_id()
        token = self.kuro_config.get_token(user_id)
        if not token:
            yield event.plain_result("你还没有绑定 token，请先使用 /kjq bind <token> 绑定。")
            return
        yield event.plain_result("⏳ 正在执行签到，请稍候...")
        try:
            result = await self.kuro_sign.do_sign(user_id, token)
            yield event.plain_result(result)
        except Exception as e:
            logger.error(f"签到异常: {e}")
            yield event.plain_result(f"❌ 签到失败: {str(e)}")

    @kjq.command("status")
    async def kjq_status(self, event: AstrMessageEvent):
        user_id = event.get_sender_id()
        token = self.kuro_config.get_token(user_id)
        if not token:
            yield event.plain_result("你还没有绑定 token，请先使用 /kjq bind <token> 绑定。")
            return
        try:
            result = await self.kuro_sign.check_status(token)
            yield event.plain_result(result)
        except Exception as e:
            logger.error(f"查询状态异常: {e}")
            yield event.plain_result(f"❌ 查询失败: {str(e)}")

    async def terminate(self):
        if self.cron_job:
            try:
                self.context.cron_manager.remove_job(self.cron_job.id)
            except Exception as e:
                logger.error(f"移除定时任务失败: {e}")
        await self.kuro_api.close()
        logger.info("库街区签到插件已卸载")
```

- [ ] **Step 2: 提交代码**

```bash
cd "D:\code\astrbot_plugin_kjqqd\data\plugins\astrbot_plugin_kjqqd"
git add main.py
git commit -m "feat: 添加每日自动签到功能（7:00）"
```

---

## Task 6: 发布准备

**Files:**
- Check: 代码格式化

- [ ] **Step 1: 检查并提交当前所有变更**

```bash
cd "D:\code\astrbot_plugin_kjqqd\data\plugins\astrbot_plugin_kjqqd"
git status
git add requirements.txt  # 如果之前没提交的话
git add docs/plans/2026-05-29-kuro-sign-plugin.md
git commit -m "docs: 添加实施计划文档"
git push origin master
```

---

## 测试建议

1. 加载插件到 AstrBot 测试
2. 测试 /kjq bind <token> 绑定
3. 测试 /kjq status 验证 token
4. 测试 /kjq sign 签到
5. 测试 /kjq unbind 解绑

---

**Plan complete and saved to `docs/plans/2026-05-29-kuro-sign-plugin.md`.**

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach would you like?**
