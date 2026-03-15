import flet as ft
import urllib.parse
import asyncio
import webbrowser

from utils.utils import fetch_json
from utils.db import save_cards

class Gacha:
    # 初期化
    def __init__(self, page):
        self.page = page
        # ローディングオーバーレイの参照を保持
        self.loading_overlay = page.overlay[0]
    # ガチャを引く
    async def draw(self, num):
        # ランダム記事取得
        async def getRandom(n):
            randomUrl = f"https://ja.wikipedia.org/w/api.php?format=json&action=query&list=random&rnnamespace=0&rnlimit={n}"
            j = await fetch_json(randomUrl)
            if "error" in j:
                return []
            return j.get("query", {}).get("random", [])
        # ランク取得
        async def getRankData(t_quote):
            while True:
                try:
                    rankUrl = f"https://api.wikirank.net/api.php?name={t_quote}&lang=ja"
                    j = await fetch_json(rankUrl)
                    break
                except:
                    print("エラー。リトライします。")
            return j
        # 記事の情報取得
        async def getInfoData(t_quote):
            infoUrl = f"https://ja.wikipedia.org/w/api.php?format=json&action=query&titles={t_quote}&prop=info%7Cpageimages%7Cpageprops%7Cpageviews%7Ccategories&inprop=url%7Ctalkid&pithumbsize=600"
            j = await fetch_json(infoUrl)
            if "error" in j:
                return {}
            return j
        # 記事の概要取得
        async def getSummary(t_quote):
            summaryUrl = f"https://ja.wikipedia.org/api/rest_v1/page/summary/{t_quote}"
            j = await fetch_json(summaryUrl)
            if "status" in j:
                return "ERROR"
            return j.get("extract", "")
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
        # カードイメージの作成
        def createCardImage(data, isShow):
            # ランクとカードタイトル
            linkText =  ft.GestureDetector(
                content=ft.Text(
                    spans=[
                        ft.TextSpan(
                        text=f"{data["title"]}",
                            style=ft.TextStyle(
                                color=ft.Colors.BLUE,
                                decoration=ft.TextDecoration.UNDERLINE,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ),
                    ],
                ),
                mouse_cursor=ft.MouseCursor.CLICK,
                on_tap=lambda e:webbrowser.open(data["pageUrl"]),
            )
            if data["isSozai"]:
                title = ft.Row(
                    controls=[
                        ft.Text(f"★"),
                        linkText,
                    ]
                )
            else:
                if data["rank"] == "SSR" or data["rank"] == "UR" or data["rank"] == "LR":
                    title = ft.Row(
                        controls=[
                            ft.Text(f"{data["rank"]}",weight=ft.FontWeight.BOLD),
                            linkText,
                        ]
                    )
                else:
                    title = ft.Row(
                        controls=[
                            ft.Text(f"{data["rank"]}"),
                            linkText,
                        ]
                    )
            # 画像
            if data["imageUrl"] != "":
                image = ft.Stack(
                    alignment=ft.Alignment.CENTER,
                    controls=[
                        ft.Container(
                            width=310,
                            height=310,
                            bgcolor=getCardColor(data["rank"], data["isSozai"]),
                            alignment=ft.Alignment.CENTER,
                            content=ft.Container(
                                width=300,
                                height=300,
                                bgcolor=ft.Colors.WHITE
                            )
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
                    width=310,
                    height=310,
                    bgcolor=getCardColor(data["rank"], data["isSozai"]),
                    alignment=ft.Alignment.CENTER,
                    content=ft.Container(
                        width=300,
                        height=300,
                        bgcolor=ft.Colors.WHITE,
                        content=ft.Text("NO IMAGE",size=30),
                        alignment=ft.Alignment.CENTER,
                    )
                )
            #ステータス
            if data["isSozai"]:
                statuses = ft.Column(
                    controls=[
                        ft.Text(f"HP : -    ",size=24, font_family="Consolas"),
                        ft.Text(f"ATK: -    ",size=24, font_family="Consolas"),
                        ft.Text(f"DEF: -    ",size=24, font_family="Consolas"),
                    ],
                )
            else:
                statuses = ft.Column(
                    controls=[
                        ft.Text(f"HP : {data["HP"]}".ljust(10," "),  size=24,font_family="Consolas"),
                        ft.Text(f"ATK: {data["ATK"]}".ljust(10," "), size=24,font_family="Consolas"),
                        ft.Text(f"DEF: {data["DEF"]}".ljust(10," "), size=24,font_family="Consolas"),
                    ],
                )
            view = ft.Container(
                alignment=ft.Alignment.CENTER,
                visible=isShow,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        title,
                        image,
                        ft.Row(
                            controls=[
                                # ステータス
                                statuses,
                                # 概要
                                ft.Container(
                                    expand=True,
                                    content=ft.Text(
                                        data["extract"],
                                        max_lines=5,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),
            )
            return view
        # サムネイルのコンテンツを生成するヘルパー
        def make_thumb_content(idx, selected):
            color = getCardColor(getCardList[idx]["rank"], getCardList[idx]["isSozai"])
            if selected:
                # 選択時の黒い枠(内側は白)をContainerで表現
                return ft.Container(
                    padding=ft.Padding.all(3),
                    bgcolor=ft.Colors.BLACK,
                    content=ft.Container(
                        padding=ft.Padding.all(3),
                        bgcolor=ft.Colors.WHITE,
                        content=ft.Container(
                            width=120,
                            height=120,
                            bgcolor=color,
                            border_radius=6,
                        ),
                    ),
                )
            else:
                return ft.Container(
                    width=120,
                    height=120,
                    bgcolor=color,
                    border_radius=8,
                )
        ####################
        # 処理開始
        ####################
        # ローディングオーバーレイを表示
        self.loading_overlay.visible = True
        self.page.update()
        count = 0
        getCardList = []
        while True:
            if count >= num:
                break
            # デバッグ：テスト用にdata固定
            #if count == 0:
            #    rand_list = [{"id":"94872",  "title":"アイヌの一覧"}]
            #    rand_list = [{"id":"7219",   "title":"UTC (曖昧さ回避)"}] #素材
            #elif count == 1:
            #    rand_list = [{"id":"296076",  "title":"菊水町"}] #素材
            #    rand_list = [{"id":"4690122", "title":"2024年アメリカ合衆国選挙"}] #C (svg画像)
            #elif count == 2:
            #    rand_list = [{"id":"673688",  "title":"カール9世 (スウェーデン王)"}] #C（tif画像）
            #elif count == 3:
            #    rand_list = [{"id":"24342",   "title":"ソロモン"}] #UC
            #elif count == 4:
            #    rand_list = [{"id":"139036",  "title":"宇宙空母ブルーノア"}] #R
            #elif count == 5:
            #    rand_list = [{"id":"371",     "title":"愛媛県"}] #SR
            #elif count == 6:
            #    rand_list = [{"id":"1492869", "title":"キンシャサノキセキ"}] #SSR
            #elif count == 7:
            #    rand_list = [{"id":"1855047", "title":"新宿駅"}] #UR
            #elif count == 8:
            #    rand_list = [{"id":"228773",  "title":"ディープインパクト (競走馬)"}] #LR
            #else:
            rand_list = await getRandom(1)
            for r in rand_list:
                pageid = r["id"]
                title = r["title"]
                t_quote = urllib.parse.quote(title)
                rankData = await getRankData(t_quote) #Rank
                infoData = await getInfoData(t_quote) #info
                if infoData == {}:
                    print("記事情報取得失敗。リトライ")
                    break
                extract  = await getSummary(t_quote) #概要
                if extract == "ERROR":
                    print("記事概要取得失敗。リトライ")
                    break
                if rankData["result"] == "not found" :
                    #評価されていない場合はCとみなす
                    q = 0
                    rank = "C"
                    atk_multi = 1
                    def_multi = 1
                else:
                    q = float(rankData["result"]["ja"]["quality"])
                    if q == 100:
                        rank = "LR"
                        atk_multi = 25
                        def_multi = 25
                    elif q >= 90:
                        rank = "UR"
                        atk_multi = 20
                        def_multi = 20
                    elif q >= 80:
                        rank = "SSR"
                        atk_multi = 15
                        def_multi = 15
                    elif q >= 60:
                        rank = "SR"
                        atk_multi = 10
                        def_multi = 10
                    elif q >= 35:
                        rank = "R"
                        atk_multi = 7.5
                        def_multi = 7.5
                    elif q >= 20:
                        rank = "UC"
                        atk_multi = 4
                        def_multi = 4
                    else:
                        rank = "C"
                        atk_multi = 1
                        def_multi = 1
                p_str = str(pageid)
                # 素材判定
                isAimai   = any("曖昧さ回避" in category.get("title", "") for category in infoData["query"]["pages"][p_str]["categories"])
                #isList    = any(category.get("title", "").endswith("一覧") for category in infoData["query"]["pages"][p_str]["categories"])
                #isHikaku  = any("の比較" in category.get("title", "") for category in infoData["query"]["pages"][p_str]["categories"])
                #isHistory = any("年表" in category.get("title", "") for category in infoData["query"]["pages"][p_str]["categories"])
                #print(isAimai, isList, isHikaku, isHistory)
                #if isAimai or isList or isHikaku or isHistory:
                if isAimai:
                    #print(infoData["query"]["pages"][p_str]["categories"])
                    isSozai = True
                else:
                    isSozai = False
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
                        #print(def_multi)
                        #print(atk_multi)
                        defence  = int((d_resource*d_hosei*def_multi)**0.5*7)
                        atk      = int((a_resource*a_hosei*atk_multi)**0.5*7)
                        hitPoint = defence+3000
                    else:
                        defence = -1
                        atk = -1
                        hitPoint = -1
                    if "thumbnail" in infoData["query"]["pages"][p_str]:
                        imageUrl = infoData["query"]["pages"][p_str]["thumbnail"]["source"]
                    else:
                        imageUrl = ""
                    fullUrl = infoData["query"]["pages"][p_str]["fullurl"]
                    # ↓デバッグ用にしばらく残す
                    print("#########################################################")
                    if isSozai:
                        print(f"{pageid}: {title} [{rank}] ({q}) ★")
                    else:
                        print(f"{pageid}: {title} [{rank}] ({q})")
                    print(f"Page URL: {fullUrl}")
                    if extract == "":
                        print("概要: なし")
                    else:
                        print(f"概要: {extract}")
                    print(f"画像URL: {imageUrl}")
                    print(f"HP :{hitPoint}")
                    print(f"ATK:{atk}")
                    print(f"DEF:{defence}")
                    print("#########################################################")
                    # ↑デバッグ用にしばらく残す
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
        # DBに保存する
        save_cards(getCardList)
        # ローディングオーバーレイを非表示
        self.loading_overlay.visible = False
        self.page.update()
        # 結果を表示する
        self.close_btn = ft.TextButton("Close", on_click=lambda e: self.page.pop_dialog())
        # 選択インデックス（初期は0）
        selected_index = 0
        # Grid のサムネイルコントロール群を作る
        grid_controls = []
        for i in range(10):
            c = ft.Container(
                content=make_thumb_content(i, i == selected_index),
                on_click=(lambda e, idx=i: selectGachaResult(idx)),
            )
            grid_controls.append(c)
        # Stack の表示用コントロール群
        stack_controls = [createCardImage(getCardList[i], i == selected_index) for i in range(10)]
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
                        controls=grid_controls,
                    ),
                    ft.Container(
                        width=320,
                        height=480,
                        content=ft.Stack(
                            controls=stack_controls,
                        ),
                        bgcolor=ft.Colors.GREY_100, border_radius=5,
                        padding=ft.Padding.all(5),
                    )
                ],
            ),
            actions=[self.close_btn],
            actions_alignment=ft.MainAxisAlignment.END,
            title_padding=ft.Padding.all(10),
        )

        # 選択処理の更新（外側の変数を変更するため nonlocal）
        def selectGachaResult(n):
            nonlocal selected_index, grid_controls, stack_controls
            selected_index = n
            # スタックの表示切替
            for idx, v in enumerate(self.dialog.content.controls[1].content.controls):
                v.visible = (idx == n)
            # サムネイルの再構築（選択枠を変更）
            for idx, c in enumerate(grid_controls):
                c.content = make_thumb_content(idx, idx == selected_index)
            self.dialog.update()

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