import flet as ft
import urllib.parse
import asyncio
import re
from utils.utils import doApi

class Gacha:
    # 初期化
    def __init__(self, page):
        self.page = page
        # ローディングオーバーレイの参照を保持
        self.loading_overlay = page.overlay[0]
    # ガチャを引く
    async def draw(self, num):
        # ローディングオーバーレイを表示
        self.loading_overlay.visible = True
        self.page.update()
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
        # ランダム記事取得
        async def getRandom(n):
            randomUrl = f"https://ja.wikipedia.org/w/api.php?format=json&action=query&list=random&rnnamespace=0&rnlimit={n}"
            j = await fetch_json(randomUrl)
            return j.get("query", {}).get("random", [])
        # ランク取得
        async def getRankData(t_quote):
            rankUrl = f"https://api.wikirank.net/api.php?name={t_quote}&lang=ja"
            j = await fetch_json(rankUrl)
            return j
        # 記事の情報取得
        async def getInfoData(t_quote):
            infoUrl = f"https://ja.wikipedia.org/w/api.php?format=json&action=query&titles={t_quote}&prop=info%7Cpageprops%7Cpageviews%7Ccategories&inprop=url%7Ctalkid"
            j = await fetch_json(infoUrl)
            print(j)
            return j
        # 記事の概要取得
        async def getSummary(title_str):
            summaryUrl = f"https://ja.wikipedia.org/api/rest_v1/page/summary/{title_str}"
            j = await fetch_json(summaryUrl)
            return j.get("extract", "")
        async def getImageUrlEntity(image):
            imageUrl = f"https://ja.wikipedia.org/w/api.php?format=json&action=query&titles=File:{image}&prop=imageinfo&iiprop=url&&iiurlwidth=300"
            j = await fetch_json(imageUrl)
            print(j)
            page = next(iter(j["query"]["pages"].values()))
            url = page["imageinfo"][0]["url"]
            if url.lower().endswith(".svg") or url.lower().endswith(".tif"):
                return page["imageinfo"][0]["thumburl"]
            else:
                return page["imageinfo"][0]["url"]
        # ランクからカードの色を決める
        def getCardColor(rank, isSozai):
            if isSozai:
                color = ft.Colors.ORANGE
            else:
                if rank == "LR":
                    color = ft.Colors.PURPLE
                elif rank == "UR":
                    color = ft.Colors.YELLOW
                elif rank == "SSR":
                    color = ft.Colors.RED
                elif rank == "SR":
                    color = ft.Colors.LIGHT_BLUE
                elif rank == "R":
                    color = ft.Colors.LIGHT_GREEN
                elif rank == "UC":
                    color = ft.Colors.GREY
                else: #C
                    color = ft.Colors.LIME_900
            return color
        def selectGachaResult(n):
            print(f"{n}番目がクリックされました")
            views = self.dialog.content.controls[1].content.controls
            cnt = 0
            for cont in views:
                if cnt == n:
                    cont.visible = True
                else:
                    cont.visible = False
                cnt+=1
        def createCardImage(data, isShow):
            # ランクとカードタイトル
            if data["isSozai"]:
                title = ft.Row(
                    controls=[
                        ft.Text(f"★"),
                        ft.Text(f"{data["title"]}")
                    ]
                )
            else:
                if data["rank"] == "SSR" or data["rank"] == "UR" or data["rank"] == "LR":
                    title = ft.Row(
                        controls=[
                            ft.Text(f"{data["rank"]}",weight=ft.FontWeight.BOLD),
                            ft.Text(f"{data["title"]}")
                        ]
                    )
                else:
                    title = ft.Row(
                        controls=[
                            ft.Text(f"{data["rank"]}"),
                            ft.Text(f"{data["title"]}")
                        ]
                    )
            # 画像
            if data["imageUrl"] != "":
                image = ft.Stack(
                    controls=[
                        ft.Container(
                            width=300,
                            height=300,
                            bgcolor=getCardColor(data["rank"], data["isSozai"]),
                            alignment=ft.Alignment.CENTER,
                            content=ft.Text("Now loading...",size=24),
                        ),
                        ft.Image(
                            src=data["imageUrl"],
                            width=300,
                            height=300,
                            fit=ft.BoxFit.CONTAIN,
                        ),
                    ],
                )
            else:
                image = ft.Container(
                    width=300,
                    height=300,
                    bgcolor=getCardColor(data["rank"], data["isSozai"]),
                    alignment=ft.Alignment.CENTER,
                    content=ft.Text("NO IMAGE",size=30),
                )
            view = ft.Container(
                alignment=ft.Alignment.CENTER,
                visible=isShow,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        title,
                        image,
                        ft.Text(f"HP : {data["HP"]}", size=24),
                        ft.Text(f"ATK: {data["ATK"]}",size=24),
                        ft.Text(f"DEF: {data["DEF"]}",size=24),
                    ],
                ),
            )
            return view
        ####################
        # 処理開始
        ####################
        count = 0
        getCardList = []
        while True:
            if count >= num:
                break
            # デバッグ：テスト用にdata固定中
            if count == 0:
                rand_list = [{"id":"7219",    "title":"UTC (曖昧さ回避)"}] #素材
            elif count == 1:
                rand_list = [{"id":"4690122", "title":"2024年アメリカ合衆国選挙"}] #C
            elif count == 2:
                rand_list = [{"id":"24342",   "title":"ソロモン"}] #UC
            elif count == 3:
                rand_list = [{"id":"139036",  "title":"宇宙空母ブルーノア"}] #R
            elif count == 4:
                rand_list = [{"id":"371", "title":"愛媛県"}] #SR
            elif count == 5:
                rand_list = [{"id":"1492869", "title":"キンシャサノキセキ"}] #SSR
            elif count == 6:
                rand_list = [{"id":"1855047", "title":"新宿駅"}] #UR
            elif count == 7:
                rand_list = [{"id":"228773",  "title":"ディープインパクト (競走馬)"}] #LR
            elif count == 8:
                rand_list = [{"id":"673688",  "title":"カール9世 (スウェーデン王)"}] #C
            else:
                rand_list = await getRandom(1)
            for r in rand_list:
                pageid = r["id"]
                title = r["title"]
                t_quote = urllib.parse.quote(title)
                rankData = await getRankData(t_quote)
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
                infoData = await getInfoData(t_quote)
                p_str = str(pageid)
                # 曖昧さ回避のページかどうか
                isSozai = any("曖昧さ回避" in category.get("title", "") for category in infoData["query"]["pages"][p_str]["categories"])
                try:
                    d_resource = infoData["query"]["pages"][p_str]["length"]
                    query = True
                except:
                    #最新すぎる記事は情報取得できないケースがある。
                    #その場合は以降の処理をすべて行わず、引いた数もカウントアップしない。
                    print("クエリ取得できない記事。リトライします。")
                    query = False
                if query:
                    if isSozai == False:
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
                    else:
                        defence = -1
                        atk = -1
                        hitPoint = -1
                    if "page_image_free" in infoData["query"]["pages"][p_str]["pageprops"]:
                        imgFileName = infoData["query"]["pages"][p_str]["pageprops"]["page_image_free"]
                        imageUrl = await getImageUrlEntity(imgFileName)
                    else:
                        imageUrl = ""
                    # 記事の概要取得
                    extract = await getSummary(title)
                    fullUrl = infoData["query"]["pages"][p_str]["fullurl"]
                    print("#########################################################")
                    if isSozai:
                        print(f"{pageid}: {title} [{rank}] ({q}) ★")
                    else:
                        print(f"{pageid}: {title} [{rank}] ({q})")
                    print(f"URL: {fullUrl}")
                    if extract == "":
                        print("")
                    else:
                        print(extract)
                    print(imageUrl)
                    print(f"HP :{hitPoint}")
                    print(f"ATK:{atk}")
                    print(f"DEF:{defence}")
                    # ↑はデバッグコードにして、dictに結果を収める
                    getCardList.append({
                        "pageId": pageid,
                        "title": title,
                        "pageUrl": fullUrl,
                        "imageUrl": imageUrl,
                        "rank": rank,
                        "quality": q,
                        "isSozai": isSozai,
                        "extract": extract,
                        "HP": hitPoint,
                        "ATK": atk,
                        "DEF": defence,
                    })
                    count = count + 1
        # ローディングオーバーレイを非表示
        self.loading_overlay.visible = False
        self.page.update()
        # 結果を表示する
        self.close_btn = ft.TextButton("Close", on_click=lambda e: self.page.pop_dialog())
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("ガチャ結果"),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                controls=[
                    ft.GridView(
                        width=700,
                        runs_count=5,
                        spacing=8,
                        child_aspect_ratio=0.8,
                        controls=[
                            ft.Container(
                                bgcolor=getCardColor(getCardList[0]["rank"], getCardList[0]["isSozai"]), border_radius=8,
                                on_click=lambda x:selectGachaResult(0),
                            ),
                            ft.Container(
                                bgcolor=getCardColor(getCardList[1]["rank"], getCardList[1]["isSozai"]), border_radius=8,
                                on_click=lambda x:selectGachaResult(1),
                            ),
                            ft.Container(
                                bgcolor=getCardColor(getCardList[2]["rank"], getCardList[2]["isSozai"]), border_radius=8,
                                on_click=lambda x:selectGachaResult(2),
                            ),
                            ft.Container(
                                bgcolor=getCardColor(getCardList[3]["rank"], getCardList[3]["isSozai"]), border_radius=8,
                                on_click=lambda x:selectGachaResult(3),
                            ),
                            ft.Container(
                                bgcolor=getCardColor(getCardList[4]["rank"], getCardList[4]["isSozai"]), border_radius=8,
                                on_click=lambda x:selectGachaResult(4),
                            ),
                            ft.Container(
                                bgcolor=getCardColor(getCardList[5]["rank"], getCardList[5]["isSozai"]), border_radius=8,
                                on_click=lambda x:selectGachaResult(5),
                            ),
                            ft.Container(
                                bgcolor=getCardColor(getCardList[6]["rank"], getCardList[6]["isSozai"]), border_radius=8,
                                on_click=lambda x:selectGachaResult(6),
                            ),
                            ft.Container(
                                bgcolor=getCardColor(getCardList[7]["rank"], getCardList[7]["isSozai"]), border_radius=8,
                                on_click=lambda x:selectGachaResult(7),
                            ),
                            ft.Container(
                                bgcolor=getCardColor(getCardList[8]["rank"], getCardList[8]["isSozai"]), border_radius=8,
                                on_click=lambda x:selectGachaResult(8),
                            ),
                            ft.Container(
                                bgcolor=getCardColor(getCardList[9]["rank"], getCardList[9]["isSozai"]), border_radius=8,
                                on_click=lambda x:selectGachaResult(9),
                            ),
                        ],
                    ),
                    ft.Container(
                        width=310,
                        height=480,
                        content=ft.Stack(
                            controls=[
                                createCardImage(getCardList[0], True),
                                createCardImage(getCardList[1], False),
                                createCardImage(getCardList[2], False),
                                createCardImage(getCardList[3], False),
                                createCardImage(getCardList[4], False),
                                createCardImage(getCardList[5], False),
                                createCardImage(getCardList[6], False),
                                createCardImage(getCardList[7], False),
                                createCardImage(getCardList[8], False),
                                createCardImage(getCardList[9], False),
                            ]
                        ),
                        bgcolor=ft.Colors.GREY_100, border_radius=5,
                        padding=ft.Padding.all(5),
                    )
                ],
            ),
            actions=[self.close_btn],
            actions_alignment=ft.MainAxisAlignment.END,
            #on_dismiss=lambda e: print("Dialog dismissed!"),
            title_padding=ft.Padding.all(10),
        )
        self.page.show_dialog(self.dialog)
    # 画面作成
    def create(self):
        gacha_container=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
               ft.Text("ガチャをひく",size=24),
               ft.IconButton(icon=ft.Icons.TOKEN, icon_size=75, on_click=lambda: asyncio.create_task(self.draw(10))),
            ],
        )
        return gacha_container