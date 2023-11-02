"""猫眼监控"""
import time
from threading import Thread

import httpx
from rich.console import Console
from wxpusher import WxPusher


class MyThread(Thread):
    def __init__(self, performanceId: str):
        self.app_name = "猫眼"
        self.performance_id = performanceId
        self.alive = True
        self.headers = {
            "User-Agent":
                "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Mobile Safari/537.36",
        }
        super().__init__()

    def get_params(self):
        return {
            "performanceId": self.performance_id,
            "optimus_risk_level": "71",
            "optimus_code": "10",
            "uuid": "x64b3dc4bhwlhm6b4yjm3qneby1k1b8v32ku42gy1f8ukdtrh22qoxnra9qtig01",
            "sellChannel": "13",
            "cityId": "10",
            "token":
                "AgFkIf6T4ulDKFT8q851YuDMWnncjUqqtUX-14DHYHT8Z6GTbHU2D40rbXZmjupNDveqWmIRDff30wAAAADKGwAAaRoxuAgQ8oCdBnDIinC4fDZX62g1ejE5F7iKZvIPoXOScG7rNa6R88pmLKG89JNb",
            "yodaReady": "h5",
            "csecplatform": "4",
            "csecversion": "2.3.0",
        }

    def run(self):
        while self.alive:
            response = httpx.get(
                url=f"https://show.maoyan.com/maoyansh/myshow/ajax/v2/performance/{self.performance_id}/shows/0",
                params=self.get_params(),
                headers=self.headers,
            )
            # 得到场次，根据场次来得到表演id showId
            json_data: dict = response.json()
            # 获取到showid 演出时间
            performances = [{
                "showId": data["showId"],
                "time": data["name"],
            } for data in json_data["data"]]

            console.log(performances)

            self.parse_performances(performances)
            time.sleep(1)

    def parse_performances(self, performances: list[dict]):
        name_response = httpx.get(
            url=f"https://show.maoyan.com/maoyansh/myshow/ajax/v2/performance/{self.performance_id}?optimus_risk_level=71&optimus_code=10&uuid=x64b3dc4bhwlhm6b4yjm3qneby1k1b8v32ku42gy1f8ukdtrh22qoxnra9qtig01&sellChannel=13&cityId=10&token=AgFkIf6T4ulDKFT8q851YuDMWnncjUqqtUX-14DHYHT8Z6GTbHU2D40rbXZmjupNDveqWmIRDff30wAAAADKGwAAaRoxuAgQ8oCdBnDIinC4fDZX62g1ejE5F7iKZvIPoXOScG7rNa6R88pmLKG89JNb&yodaReady=h5&csecplatform=4&csecversion=2.3.0",
            headers=self.headers,
        )
        name_info = name_response.json()
        for performance in performances:
            response = httpx.get(
                f"https://show.maoyan.com/maoyansh/myshow/ajax/v2/show/{performance['showId']}/tickets",
                headers=self.headers,
                params=self.get_params(),
            )
            response_data = response.json()
            self.check_tickets(response_data["data"], performance, name_info)

    def check_tickets(self, tickets: list[dict], performance: dict, name_info: dict):
        for i in tickets:
            if i["stockable"]:
                WxPusher.send_message(
                    f"{self.app_name}\\{name_info['data']['name']}\n"
                    f"{performance['time']}\n"
                    f"票价: {i['ticketName']} {i['ticketPrice']}\n"
                    f"是否有票: {i['stockable']}",
                    topic_ids=['23377'],
                    token='AT_oO5CAXnpSCXBHh4TDK6J9hH0g3tKBZzd',
                )
            console.log(f"平台：{self.app_name}")
            console.log(name_info["data"]["name"])
            console.log(performance["time"])
            console.log(f"票价：{i['ticketName']} {i['ticketPrice']}")
            console.log(f"是否有票：{i['stockable']}")


def main():
    # 薛之谦成都
    t1 = MyThread("269177")
    # 伍佰合肥
    t2 = MyThread("277793")

    t1.start()
    t2.start()


console = Console()

if __name__ == "__main__":
    main()
