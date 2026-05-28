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
            "/kjq status - 查看今日签到状态\n"
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
        result = await self.kuro_sign.do_sign(user_id, token)
        yield event.plain_result(result)

    @kjq.command("status")
    async def kjq_status(self, event: AstrMessageEvent):
        user_id = event.get_sender_id()
        token = self.kuro_config.get_token(user_id)
        if not token:
            yield event.plain_result("你还没有绑定 token，请先使用 /kjq bind <token> 绑定。")
            return
        result = await self.kuro_sign.check_status(token)
        yield event.plain_result(result)

    async def terminate(self):
        logger.info("库街区签到插件已卸载")
