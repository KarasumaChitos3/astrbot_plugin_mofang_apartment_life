from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult, MessageChain
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
from .mofangapi import MofangApi
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

@register("MofangApartmentLife", "KarasumaChitose", "魔方生活相关信息查询", "0.0.1")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config  # 插件配置对象，包含了插件的配置信息
        self.api = MofangApi(
            mobile=self.config.get("mobile"),
            password=self.config.get("password")
        )
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(
                self._check_threshold,
                "interval",
                hours=24,
                id="scheduled_plugin_check",
                name="Scheduled Plugin Check",
            )
        self._check_threshold()

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        

    async def _check_threshold(self):
        """这个方法被调用用来检查每天"""
        if not self.config.get('reminder_user',None):
            logger.debug("未配置提醒用户，跳过检查")
            return
        data = await self.api.get_energy()
        ret_str = ''
        for fee in data['data']:
            if float(fee['balanceAmount']) < self.config.get("reminder_threshold", 20):
                ret_str += f"提醒：{fee['accountSubjectName']} 余额低于阈值!请及时充值\n"
        message_chain = MessageChain().message(ret_str)
        yield self.context.send_message(self.config.get('reminder_user',''),message_chain) # 发送一条纯文本消息
    
    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("mofang")
    async def helloworld(self, event: AstrMessageEvent):
        """这是一个魔方生活相关信息查询指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        data = await self.api.get_energy()
        ret_str = ''
        for fee in data['data']:
            ret_str += f"{fee['accountSubjectName']}：{fee['balanceAmount']}\n"
            if float(fee['balanceAmount']) < self.config.get("reminder_threshold", 20):
                ret_str += f"提醒：{fee['accountSubjectName']} 余额低于阈值!请及时充值\n"
        yield event.plain_result(ret_str) # 发送一条纯文本消息

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
