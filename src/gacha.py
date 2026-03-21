import flet as ft
import urllib.parse
import asyncio
import time

from utils.utils import fetch_json, calc_status
from utils.db import save_cards
from utils.ui import get_card_color, create_card_image

class Gacha:
    # 初期化
    def __init__(self, page):
        self.page = page
        # ローディングオーバーレイの参照を保持
        self.loading_overlay = page.overlay[0]
    # ガチャを引く
    async def draw(self, num):
        # ランダム記事取得
        async def get_random(n):
            j = {}
            try:
                random_url = f"https://ja.wikipedia.org/w/api.php?format=json&action=query&list=random&rnnamespace=0&rnlimit={n}"
                j = await fetch_json(random_url)
            except:
                pass
            if "error" in j or j == {}:
                return []
            return j.get("query", {}).get("random", [])
        # ランク取得
        async def get_rank_data(t_quote):
            n = 0
            j = {}
            while n <= 5:
                try:
                    rank_url = f"https://api.wikirank.net/api.php?name={t_quote}&lang=ja"
                    j = await fetch_json(rank_url)
                    break
                except Exception as e:
                    print("エラー。5秒後にリトライします。")
                    j = {}
                    time.sleep(5)
                    n+=1
            return j
        # 記事の情報取得
        async def get_info_data(t_quote):
            n = 0
            j = {}
            while n <= 5:
                try:
                    info_url = f"https://ja.wikipedia.org/w/api.php?format=json&action=query&titles={t_quote}&prop=info%7Cpageimages%7Cpageprops%7Cpageviews%7Ccategories&inprop=url%7Ctalkid&pithumbsize=600"
                    j = await fetch_json(info_url)
                    break
                except Exception as e:
                    print("エラー。5秒後にリトライします。")
                    j = {}
                    time.sleep(5)
                    n+=1
            return j
        # 記事の概要取得
        async def get_summary(t_quote):
            summary_url = f"https://ja.wikipedia.org/api/rest_v1/page/summary/{t_quote}"
            j = await fetch_json(summary_url)
            if "status" in j:
                return "ERROR"
            return j.get("extract", "")
        # サムネイルのコンテンツを生成するヘルパー
        def make_thumb_content(idx, selected):
            color = get_card_color(get_card_list[idx]["rank"], get_card_list[idx]["isSozai"])
            if selected:
                # 選択時の黒い枠(内側は白)をContainerで表現
                thumb = ft.Container(
                    padding=ft.Padding.all(3),
                    bgcolor=ft.Colors.BLACK,
                    content=ft.Container(
                        padding=ft.Padding.all(3),
                        bgcolor=ft.Colors.WHITE,
                        content=ft.Stack(
                            controls=[
                                ft.Container(
                                    width=120,
                                    height=140,
                                    bgcolor=color,
                                    border_radius=6,
                                    shadow=ft.BoxShadow(
                                        blur_style=ft.BlurStyle.NORMAL,
                                        spread_radius=1,
                                        blur_radius=10,
                                        color=ft.Colors.BLACK_45,
                                        offset=ft.Offset(0, 0),
                                    ),
                                ),
                                ft.Container(
                                    width=120,
                                    height=140,
                                    alignment=ft.Alignment.CENTER,
                                    content=ft.Text("✡",size=50, color=ft.Colors.with_opacity(0.8, ft.Colors.BLACK)),
                                )
                            ],
                        ),
                    ),
                )
            else:
                thumb = ft.Stack(
                    controls=[
                        ft.Container(
                            width=120,
                            height=140,
                            bgcolor=color,
                            border_radius=8,
                            shadow=ft.BoxShadow(
                                blur_style=ft.BlurStyle.NORMAL,
                                spread_radius=1,
                                blur_radius=10,
                                color=ft.Colors.BLACK_45,
                                offset=ft.Offset(0, 0),
                            ),
                        ),
                        ft.Container(
                            width=120,
                            height=140,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Text("✡",size=50, color=ft.Colors.with_opacity(0.5, ft.Colors.BLACK)),
                        )
                    ],
                )
            return thumb
        # 選択処理の更新（外側の変数を変更するため nonlocal）
        def select_gacha_result(n):
            nonlocal selected_index, grid_controls, stack_controls
            selected_index = n
            # スタックの表示切替
            for idx, v in enumerate(self.dialog.content.controls[1].content.controls):
                v.visible = (idx == n)
            # サムネイルの再構築（選択枠を変更）
            for idx, c in enumerate(grid_controls):
                c.content = make_thumb_content(idx, idx == selected_index)
            self.dialog.update()
        # ガチャ回してる時のイメージ切り替え
        def image_slide(col, idx):
            for cnt in range(5):
                if cnt==idx:
                    col.controls[0].controls[cnt].visible = True
                else:
                    col.controls[0].controls[cnt].visible = False
        ####################
        # 処理開始
        ####################
        # ローディングオーバーレイ（進捗）を表示
        # overlay[0] は gacha のオーバーレイ（counter + progress）
        self.loading_overlay.visible = True
        # 初期化：counter と progress を 0 にする
        try:
            col = self.loading_overlay.content
            if hasattr(col, 'controls') and len(col.controls) >= 2:
                col.controls[1].controls[1].value = f"ガチャを回しています... 0/{num}"
                col.controls[1].controls[2].value = 0
        except Exception:
            pass
        self.page.update()
        count = 0
        get_card_list = []
        force_stopped = False
        while True:
            if count >= num:
                break
            # デバッグ：テスト用にdata固定
            #if count == 0:
            #    randList = [{"id":"2717179", "title":"印象"}] #素材(ソフトリダイレクト)
            #    randList = [{"id":"4059891", "title":"コニャ"}] #素材(500エラーになる)
            #    randList = [{"id":"1610365", "title":"1-(5-ホスホリボシル)-5-((5-ホスホリボシルアミノ)メチリデンアミノ)イミダゾール-4-カルボキサミドイソメラーゼ"}] #素材(バカ長い名前)
            #    randList = [{"id":"1662965", "title":"鎌倉山 (曖昧さ回避)"}] #素材
            #    randList = [{"id":"296076",  "title":"菊水町"}] #素材
            #    randList = [{"id":"4690122", "title":"2024年アメリカ合衆国選挙"}] #C (svg画像)
            #    randList = [{"id":"673688",  "title":"カール9世 (スウェーデン王)"}] #C（tif画像）
            #    randList = [{"id":"24342",   "title":"ソロモン"}] #UC
            #    randList = [{"id":"139036",  "title":"宇宙空母ブルーノア"}] #R
            #    randList = [{"id":"371",     "title":"愛媛県"}] #SR
            #    randList = [{"id":"1492869", "title":"キンシャサノキセキ"}] #SSR
            #    randList = [{"id":"1855047", "title":"新宿駅"}] #UR
            #    randList = [{"id":"228773",  "title":"ディープインパクト (競走馬)"}] #LR
            #else:
            randList = await get_random(1)
            #randList = []
            if randList == []:
                force_stopped = True
                break
            for r in randList:
                pageid = r["id"]
                title = r["title"]
                t_quote = urllib.parse.quote(title)
                rank_data = await get_rank_data(t_quote) #Rank
                info_data = await get_info_data(t_quote) #info
                if info_data == {}:
                    print("記事情報取得失敗。リトライ")
                    break
                extract  = await get_summary(t_quote) #概要
                if extract == "ERROR":
                    print("記事概要取得失敗。リトライ")
                    break
                if rank_data["result"] == "not found" :
                    #評価されていない場合はCとみなす
                    q = 0
                    rank = "C"
                else:
                    q = float(rank_data["result"]["ja"]["quality"])
                    if q == 100:
                        rank = "LR"
                    elif q >= 90:
                        rank = "UR"
                    elif q >= 80:
                        rank = "SSR"
                    elif q >= 60:
                        rank = "SR"
                    elif q >= 35:
                        rank = "R"
                    elif q >= 20:
                        rank = "UC"
                    else:
                        rank = "C"
                p_str = str(pageid)
                # 素材判定
                isAimai         = any("曖昧さ回避" in category.get("title", "") for category in info_data["query"]["pages"][p_str]["categories"])
                isSoftRedirect  = any("ソフトリダイレクト" in category.get("title", "") for category in info_data["query"]["pages"][p_str]["categories"])
                if isAimai or isSoftRedirect:
                    isSozai = 1
                else:
                    isSozai = 0
                try:
                    # リソース取得
                    d_resource = info_data["query"]["pages"][p_str]["length"]
                    a_resource = 0
                    for dayView in info_data["query"]["pages"][p_str]["pageviews"]:
                        if info_data["query"]["pages"][p_str]["pageviews"][dayView] != None:
                            a_resource = a_resource + info_data["query"]["pages"][p_str]["pageviews"][dayView]
                    query = True
                except:
                    #最新すぎる記事は情報取得できないケースがある。
                    #その場合は以降の処理をすべて行わず、引いた数もカウントアップしない。
                    print("クエリ取得できない記事。リトライします。")
                    query = False
                if query:
                    if isSozai == 0:
                        defence, atk, hitPoint = calc_status(d_resource, a_resource, rank)
                    else:
                        defence = -1
                        atk = -1
                        hitPoint = -1
                    if "thumbnail" in info_data["query"]["pages"][p_str]:
                        image_url = info_data["query"]["pages"][p_str]["thumbnail"]["source"]
                    else:
                        image_url = ""
                    full_url = info_data["query"]["pages"][p_str]["fullurl"]
                    # ↓デバッグ用にしばらく残す
                    print("#########################################################")
                    if isSozai == 1:
                        print(f"{pageid}: {title} [{rank}] ({q}) (素材)")
                    else:
                        print(f"{pageid}: {title} [{rank}] ({q})")
                    print(f"Page URL: {full_url}")
                    if extract == "":
                        print("概要: なし")
                    else:
                        print(f"概要: {extract}")
                    print(f"画像URL: {image_url}")
                    print(f"HP :{hitPoint}")
                    print(f"ATK:{atk} ({a_resource})")
                    print(f"DEF:{defence} ({d_resource})")
                    print("#########################################################")
                    # ↑デバッグ用にしばらく残す
                    get_card_list.append({
                        "pageId": pageid,
                        "title": title,
                        "pageUrl": full_url,
                        "imageUrl": image_url,
                        "rank": rank,
                        "quality": q,
                        "isSozai": isSozai,
                        "extract": extract,
                        "HP": hitPoint,
                        "ATK": atk,
                        "DEF": defence,
                        "resourceATK": a_resource,
                        "resourceDEF": d_resource,
                        "resourceRANK": rank,
                    })
                    count = count + 1
                    # 更新：プログレスとカウンタ
                    try:
                        col = self.loading_overlay.content
                        if hasattr(col, 'controls') and len(col.controls) >= 2:
                            image_slide(col, count%5)
                            col.controls[1].controls[1].value = f"ガチャを回しています... {count}/{num}"
                            # progress value between 0..1
                            col.controls[1].controls[2].value = count / float(num)
                            col.controls[1].controls[1].update()
                            col.controls[1].controls[2].update()
                    except Exception:
                        pass
                    self.page.update()
        if force_stopped == True:
            self.loading_overlay.visible = False
            self.page.show_dialog(ft.SnackBar(ft.Text("ランダム記事取得エラー。1時間程度時間を置いてからお試しください。")))
            self.page.update()
            return
        # DBに保存する
        save_cards(get_card_list)
        # ローディングオーバーレイを非表示
        self.loading_overlay.visible = False
        self.page.update()
        # 結果を閉じるボタンの準備
        self.close_button = ft.TextButton("Close", on_click=lambda e: self.page.pop_dialog())
        # 選択インデックス（初期は0）
        selected_index = 0
        # Grid のサムネイルコントロール群を作る
        grid_controls = []
        for i in range(10):
            c = ft.Container(
                content=make_thumb_content(i, i == selected_index),
                on_click=(lambda e, idx=i: select_gacha_result(idx)),
            )
            grid_controls.append(c)
        # Stack の表示用コントロール群
        stack_controls = [create_card_image(get_card_list[i], i == selected_index) for i in range(10)]
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
            actions=[self.close_button],
            actions_alignment=ft.MainAxisAlignment.END,
            title_padding=ft.Padding.all(10),
        )
        self.page.show_dialog(self.dialog)
    # 画面作成
    def create(self):
        gacha_container=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("ガチャを回す",size=36),
                ft.Container(
                    width=200,
                    height=420,
                    bgcolor=ft.Colors.ON_PRIMARY ,
                    content=ft.Image(
                        src="gacha.png",
                        fit=ft.BoxFit.CONTAIN,
                    ),
                    on_click=lambda: asyncio.create_task(self.draw(10))
                )
            ],
        )
        return gacha_container