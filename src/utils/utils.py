import requests
import asyncio
import random
import random

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

def debug_print(debug, msg):
    """デバッグ出力"""
    if debug:
        print(msg)

def do_api(url):
    """HTTPリクエスト(API)"""
    while True:
        try:
            response = requests.get(url, headers=HEADER)
            response.raise_for_status()  # エラー時にすぐ分かる
            break
        except Exception as e:
            pass
    return response

async def fetch_json(url, key_path=None):
    """非同期でブロッキングなHTTP呼び出しをスレッドで実行するヘルパー"""
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

def rankid_to_rank(rankId, isSozai):
    """rank to rankid"""
    if isSozai == 1:
        return RANK_TABLE[-1]
    else:
        return RANK_TABLE[int(rankId)]

def rank_to_rankid(rank):
    """rankid to rank"""
    key = next((k for k, v in RANK_TABLE.items() if v == rank), None)
    return key

def calc_status(d_resource, a_resource, rank):
    """リソースからATK,DEF,HPの計算"""
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

def calc_damage(debug, id1_data, id2_data, id2_hp):
    """戦闘共通のダメージ計算"""
    defence_rnd = random.triangular(0.7, 1.3)
    wariai_rnd = random.triangular(0.05, 0.10)
    debug_print(debug, f"ランダム装甲: {defence_rnd}, 割合係数: {wariai_rnd}")
    if int(id2_data["DEF"])*defence_rnd - int(id1_data["ATK"]) < 0:
        #DEF*ランダム(0.7～1.3)-ATKして+200
        debug_print(debug, "実ダメージ")
        id2_damage = abs(int(id2_data["DEF"])*defence_rnd - int(id1_data["ATK"])) + 200
    else:
        #DEF-ATKでマイナスにならない（装甲抜けなかった）場合は割合ダメージ(5%～10%)+100
        #(艦これと違って割合ダメでも倒せるようにする)
        debug_print(debug, "割合+100")
        id2_damage = id2_hp*wariai_rnd + 100
    return id2_damage