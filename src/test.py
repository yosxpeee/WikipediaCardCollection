from utils.utils import doApi, fetch_json
import asyncio

async def main():
	ret = await fetch_json("https://ja.wikipedia.org/api/rest_v1/page/summary/%E8%B1%8A%E5%B3%B6%E3%83%BB%E3%82%B4%E3%82%A8%E3%81%AE%E3%81%82%E3%81%95%E3%81%AF%E3%82%84%E3%81%A3!")

if __name__ == "__main__":
	print("START")
	asyncio.create_task(main())