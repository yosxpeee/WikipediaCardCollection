import flet as ft
import urllib.parse
import asyncio
import time

from utils.utils import fetchJson
from utils.db import saveCards
from utils.ui import getCardColor, createCardImage

class Gacha:
    # 初期化
    def __init__(self, page):
        self.page = page
        # ローディングオーバーレイの参照を保持
        self.loadingOverlay = page.overlay[0]
    # ガチャを引く
    async def draw(self, num):
        # ランダム記事取得
        async def getRandom(n):
            randomUrl = f"https://ja.wikipedia.org/w/api.php?format=json&action=query&list=random&rnnamespace=0&rnlimit={n}"
            j = await fetchJson(randomUrl)
            if "error" in j:
                return []
            return j.get("query", {}).get("random", [])
        # ランク取得
        async def getRankData(tQuote):
            n = 0
            j = {"result":"not found"}
            while n <= 5:
                try:
                    rankUrl = f"https://api.wikirank.net/api.php?name={tQuote}&lang=ja"
                    j = await fetchJson(rankUrl)
                    break
                except Exception as e:
                    print("エラー。5秒後にリトライします。")
                    time.sleep(5)
                    n+=1
            return j
        # 記事の情報取得
        async def getInfoData(tQuote):
            infoUrl = f"https://ja.wikipedia.org/w/api.php?format=json&action=query&titles={tQuote}&prop=info%7Cpageimages%7Cpageprops%7Cpageviews%7Ccategories&inprop=url%7Ctalkid&pithumbsize=600"
            j = await fetchJson(infoUrl)
            if "error" in j:
                return {}
            return j
        # 記事の概要取得
        async def getSummary(tQuote):
            summaryUrl = f"https://ja.wikipedia.org/api/rest_v1/page/summary/{tQuote}"
            j = await fetchJson(summaryUrl)
            if "status" in j:
                return "ERROR"
            return j.get("extract", "")
        # サムネイルのコンテンツを生成するヘルパー
        def makeThumbContent(idx, selected):
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
        # 選択処理の更新（外側の変数を変更するため nonlocal）
        def selectGachaResult(n):
            nonlocal selectedIndex, gridControls, stackControls
            selectedIndex = n
            # スタックの表示切替
            for idx, v in enumerate(self.dialog.content.controls[1].content.controls):
                v.visible = (idx == n)
            # サムネイルの再構築（選択枠を変更）
            for idx, c in enumerate(gridControls):
                c.content = makeThumbContent(idx, idx == selectedIndex)
            self.dialog.update()
        ####################
        # 処理開始
        ####################
        # ローディングオーバーレイ（進捗）を表示
        # overlay[0] は gacha のオーバーレイ（counter + progress）
        self.loadingOverlay.visible = True
        # 初期化：counter と progress を 0 にする
        try:
            col = self.loadingOverlay.content
            # content is Column; controls[0]=counter text, controls[1]=progress bar
            if hasattr(col, 'controls') and len(col.controls) >= 2:
                col.controls[0].value = f"ガチャを回しています... 0/{num}"
                col.controls[1].value = 0
        except Exception:
            pass
        self.page.update()
        count = 0
        getCardList = []
        while True:
            if count >= num:
                break
            # デバッグ：テスト用にdata固定
            #if count == 0:
            #    randList = [{"id":"4059891",  "title":"コニャ"}] #素材(500エラーになる)
            #    randList = [{"id":"1610365",  "title":"1-(5-ホスホリボシル)-5-((5-ホスホリボシルアミノ)メチリデンアミノ)イミダゾール-4-カルボキサミドイソメラーゼ"}] #素材(バカ長い名前)
            #    randList = [{"id":"7219",   "title":"UTC (曖昧さ回避)"}] #素材
            #elif count == 1:
            #    randList = [{"id":"296076",  "title":"菊水町"}] #素材
            #    randList = [{"id":"4690122", "title":"2024年アメリカ合衆国選挙"}] #C (svg画像)
            #elif count == 2:
            #    randList = [{"id":"673688",  "title":"カール9世 (スウェーデン王)"}] #C（tif画像）
            #elif count == 3:
            #    randList = [{"id":"24342",   "title":"ソロモン"}] #UC
            #elif count == 4:
            #    randList = [{"id":"139036",  "title":"宇宙空母ブルーノア"}] #R
            #elif count == 5:
            #    randList = [{"id":"371",     "title":"愛媛県"}] #SR
            #elif count == 6:
            #    randList = [{"id":"1492869", "title":"キンシャサノキセキ"}] #SSR
            #elif count == 7:
            #    randList = [{"id":"1855047", "title":"新宿駅"}] #UR
            #elif count == 8:
            #    randList = [{"id":"228773",  "title":"ディープインパクト (競走馬)"}] #LR
            #else:
            randList = await getRandom(1)
            for r in randList:
                pageid = r["id"]
                title = r["title"]
                tQuote = urllib.parse.quote(title)
                rankData = await getRankData(tQuote) #Rank
                infoData = await getInfoData(tQuote) #info
                if infoData == {}:
                    print("記事情報取得失敗。リトライ")
                    break
                extract  = await getSummary(tQuote) #概要
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
                        print(f"{pageid}: {title} [{rank}] ({q}) (素材)")
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
                    # 更新：プログレスとカウンタ
                    try:
                        col = self.loadingOverlay.content
                        if hasattr(col, 'controls') and len(col.controls) >= 2:
                            col.controls[0].value = f"ガチャを回しています... {count}/{num}"
                            # progress value between 0..1
                            col.controls[1].value = count / float(num)
                            col.controls[0].update()
                            col.controls[1].update()
                    except Exception:
                        pass
                    self.page.update()
        # DBに保存する
        saveCards(getCardList)
        # ローディングオーバーレイを非表示
        self.loadingOverlay.visible = False
        self.page.update()
        # 結果を閉じるボタンの準備
        self.closeButton = ft.TextButton("Close", on_click=lambda e: self.page.pop_dialog())
        # 選択インデックス（初期は0）
        selectedIndex = 0
        # Grid のサムネイルコントロール群を作る
        gridControls = []
        for i in range(10):
            c = ft.Container(
                content=makeThumbContent(i, i == selectedIndex),
                on_click=(lambda e, idx=i: selectGachaResult(idx)),
            )
            gridControls.append(c)
        # Stack の表示用コントロール群
        stackControls = [createCardImage(getCardList[i], i == selectedIndex) for i in range(10)]
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
                        controls=gridControls,
                    ),
                    ft.Container(
                        width=320,
                        height=480,
                        content=ft.Stack(
                            controls=stackControls,
                        ),
                        bgcolor=ft.Colors.GREY_100, border_radius=5,
                        padding=ft.Padding.all(5),
                    )
                ],
            ),
            actions=[self.closeButton],
            actions_alignment=ft.MainAxisAlignment.END,
            title_padding=ft.Padding.all(10),
        )
        self.page.show_dialog(self.dialog)
    # 画面作成
    def create(self):
        gachaContainer=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
               ft.Text("ガチャを回す",size=36),
               ft.IconButton(icon=ft.Icons.TOKEN, icon_size=100, on_click=lambda: asyncio.create_task(self.draw(10))),
            ],
        )
        return gachaContainer