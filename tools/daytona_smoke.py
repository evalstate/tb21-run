from __future__ import annotations

import asyncio

from daytona import AsyncDaytona


async def main() -> None:
    client = AsyncDaytona()
    count = 0
    async for _ in client.list():
        count += 1
    await client.close()
    print(f"OK: Daytona authentication ({count} visible sandboxes)")


asyncio.run(main())
