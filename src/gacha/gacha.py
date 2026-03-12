import flet as ft
import urllib.parse
from utils.utils import doApi

class Gacha:
    # 初期化
    def __init__(self, page):
        self.page = page
    # ガチャを引く
    def draw(self, num):
        # ランダム記事取得
        def getRandom(num):
            randomUrl = f"https://ja.wikipedia.org/w/api.php?format=json&action=query&list=random&rnnamespace=0&rnlimit={num}"
            randomReq = doApi(randomUrl)
            randomJson = randomReq.json()
            return randomJson["query"]["random"]
        # ランク取得
        def getRankData(t_quote):
            # WikiRankから記事のスコアを取得する
            rankUrl = f"https://api.wikirank.net/api.php?name={t_quote}&lang=ja"
            rankReq = doApi(rankUrl)
            return rankReq.json()
        # 記事の情報取得
        def getInfoData(t_quote):
            # 記事の一般情報を取得する
            infoUrl = f"https://ja.wikipedia.org/w/api.php?format=json&action=query&titles={t_quote}&prop=info%7Cpageprops%7Cpageviews%7Ccategories&inprop=url%7Ctalkid%7Cdescription"
            infoReq = doApi(infoUrl)
            return infoReq.json()
        # 記事の概要取得
        def getSummary():
            summaryUrl = f"https://ja.wikipedia.org/api/rest_v1/page/summary/{title}"
            summaryReq = doApi(summaryUrl)
            summaryJson = summaryReq.json()
            return summaryJson["extract"]
        ####################
        # 処理開始
        ####################
        count = 0
        while True:
            if count >= num:
                break
            list = getRandom(1)
            #list = [
            #    {"id":602796,  "title":"天白川 (愛知県)"},  #LR
            #    {"id":3330550, "title":"東信電気"},         #LR
            #    {"id":337603,  "title":"火薬陰謀事件"},     #UR
            #    {"id":1855047, "title":"新宿駅"},           #UR
            #    {"id":1361153, "title":"小池百合子"},       #SSR
            #    {"id":23852,   "title":"ドイツ民主共和国"},  #SR
            #    {"id":4919272, "title":"ラヴィット!"},      #SR
            #    {"id":24364, "title":"銃"},                 #R
            #    {"id":212825, "title":"ザボン"},            #UC
            #    {"id":1755333, "title":"干鰯"},             #UC
            #    {"id":2471670, "title":"奥村ひのき"},        #C
            #    {"id":4712299, "title":"Hash Bang"},        #C  ※これはこのスクリプトでは対象外とする
            #    {"id":422707, "title":"SLF"},
            #    {"id":110949, "title":"ジョン・N・ガーナー"},
            #]
            for r in list:
                pageid = r["id"]
                title = r["title"]
                t_quote = urllib.parse.quote(title)
                rankData = getRankData(t_quote)
                if rankData["result"] == "not found" :
                    #評価されていない場合はCとみなす
                    rank = "C"
                    q = 0
                else:
                    q = float(rankData["result"]["ja"]["quality"])
                    match q:
                        case float(q) if q == 100:
                            rank = "LR"
                            atk_multi = 25
                            def_multi = 25
                        case float(q) if q >= 90:
                            rank = "UR"
                            atk_multi = 20
                            def_multi = 20
                        case float(q) if q >= 80:
                            rank = "SSR"
                            atk_multi = 15
                            def_multi = 15
                        case float(q) if q >= 60:
                            rank = "SR"
                            atk_multi = 10
                            def_multi = 10
                        case float(q) if q >= 35:
                            rank = "R"
                            atk_multi = 7.5
                            def_multi = 7.5
                        case float(q) if q >= 20:
                            rank = "UC"
                            atk_multi = 4
                            def_multi = 4
                        case _:
                            rank = "C"
                            atk_multi = 1
                            def_multi = 1
                # 記事のinfo取得
                infoData = getInfoData(t_quote)
                p_str = str(pageid)
                try:
                    d_resource = infoData["query"]["pages"][p_str]["length"]
                    query = True
                except:
                    #最新すぎる記事は情報取得できないケースがある。
                    #その場合は以降の処理をすべて行わず、引いた数もカウントアップしない。
                    print("クエリ取得できない記事。リトライします。")
                    query = False
                if query:
                    a_resource = 0
                    for dayView in infoData["query"]["pages"][p_str]["pageviews"]:
                        if infoData["query"]["pages"][p_str]["pageviews"][dayView] != None:
                            a_resource = a_resource + infoData["query"]["pages"][p_str]["pageviews"][dayView]
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
                        a_hosei = 2
                    elif a_resource > 10000:
                        a_hosei = 5
                    elif a_resource > 1000:
                        a_hosei = 10
                    elif a_resource > 100:
                        a_hosei = 100
                    elif a_resource > 10:
                        a_hosei = 2000
                    else:
                        a_hosei = 5000
                    defence  = int((d_resource*d_hosei*def_multi)**0.5*7)
                    atk      = int((a_resource*a_hosei*atk_multi)**0.5*7)
                    hitPoint = defence+3000
                    if "description" in infoData["query"]["pages"][p_str]:
                        desc = infoData["query"]["pages"][p_str]["description"]
                    else:
                        desc = ""
                    if "page_image_free" in infoData["query"]["pages"][p_str]["pageprops"]:
                        image = infoData["query"]["pages"][p_str]["pageprops"]["page_image_free"]
                        imageUrl = f"https://ja.wikipedia.org/wiki/{t_quote}#/media/File:{image}"
                    else:
                        image = ""
                        imageUrl = ""
                    # 曖昧さ回避のページかどうか
                    isSozai = any("曖昧さ回避" in category.get("title", "") for category in infoData["query"]["pages"][p_str]["categories"])
                    # 記事の概要取得
    
                    extract = getSummary()
                    print("#########################################################")
                    if isSozai:
                        print(f"{pageid}: {title} [{rank}] ({q}) ★")
                    else:
                        print(f"{pageid}: {title} [{rank}] ({q})")
                    if extract == "":
                        print(desc)
                    else:
                        print(extract)
                    print(imageUrl)
                    print(f"HP :{hitPoint}")
                    print(f"ATK:{atk}")
                    print(f"DEF:{defence}")
                    count = count + 1
    # 画面作成
    def create(self):
        gacha_container=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
               ft.Text("ガチャをひく",size=24),
               ft.IconButton(icon=ft.Icons.TOKEN, icon_size=75, on_click=lambda: self.draw(10)),
            ],
        )
        return gacha_container