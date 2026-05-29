import aiohttp
import asyncio
import random
import string
from typing import Dict, Any, Optional
from astrbot.api import logger


class KuroAPIError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class KuroAPI:
    BASE_URL = "https://api.kurobbs.com"
    MAX_RETRIES = 3
    RETRY_DELAYS = [1, 2, 4]

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

    def _validate_response(self, response_data: Any, url: str) -> Dict[str, Any]:
        if not isinstance(response_data, dict):
            logger.error(f"响应格式错误: 期望字典类型，获得 {type(response_data).__name__}, URL: {url}")
            raise KuroAPIError(
                f"响应格式错误: 期望字典类型，获得 {type(response_data).__name__}",
                response=response_data
            )

        if "code" in response_data and response_data["code"] != 200:
            error_msg = response_data.get("msg", "未知错误")
            logger.error(f"API 返回错误码 {response_data['code']}: {error_msg}, URL: {url}, 响应: {response_data}")
            raise KuroAPIError(
                f"API 返回错误: {error_msg}",
                response=response_data
            )

        return response_data

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

        last_exception = None

        for attempt in range(self.MAX_RETRIES):
            try:
                logger.debug(f"请求 {method} {url} (尝试 {attempt + 1}/{self.MAX_RETRIES})")

                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    logger.debug(f"响应状态码: {resp.status}, URL: {url}")

                    if resp.status >= 500:
                        error_text = await resp.text()
                        logger.warning(
                            f"服务器错误 {resp.status}: {error_text[:200]}, "
                            f"URL: {url}, 尝试 {attempt + 1}/{self.MAX_RETRIES}"
                        )

                        if attempt < self.MAX_RETRIES - 1:
                            delay = self.RETRY_DELAYS[attempt] if attempt < len(self.RETRY_DELAYS) else self.RETRY_DELAYS[-1]
                            logger.info(f"等待 {delay} 秒后重试...")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            raise KuroAPIError(
                                f"服务器错误: HTTP {resp.status}",
                                status_code=resp.status,
                                response={"error": error_text}
                            )

                    try:
                        result = await resp.json()
                    except (aiohttp.ContentTypeError, ValueError) as e:
                        error_text = await resp.text()
                        logger.error(
                            f"JSON 解析失败: {e}, 响应内容: {error_text[:500]}, "
                            f"Content-Type: {resp.headers.get('Content-Type')}, URL: {url}"
                        )
                        raise KuroAPIError(
                            f"JSON 解析失败: {e}",
                            status_code=resp.status,
                            response={"raw_response": error_text}
                        )

                    if resp.status >= 400:
                        logger.error(
                            f"请求失败 HTTP {resp.status}: {result}, URL: {url}"
                        )
                        raise KuroAPIError(
                            f"请求失败: HTTP {resp.status}",
                            status_code=resp.status,
                            response=result
                        )

                    logger.debug(f"响应: {result}")
                    return self._validate_response(result, url)

            except KuroAPIError:
                raise
            except asyncio.TimeoutError as e:
                last_exception = e
                logger.error(
                    f"请求超时: {e}, URL: {url}, 尝试 {attempt + 1}/{self.MAX_RETRIES}"
                )
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAYS[attempt] if attempt < len(self.RETRY_DELAYS) else self.RETRY_DELAYS[-1]
                    logger.info(f"等待 {delay} 秒后重试...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"已达到最大重试次数 {self.MAX_RETRIES}，放弃请求: {url}")
                    raise KuroAPIError(
                        f"请求超时，已达到最大重试次数: {e}",
                        response={"url": url, "method": method}
                    ) from e

            except aiohttp.ClientError as e:
                last_exception = e
                logger.error(
                    f"客户端错误: {type(e).__name__}: {e}, URL: {url}, "
                    f"尝试 {attempt + 1}/{self.MAX_RETRIES}"
                )
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAYS[attempt] if attempt < len(self.RETRY_DELAYS) else self.RETRY_DELAYS[-1]
                    logger.info(f"等待 {delay} 秒后重试...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"已达到最大重试次数 {self.MAX_RETRIES}，放弃请求: {url}")
                    raise KuroAPIError(
                        f"请求失败，已达到最大重试次数: {e}",
                        response={"url": url, "method": method}
                    ) from e

            except Exception as e:
                last_exception = e
                logger.error(
                    f"未知错误: {type(e).__name__}: {e}, URL: {url}, "
                    f"尝试 {attempt + 1}/{self.MAX_RETRIES}, 数据: {data}"
                )
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAYS[attempt] if attempt < len(self.RETRY_DELAYS) else self.RETRY_DELAYS[-1]
                    logger.info(f"等待 {delay} 秒后重试...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"已达到最大重试次数 {self.MAX_RETRIES}，放弃请求: {url}")
                    raise KuroAPIError(
                        f"请求失败，已达到最大重试次数: {e}",
                        response={"url": url, "method": method, "data": data}
                    ) from e

        if last_exception:
            raise KuroAPIError(
                f"请求失败，已达到最大重试次数: {last_exception}",
                response={"url": url, "method": method, "final_attempt": self.MAX_RETRIES}
            ) from last_exception

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
