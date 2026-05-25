import asyncio
from collections import defaultdict
from typing import Callable

from .constants import allows
from .qindaou import QingdaoUOJ


class StandingCache:
    def __init__(self):
        self.cache = {}
        self.oj = QingdaoUOJ()
        self.lock = asyncio.Lock()
        self.locks = {}
    async def init(self):
        await self.oj.init()
    async def get_data(self, contest_id: str, category: list[tuple[str, Callable[[str], bool]]] | None = None):
        problems_data = await self.oj.get_contest_problems(contest_id)
        ranking = await self.oj.get_ranking(contest_id)
        problems = {}
        mx = defaultdict(int)
        pids = []
        cats = [k for k,v in category] if category is not None else []
        for o in problems_data:
            pid = o["_id"]
            problems[str(o["id"])] = pid
            mx[pid] = o["total_score"]
            if category is not None:
                for x, y in category:
                    if y(pid):
                        mx[x] += o["total_score"]
            mx["total"] += o["total_score"]
            pids.append(pid)
        ks = ["total"] + cats + pids
        res = {}
        for dat in ranking:
            handle = dat["user"]["username"]
            score = {k:0 for k in ks}
            for k, v in dat["submission_info"].items():
                if k not in problems:
                    continue
                pid = problems[k]
                score[pid] = v
                if category is not None:
                    for x, y in category:
                        if y(pid):
                            score[x] += v
                score["total"] += v
            res[handle] = score
        return {"problems": pids, "categories": cats, "ranking": res, "max_score": mx}
    async def ask_data(self, contest_name: str):
        if contest_name not in allows:
            return None
        async with self.lock:
            if contest_name not in self.locks:
                self.locks[contest_name] = asyncio.Lock()
        async with self.locks[contest_name]:
            contest_id = allows[contest_name]["contest_id"]
            category = allows[contest_name]["category"]
            if contest_id not in self.cache:
                self.cache[contest_id] = await self.get_data(contest_id, category)
            return self.cache[contest_id]