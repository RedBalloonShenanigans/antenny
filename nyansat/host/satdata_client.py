import aiohttp
import asyncio


SOURCE = "https://celestrak.com/NORAD/elements/active.txt"


class SatelliteScraper:

    def __init__(self):
        self.file_text = None

    async def get_tle_file(self, source=SOURCE):
        async with aiohttp.ClientSession() as session:
            async with session.get(source) as response:
                self.file_text = await response.text()

    async def get_tle_lines(self):
        await self.get_tle_file()
        raw_lines = self.file_text.split('\n')
        encode_lines = list(map(lambda l: l.encode("utf-8"), raw_lines))
        return encode_lines


# entry point
async def load_tle():
    scraper = SatelliteScraper()
    return await scraper.get_tle_lines()

if __name__ == "__main__":
    asyncio.run(load_tle())
