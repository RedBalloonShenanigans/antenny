import aiohttp
import asyncio
from tempfile import NamedTemporaryFile

# Space stations

SOURCE = "https://celestrak.com/NORAD/elements/stations.txt"


class Scraper:

    def __init__(self, source=SOURCE):
        self.source = source
        self.temp_file = NamedTemporaryFile(mode='w+t')

    async def get_tle(self, source=SOURCE):
        async with aiohttp.ClientSession() as session:
            async with session.get(source) as response:
                html = await response.text()
                if html:
                    self.temp_file.writelines(html)
                    self.temp_file.seek(0)
                else:
                    return False

    async def read_tle(self):
        await self.get_tle()
        return self.temp_file.read()


async def main():
    s = Scraper()
    r = await s.read_tle()
    print(s.temp_file.name)
    print(r[:100])

asyncio.run(main())
