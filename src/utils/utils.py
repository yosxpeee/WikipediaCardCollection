import requests
import asyncio

# static tables
HEADER = {
    "Content-Type":"application/json", 
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
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
def do_api(url):
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
        r = do_api(url)
        j = r.json()
        if key_path is None:
            return j
        v = j
        for k in key_path:
            v = v.get(k, {})
        return v
    return await asyncio.to_thread(_call)

#rank to rankid
def rankid_to_rank(rankId, isSozai):
    if isSozai == 1:
        return RANK_TABLE[-1]
    else:
        return RANK_TABLE[int(rankId)]

#rankid to rank
def rank_to_rankid(rank):
    key = next((k for k, v in RANK_TABLE.items() if v == rank), None)
    return key

#リソースからATK,DEF,HPの計算
def calc_status(d_resource, a_resource, rank):
    #rankから掛け算の補正を決める
    if rank == "LR":
        atk_multi = 25
        def_multi = 25
    elif rank == "UR":
        atk_multi = 20
        def_multi = 20
    elif rank == "SSR":
        atk_multi = 15
        def_multi = 15
    elif rank == "SR":
        atk_multi = 10
        def_multi = 10
    elif rank == "R":
        atk_multi = 7.5
        def_multi = 7.5
    elif rank == "UC":
        atk_multi = 4
        def_multi = 4
    else: #C
        atk_multi = 1
        def_multi = 1
    #defリソースに対する補正
    if d_resource > 500000:
        d_hosei = 0.6
    elif d_resource > 250000:
        d_hosei = 0.8
    elif d_resource > 10000:
        d_hosei = 1
    else:
        d_hosei = 5
    #atkリソースに対する補正
    if a_resource > 30000:
        a_hosei = 3
    elif a_resource > 10000:
        a_hosei = 7.5
    elif a_resource > 1000:
        a_hosei = 20
    elif a_resource > 500:
        a_hosei = 75
    elif a_resource > 100:
        a_hosei = 150
    elif a_resource > 10:
        a_hosei = 1500
    else:
        a_hosei = 4000
    defence  = int((d_resource*d_hosei*def_multi)**0.5*7)
    atk      = int((a_resource*a_hosei*atk_multi)**0.5*7)
    hitPoint = defence+3000
    return defence, atk, hitPoint