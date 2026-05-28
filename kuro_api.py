import aiohttp
import random
import string
from typing import Dict, Any, Optional
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
        return await self._request(
            "POST",
            "/user/mineV2",
            token,
            data={"type": type},
        )

    async def get_user_game_list(self, token: str, user_id: int) -> Dict[str, Any]:
        return await self._request(
            "POST",
            "/gamer/role/default",
            token,
            data={"queryUserId": user_id},
        )

    async def user_sign_in(self, token: str, game_id: int = 2) -> Dict[str, Any]:
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
