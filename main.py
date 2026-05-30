from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

from .kuro_config import KuroConfig
from .kuro_api import KuroAPI
from .kuro_sign import KuroSign

import json
import asyncio
import datetime


@register("astrbot_plugin_kjqqd", "AKONG-z", "库街区自动签到插件", "0.1.0")
class KuroPlugin(Star):
    def __init__(self, context: Context, config=None):
        super().__init__(context)
        self.config = config
        self.kuro_config = KuroConfig()
        self.kuro_api = KuroAPI()
        self.kuro_sign = KuroSign(self.kuro_config, self.kuro_api)
        self._auto_sign_task = None
        self.pending_logins = {}

    async def initialize(self):
        logger.info("库街区签到插件已加载")
        try:
            self._register_web_api()
            if self._is_auto_sign_enabled():
                self._auto_sign_task = asyncio.create_task(self._auto_sign_task_loop())
                await self._check_and_run_today()
        except Exception as e:
            logger.error(f"初始化失败: {e}")

    def _register_web_api(self):
        """注册 Web API 路由"""
        self.context.register_web_api(
            '/api/plugin/astrbot_plugin_kjqqd/config',
            self._handle_config_request,
            methods=['GET', 'POST'],
            desc='库街区签到插件配置 API'
        )
        logger.info("已注册配置 API 路由")

    def _is_auto_sign_enabled(self):
        """检查自动签到是否启用"""
        if self.config:
            return self.config.get("auto_sign_enabled", True)
        return True

    def _get_sign_time(self):
        """获取签到时间"""
        if self.config:
            return self.config.get("auto_sign_time", "07:00")
        return "07:00"

    async def _auto_sign_task_loop(self):
        """自动签到后台任务循环"""
        while True:
            try:
                next_time = self._calculate_next_sign_time()
                wait_seconds = (next_time - datetime.datetime.now()).total_seconds()
                
                if wait_seconds > 0:
                    logger.info(f"下次签到时间: {next_time.strftime('%Y-%m-%d %H:%M:%S')}，等待 {wait_seconds:.0f} 秒")
                    await asyncio.sleep(wait_seconds)
                
                await self._do_auto_sign()
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                logger.info("自动签到任务已取消")
                break
            except Exception as e:
                logger.error(f"自动签到任务异常: {e}")
                await asyncio.sleep(60)

    def _calculate_next_sign_time(self):
        """计算下次签到时间"""
        sign_time = self._get_sign_time()
        hours, minutes = map(int, sign_time.split(":"))
        
        now = datetime.datetime.now()
        next_time = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        
        if next_time <= now:
            next_time += datetime.timedelta(days=1)
        
        return next_time

    async def _check_and_run_today(self):
        """启动时检查今天是否已签到，未签到则立即执行"""
        try:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            last_sign_date = self.kuro_config.get_last_sign_date()
            
            if last_sign_date != today:
                logger.info(f"今天 ({today}) 还未签到，立即执行签到")
                await self._do_auto_sign()
            else:
                logger.info(f"今天 ({today}) 已签过到，跳过")
        except Exception as e:
            logger.error(f"启动时签到检查失败: {e}")

    async def _do_auto_sign(self):
        """执行自动签到"""
        try:
            logger.info("开始执行每日自动签到任务")
            results = await self.kuro_sign.do_sign_all()
            logger.info(f"自动签到完成，处理了 {len(results)} 个用户")
            
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            self.kuro_config.set_last_sign_date(today)
            
            for user_id, result in results.items():
                logger.debug(f"用户 {user_id} 签到结果: {result}")
        except Exception as e:
            logger.error(f"自动签到任务执行失败: {e}")

    @filter.command_group("kjq")
    def kjq(self):
        pass

    @kjq.command()
    async def kjq_default(self, event: AstrMessageEvent):
        yield event.plain_result(
            "☆ 库街区签到助手 ☆\n\n"
            "可用指令：\n"
            "/kjq login <手机号> <验证码> - 登录绑定\n"
            "/kjq bind <token> - 手动绑定\n"
            "/kjq sign - 手动签到\n"
            "/kjq status - 查看状态\n"
            "/kjq help - 详细帮助"
        )

    @kjq.command("help")
    async def kjq_help(self, event: AstrMessageEvent):
        yield event.plain_result(
            "☆ 库街区签到助手 ☆\n\n"
            "📱 登录绑定指令：\n"
            "/kjq login <手机号> <验证码> - 登录并绑定\n"
            "/kjq bind <token> - 手动绑定 token\n"
            "/kjq unbind - 解除绑定\n\n"
            "🎮 签到指令：\n"
            "/kjq sign - 手动执行签到\n"
            "/kjq status - 查看签到状态\n\n"
            "📖 其他：\n"
            "/kjq help - 显示帮助信息\n\n"
            "⚠️ 注意事项：\n"
            "登录会顶掉手机APP的登录状态，建议使用 /kjq bind 命令绑定。\n"
            "获取token方法：在手机上用手机号登录库街区APP，通过抓包获取token。"
        )

    @kjq.command("login")
    async def kjq_login(self, event: AstrMessageEvent, mobile: str = "", code: str = ""):
        if not mobile or not code:
            yield event.plain_result(
                "📱 库街区登录\n\n"
                "请提供手机号和验证码：\n"
                "/kjq login <手机号> <验证码>\n\n"
                "示例：\n"
                "/kjq login 13800138000 123456\n\n"
                "⚠️ 注意：登录后会顶掉手机APP的登录状态！\n"
                "如需使用手机APP，请重新在手机上登录。"
            )
            return
        
        if not mobile.isdigit() or len(mobile) != 11:
            yield event.plain_result("❌ 手机号格式错误，请输入11位手机号\n\n示例：/kjq login 13800138000 123456")
            return
        
        if not code.isdigit():
            yield event.plain_result("❌ 验证码格式错误，验证码应为数字\n\n示例：/kjq login 13800138000 123456")
            return
        
        user_id = event.get_sender_id()
        
        try:
            yield event.plain_result("⏳ 正在验证...")
            result = await self.kuro_sign.login_with_code(mobile, code)
            
            if result.get("success"):
                token = result.get("token")
                username = result.get("username", "")
                user_id_str = result.get("userId", "")
                self.kuro_config.set_token(user_id, token)
                logger.info(f"用户 {user_id} ({username}, ID: {user_id_str}) 登录成功")
                yield event.plain_result(
                    f"✅ 登录成功！\n\n"
                    f"👤 用户名：{username}\n"
                    f"🔢 用户ID：{user_id_str}\n"
                    f"✅ Token 已自动绑定\n\n"
                    f"现在可以使用 /kjq sign 进行签到！"
                )
            else:
                yield event.plain_result(f"❌ 登录失败: {result.get('msg')}\n\n请检查手机号和验证码是否正确。")
        except Exception as e:
            logger.error(f"登录失败: {e}")
            yield event.plain_result(f"❌ 登录出错: {str(e)}\n\n请稍后重试。")

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
        try:
            user_id = event.get_sender_id()
            token = self.kuro_config.get_token(user_id)
            if not token:
                yield event.plain_result("你还没有绑定 token，请先使用 /kjq bind <token> 绑定。")
                return
            yield event.plain_result("⏳ 正在执行签到，请稍候...")
            result = await self.kuro_sign.do_sign(user_id, token)
            yield event.plain_result(result)
        except Exception as e:
            logger.error(f"签到命令执行失败: {e}")
            yield event.plain_result(f"❌ 签到执行出错: {str(e)}\n\n请稍后重试。")

    @kjq.command("status")
    async def kjq_status(self, event: AstrMessageEvent):
        try:
            user_id = event.get_sender_id()
            token = self.kuro_config.get_token(user_id)
            if not token:
                yield event.plain_result("你还没有绑定 token，请先使用 /kjq bind <token> 绑定。")
                return
            result = await self.kuro_sign.check_status(token)
            yield event.plain_result(result)
        except Exception as e:
            logger.error(f"查询状态命令执行失败: {e}")
            yield event.plain_result(f"❌ 查询状态出错: {str(e)}\n\n请稍后重试。")

    async def terminate(self):
        try:
            await self.kuro_api.close()
            if self._auto_sign_task:
                self._auto_sign_task.cancel()
                try:
                    await self._auto_sign_task
                except asyncio.CancelledError:
                    pass
            logger.info("已移除自动签到定时任务")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")
        logger.info("库街区签到插件已卸载")

    async def _handle_config_request(self, request):
        """处理配置请求（GET 获取配置，POST 保存配置）"""
        try:
            if request.method == 'GET':
                config = self.kuro_config.get_config()
                return json.dumps(config), 200, {'Content-Type': 'application/json'}
            elif request.method == 'POST':
                body = await request.text()
                data = json.loads(body)
                
                if "kuro_token" in data and data["kuro_token"]:
                    global_token = data["kuro_token"]
                    all_users = self.kuro_config.get_all_tokens().keys()
                    for user_id in all_users:
                        self.kuro_config.set_token(user_id, global_token)
                    logger.info(f"已为所有用户设置全局 token")
                
                self.kuro_config.update_config(data)
                
                if "auto_sign_enabled" in data or "auto_sign_time" in data:
                    if data.get("auto_sign_enabled") and not self._auto_sign_task:
                        self._auto_sign_task = asyncio.create_task(self._auto_sign_task_loop())
                    elif not data.get("auto_sign_enabled") and self._auto_sign_task:
                        self._auto_sign_task.cancel()
                        self._auto_sign_task = None
                
                return json.dumps({"success": True, "msg": "配置保存成功"}), 200, {'Content-Type': 'application/json'}
            else:
                return json.dumps({"success": False, "msg": "不支持的请求方法"}), 405, {'Content-Type': 'application/json'}
        except Exception as e:
            logger.error(f"处理配置请求失败: {e}")
            return json.dumps({"success": False, "msg": str(e)}), 500, {'Content-Type': 'application/json'}
