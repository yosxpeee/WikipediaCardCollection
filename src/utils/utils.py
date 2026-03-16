import requests
import asyncio

# static tables
HEADER = {
    "Content-Type":"application/json", 
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
}
RANK_TABLE = {
    -1: "--",
    0: "C",
    1: "UC",
    2: "R",
    3: "SR",
    4: "SSR",
    5: "UR",
    6: "LR",
}

# HTTPリクエスト(API)
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
async def fetchJson(url, key_path=None):
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

#rank to rankid
def rankIdToRank(rankId, isSozai):
    #print(rankId, isSozai)
    if isSozai == "1":
        return RANK_TABLE[-1]
    else:
        return RANK_TABLE[int(rankId)]

#rankid to rank
def rankToRankId(rank):
    key = next((k for k, v in RANK_TABLE.items() if v == rank), None)
    return key