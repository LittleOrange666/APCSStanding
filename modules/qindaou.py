import json
import os.path
import random
import string
import asyncio

import aiohttp
from loguru import logger
from tqdm.asyncio import trange


class QingdaoUProblem:
    __slots__ = ("data",)

    def __init__(self, data: dict):
        self.data = data


submission_result_table = {0: "AC", 1: "TLE", 3: "MLE", 4: "RE", 8: "PA", -1: "WA", -2: "CE"}
info_file = "qindaou_info.json"


class QingdaoUOJ:

    def __init__(self):
        self.info = {}
        if os.path.exists(info_file):
            with open(info_file) as f:
                self.info = json.load(f)
        if "url" not in self.info:
            if "QingdaoUOJ_URL" in os.environ:
                self.info["url"] = os.environ["QingdaoUOJ_URL"].strip()
            else:
                self.info["url"] = input("Please input the url of OJ: ").strip()
        if "account" not in self.info:
            if "QingdaoUOJ_ACCOUNT" in os.environ:
                self.info["account"] = os.environ["QingdaoUOJ_ACCOUNT"].strip()
            else:
                self.info["account"] = input("Please input the account of OJ: ").strip()
        if "password" not in self.info:
            if "QingdaoUOJ_PASSWORD" in os.environ:
                self.info["password"] = os.environ["QingdaoUOJ_PASSWORD"].strip()
            else:
                self.info["password"] = input("Please input the password of OJ: ").strip()
        url = self.info["url"]
        if url.endswith("/"):
            url = url[:-1]
        if not url.startswith("http"):
            url = "https://" + url
        self.info["url"] = url
        self.url: str = url
        self.cookie: str | None = None

    async def init(self):
        if "cookie" in self.info:
            self.cookie = self.info["cookie"]
            if not await self.check_login():
                await self.login()
                self.info["cookie"] = self.cookie
        else:
            await self.login()
            self.info["cookie"] = self.cookie
        with open(info_file, "w") as f:
            json.dump(self.info, f)

    async def check_login(self):
        try:
            dat = await self.get_data("api/profile", skip_check=True)
            return dat is not None
        except Exception:
            return False

    async def login(self):
        account = self.info["account"]
        password = self.info["password"]
        login_url = self.url+"/api/login"
        csrf_token = "".join(random.choices(string.ascii_letters + string.digits, k=64))
        headers = {
            "Content-Type": "application/json",
            "Referer": self.url,
            "Origin": self.url,
            "x-csrftoken": csrf_token
        }
        cookies = {"csrftoken": csrf_token}
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.post(login_url, json={"username": account, "password": password}, headers=headers) as res:
                text = await res.text()
                print(text)
                cookie_dict = {}
                for cookie in session.cookie_jar:
                    cookie_dict[cookie.key] = cookie.value
                print(cookie_dict)
                self.cookie = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])

    def get_cookie(self) -> str:
        if self.cookie is None:
            raise ValueError("cookie can not be None here")
        return self.cookie

    async def get_data(self, path: str, skip_check=False):
        if not path.startswith("/") and len(path) > 0:
            path = "/" + path
        logger.debug(f"get {path}")
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url + path, headers={"Cookie": self.get_cookie()}) as res:
                if not res.ok:
                    raise Exception(f"request to {res.url} fail, error code={res.status}")
                dat = await res.json()
        if dat.get("error"):
            if dat.get('data') == 'Please login first.' and not skip_check:
                await self.login()
                return await self.get_data(path, skip_check=True)
            raise Exception(f"request to {self.url + path} fail, {dat.get('data')}")
        return dat.get("data")

    async def do_post(self, path: str, data: dict):
        if not path.startswith("/") and len(path) > 0:
            path = "/" + path
        csrf_token = "".join(random.choices(string.ascii_letters + string.digits, k=64))
        headers = {
            "Referer": self.url,
            "Origin": self.url,
            "x-csrftoken": csrf_token,
            "Cookie": self.get_cookie() + ";csrftoken=" + csrf_token,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url + path, headers=headers, json=data) as res:
                if not res.ok:
                    raise Exception(f"request to {res.url} fail, error code={res.status}")
                return await res.json()

    async def get_problem(self, pid: str) -> QingdaoUProblem:
        path = "/api/admin/problem?id=" + pid
        return QingdaoUProblem(await self.get_data(path))

    async def save_problem(self, problem: QingdaoUProblem):
        link = self.url + "/api/admin/problem"
        csrf_token = "".join(random.choices(string.ascii_letters + string.digits, k=64))
        headers = {
            "Referer": self.url,
            "Origin": self.url,
            "x-csrftoken": csrf_token,
            "Cookie": self.get_cookie() + ";csrftoken=" + csrf_token,
        }
        async with aiohttp.ClientSession() as session:
            async with session.put(link, json=problem.data, headers=headers) as res:
                if not res.ok:
                    raise Exception(f"request to {res.url} fail, error code={res.status}")
                return await res.text()

    async def get_ranking(self, contest_id: str, progress: bool = False) -> list:
        limit = 50
        the_range = trange if progress else range
        link = f"api/contest_rank?offset={{0}}&limit={limit}&contest_id=" + contest_id
        dat1 = await self.get_data(link.format(0))
        cnt = dat1["total"]
        ret: list = dat1["results"]
        n = (cnt - 1) // limit
        
        async def fetch(i):
            s = link.format(limit + i * limit)
            return await self.get_data(s)

        for i in the_range(n):
            dat = await fetch(i)
            ret.extend(dat["results"])
        return ret

    async def get_submissions(self, contest_id: str, progress: bool = False, had: int = 0) -> list:
        limit = 50
        the_range = trange if progress else range
        link = f"api/contest_submissions?contest_id={contest_id}&limit={limit}&offset={{0}}"
        dat1 = await self.get_data(link.format(0))
        cnt = dat1["total"]
        ret: list = dat1["results"]
        n = (cnt - had - 1) // limit
        
        async def fetch(i):
            s = link.format(limit + i * limit)
            return await self.get_data(s)
            
        for i in the_range(n):
            dat = await fetch(i)
            ret.extend(dat["results"])
        for o in ret:
            o["result"] = submission_result_table.get(o["result"], "?")
        return ret[:cnt-had]

    async def get_contest_problems(self, contest_id: str) -> list:
        link = "api/contest/problem?contest_id=" + contest_id
        return await self.get_data(link)

    async def count_ac(self, contest_id: str):
        ranking = await self.get_ranking(contest_id)
        problems_data = await self.get_contest_problems(contest_id)
        problems = {}
        for o in problems_data:
            problems[str(o["id"])] = {"id": o["_id"],
                                      "name": o["title"],
                                      "score": o["total_score"]}
        out = []
        for dat in ranking:
            handle = dat["user"]["username"]
            real_name = dat["user"]["real_name"]
            score = 0
            for k, v in dat["submission_info"].items():
                if k not in problems:
                    continue
                if v >= problems[k]["score"]:
                    score += 1
            out.append({"handle": handle, "real_name": real_name, "ac": score})
        out.sort(key=lambda obj: -obj["ac"])
        return {"all": len(problems_data), "rank": out}


async def main():
    oj = QingdaoUOJ()
    await oj.init()


if __name__ == '__main__':
    asyncio.run(main())
