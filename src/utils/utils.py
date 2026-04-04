import requests
import asyncio
import random
from requests.exceptions import Timeout

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

def do_api(debug, url, timeout=None):
    """HTTPリクエスト(API)
    timeout: seconds for requests.get; if provided, do_api will raise on timeout instead of retrying.
    """
    while True:
        try:
            response = requests.get(url, headers=HEADER, timeout=timeout)
            response.raise_for_status()  # エラー時にすぐ分かる
            break
        except Timeout as e:
            debug_print(debug, f"リクエストタイムアウト: sec={timeout} error={e}")
            break
        except Exception as e:
            debug_print(debug, f"例外発生: error={e}")
            break
    return response

async def fetch_json(debug, url, key_path=None):
    """非同期でブロッキングなHTTP呼び出しをスレッドで実行するヘルパー
    全体のタイムアウトは15秒。
    """
    def _call():
        r = do_api(debug, url, timeout=15)
        j = r.json()
        if key_path is None:
            return j
        v = j
        for k in key_path:
            v = v.get(k, {})
        return v
    # スレッド実行全体に対する保護（念のため）
    return await asyncio.wait_for(asyncio.to_thread(_call), timeout=15)

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
    type = "normal"
    #回避を計算する(ダメージ0)
    avoid_rnd = int(random.triangular(1, 100))
    print(f"回避係数: {avoid_rnd}")
    if avoid_rnd >= 50 and avoid_rnd <= 52:
        debug_print(debug, "相手が回避")
        type = "avoid"
        return 0, type
    #クリティカルを計算する(1.5倍)
    critical_rnd = int(random.triangular(1, 100))
    print(f"CRI係数: {critical_rnd}")
    if critical_rnd >= 50 and critical_rnd <= 54:
        debug_print(debug, "クリティカルダメージ発生")
        critical_damage_rate = 1.5
        type = "critical"
    else:
        critical_damage_rate = 1
    debug_print(debug, f"{id1_data["title"]} > {id2_data["title"]}")
    debug_print(debug, f"ランダム装甲: {defence_rnd}, 割合係数: {wariai_rnd}")
    if int(id2_data["DEF"])*defence_rnd - int(id1_data["ATK"])*critical_damage_rate < 0:
        #DEF*ランダム(0.7～1.3)-ATKして+200
        debug_print(debug, "実ダメージ")
        id2_damage = abs(int(id2_data["DEF"])*defence_rnd - int(id1_data["ATK"])*critical_damage_rate) + 200
    else:
        #DEF-ATKでマイナスにならない（装甲抜けなかった）場合は割合ダメージ(5%～10%)+100
        #(艦これと違って割合ダメでも倒せるようにする)
        debug_print(debug, "割合+100")
        id2_damage = int(id2_hp*wariai_rnd*critical_damage_rate) + 100
    return id2_damage, type

def create_card_image_data(data):
    """カード画像作成用のデータを作る"""
    rank = rankid_to_rank(data[5], data[7])
    rank_origin = rankid_to_rank(data[15], data[7])
    card_data = {
        "id": data[0],
        "pageId": data[1],
        "title": data[2],
        "pageUrl": data[3],
        "imageUrl": data[4],
        "rank": rank,
        "quality": data[6],
        "isSozai": data[7],
        "extract": data[8],
        "HP": data[9],
        "ATK": data[10],
        "DEF": data[11],
        "favorite": data[12],
        "resourceATK": data[13],
        "resourceDEF": data[14],
        "resourceRANK": rank_origin,
    }
    return card_data