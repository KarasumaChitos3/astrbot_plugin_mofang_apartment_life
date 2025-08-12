import os
import asyncio
from typing import Callable, Awaitable, TypeVar, Any
import httpx

T = TypeVar("T")


def ensure_token(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """装饰器：调用目标协程前确保 access_token 已获取。

    约定：实例上应存在 self.access_token、self.mobile、self.password、self.get_access_token。
    若 access_token 为空，则使用保存的账号密码先获取。
    """

    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> T:
        if not getattr(self, "access_token", None):
            mobile = getattr(self, "mobile", None)
            password = getattr(self, "password", None)
            if not mobile or not password:
                raise RuntimeError(
                    "access_token 为空且未提供登录凭据（mobile/password）。"
                )
            await self.get_access_token(mobile, password)
        return await func(self, *args, **kwargs)

    return wrapper


class MofangApi:
    def __init__(self, mobile: str | None = None, password: str | None = None) -> None:
        # 从参数或环境变量读取账号信息，便于装饰器在需要时自动获取 token
        self.mobile: str | None = mobile or os.getenv("MF_MOBILE")
        self.password: str | None = password or os.getenv("MF_PASSWORD")

        self.client = httpx.AsyncClient()
        self.access_token: str | None = None

    

    async def get_access_token(self, mobile: str, password: str) -> str:
        response = await self.client.post("https://renter-api.52mf.com/renter/login/v1/loginByPassword", json={
            "mobile": mobile,
            "password": password
            })
        response.raise_for_status()
        data = response.json()
        token = data["data"]["accessToken"]
        # 明确 token 为 str，避免 httpx headers 的类型告警
        if not isinstance(token, str):
            raise TypeError("accessToken 应为字符串")

        self.access_token = token
        # 使用下标赋值，且值明确为 str，避免 “str | None” 的类型问题
        self.client.headers["accessToken"] = token
        return token

    @ensure_token
    async def get_energy(self, contract_id: int = 250806001063) -> dict[str, Any]:
        '''
        返回的例子如下
        {
            "code": 1,
            "message": "操作成功",
            "detail": "5a167f9c-fcb8-4c86-b954-bf00ac7417fc|1",
            "errorLevel": null,
            "data": [
                {
                    "accountSubjectCode": "10501",
                    "accountSubjectName": "电费",
                    "contractCode": "250806001063",
                    "energyAccountCode": "d3d7e842-7a08-46ad-931c-0dc3caceadad",
                    "balanceAmount": "225.77",
                    "rechargeAmountDesc": "电费余额：",
                    "rechargeAmountList": [
                        0,
                        100,
                        200,
                        300,
                        500,
                        1000
                    ],
                    "judgeEnergyRechange": true
                },
                {
                    "accountSubjectCode": "10502",
                    "accountSubjectName": "冷水费",
                    "contractCode": "250806001063",
                    "energyAccountCode": "663d50ff-664d-45be-9cf1-70b70d7b588e",
                    "balanceAmount": "190.00",
                    "rechargeAmountDesc": "冷水费余额：",
                    "rechargeAmountList": [
                        0,
                        100,
                        200,
                        300,
                        500,
                        1000
                    ],
                    "judgeEnergyRechange": true
                }
            ]
        }
        '''
        response = await self.client.post(f"https://renter-api.52mf.com/renter/energy/v1/getEnergyRechargeInfo?contractCode={contract_id}&accountSubjectCode=")
        response.raise_for_status()
        data = response.json()
        return data
