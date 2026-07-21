import asyncio
import json
import os

from modules.constants import allows
from modules.utils import StandingCache


async def main():
    os.makedirs("out", exist_ok=True)
    cache = StandingCache()
    await cache.init()
    for k in allows.keys():
        if k in ("24summer","25winter", "25summer","26winter"):
            continue
        print("resolving",k)
        res = await cache.ask_data(k)
        fn = f"out/{k}"
        with open(fn, "w") as f:
            json.dump(res, f)



if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())