import asyncio
import hashlib
import json
import time
import traceback
from enum import Enum, auto
from functools import cached_property

import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn
from wxpusher import WxPusher

import settings


class Status(Enum):
    EXIT = auto()


def get_proxy() -> str:
    return httpx.get("http://127.0.0.1:5010/get/").json().get("proxy")


def delete_proxy(proxy: str):
    httpx.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))


class PerformanceResponse:
    def __init__(self, response: httpx.Response, api: dict | None = None) -> None:
        self.response = response
        self.api: dict = api or response.json()

    @cached_property
    def id(self) -> str:
        """演出id"""
        return self.result["performCalendar"]["currentPerformId"]

    @cached_property
    def name(self) -> str:
        """演出名"""
        for i in self.views:
            if i["performId"] == self.id:
                return i["performName"]
        raise ValueError("找不到演出名")

    @cached_property
    def views(self):
        """演出列表"""
        return self.result["performCalendar"]["performViews"]

    @cached_property
    def result(self) -> dict:
        return json.loads(self.api["data"]["result"])

    @cached_property
    def perform_ids(self) -> list[str]:
        """所有场次的id"""
        return [i["performId"] for i in self.views]

    @cached_property
    def sku_list(self) -> list[dict]:
        """有票的场次"""
        return [i for i in self.result["perform"]["skuList"] if i["skuSalable"] == "true"]


class PerformanceMonitor:
    def __init__(self, id: str):
        self.id = id
        self.app_key = 12574478
        self._m_h5_tk = ""
        self._m_h5_tk_enc = ""
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36 Edg/118.0.2088.76",
            "Origin": "https://m.damai.cn",
            "Pragma": "no-cache",
            "Referer": "https://m.damai.cn/",
            "Sec-Ch-Ua": '"Chromium";v="118", "Microsoft Edge";v="118", "Not=A?Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?1",
            "Sec-Ch-Ua-Platform": "Android",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }
        self._cookies = {}

    def _get_params(self, perform_id: str | None = None):
        t = int(time.time() * 1000)
        data = {
            "itemId": self.id,
            "bizCode": "ali.china.damai",
            "scenario": "itemsku",
            "exParams": json.dumps({
                "dataType": 2,
                "dataId": perform_id or "",
                "privilegeActId": ""
            }, separators=(",", ":")),
            "platform": "8",
            "comboChannel": "2",
            "dmChannel": "damai@damaih5_h5",
        }
        str_data = json.dumps(data, separators=(',', ':'))
        sign = f"{self._m_h5_tk.split('_')[0]}&{t}&{self.app_key}&{str_data}"
        sign = hashlib.md5(sign.encode()).hexdigest()
        return httpx.QueryParams(
            jsv="2.7.2",
            appKey=self.app_key,
            t=t,
            sign=sign,
            api="mtop.alibaba.detail.subpage.getdetail",
            v="2.0",
            H5Request=True,
            type="originaljson",
            timeout=10000,
            dataType="json",
            valueType="original",
            forceAntiCreep=True,
            AntiCreep=True,
            useH5=True,
            data=str_data,
        )

    async def get_performance(self, perform_id: str | None = None):
        def is_expired(data: dict) -> bool:
            ret: str = ''.join(data.get("ret", []))
            return "令牌为空" in ret or "令牌过期" in ret

        async with httpx.AsyncClient(headers=self.headers, cookies=self.cookies) as client:
            response = await client.get(
                url="https://mtop.damai.cn/h5/mtop.alibaba.detail.subpage.getdetail/2.0/",
                params=self._get_params(perform_id),
            )
        data = response.json()

        if is_expired(data):
            self.cookies = response.cookies
            return False, []
        if response.is_error:
            console.log(response, response.text)
            return False, []

        performance = PerformanceResponse(response)
        try:
            console.log(
                f"ID: {self.id}",
                f"演出ID: {performance.id}",
                f"演出名: {performance.name}",
                f"可购票: {[i['priceName'] for i in performance.sku_list]}",
            )
            if False:
                WxPusher.send_message("...")
        except Exception:
            console.log(traceback.format_exc())
            console.log(response.text)
        return True, filter(lambda x: x != performance.id, performance.perform_ids)

    async def start(self):
        async def coro_perform(perform_id: str | None = None):
            await asyncio.sleep(settings.TIME_INTERVAL)
            return await self.get_performance(perform_id)

        while True:
            try:
                success, other_perform_ids = await coro_perform()
                if not success:
                    continue
                for i in other_perform_ids:
                    await coro_perform(i)
            except Exception:
                console.log(traceback.format_exc())

    @property
    def cookies(self):
        return self._cookies

    @cookies.setter
    def cookies(self, cookies: httpx.Cookies):
        self._m_h5_tk = cookies['_m_h5_tk']
        self._m_h5_tk_enc = cookies['_m_h5_tk_enc']
        self._cookies = {
            "_m_h5_tk": self._m_h5_tk,
            "_m_h5_tk_enc": self._m_h5_tk_enc,
        }


async def main():
    async def new_task(monitor: PerformanceMonitor):
        task_id = progress.add_task(monitor.id, total=None)
        await monitor.start()
        progress.remove_task(task_id)

    console.log("启动")
    with Progress(
        SpinnerColumn(),
        *Progress.get_default_columns(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        while True:
            monitor = await monitor_queue.get()
            if monitor is Status.EXIT:
                return
            asyncio.create_task(new_task(monitor))


console = Console()
monitor_queue = asyncio.Queue[PerformanceMonitor | Status]()
monitor_queue.put_nowait(PerformanceMonitor("742825990950"))
# monitor_queue.put_nowait(PerformanceMonitor("744726326543"))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.log("用户中断")
