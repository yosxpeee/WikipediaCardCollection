import requests
import time
import asyncio

HEADER = {
    "Content-Type":"application/json", 
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
}

def doApi(url):
    while True:
        try:
            #print(url)
            response = requests.get(url, headers=HEADER)
            response.raise_for_status()  # エラー時にすぐ分かる
            break
        except Exception as e:
            print(e)
            break
    return response

# 非同期でブロッキングなHTTP呼び出しをスレッドで実行するヘルパー
async def fetch_json(url, key_path=None):
    def _call():
        r = doApi(url)
        j = r.json()
        if key_path is None:
            return j
        v = j
        for k in key_path:
            v = v.get(k, {})
        return v
    return await asyncio.to_thread(_call)