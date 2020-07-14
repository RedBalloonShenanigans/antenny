import aiohttp
import aiofiles
import asyncio


SOURCE = "https://celestrak.com/NORAD/elements/active.txt"
FILENAME = "/tmp/sat_data.tle"

async def _get_tle_file(source=SOURCE, filename=FILENAME):
    async with aiohttp.ClientSession() as session:
        async with session.get(source) as response:
            html = await response.text()
            async with aiofiles.open(filename, mode='w') as f:
                await f.write(html)

async def _get_tle_lines(): 
    await _get_tle_file()
    async with aiofiles.open(FILENAME, "r") as f:
        raw_lines = await f.readlines()
        encode_lines = list(map(lambda l: l.encode("utf-8"), raw_lines))
        return encode_lines

# entry point
async def load_tle():
    return await _get_tle_lines()

if __name__ == "__main__":
    asyncio.run(load_tle())
    #print(load_tle())
