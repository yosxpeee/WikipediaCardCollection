import flet as ft
import urllib.parse
import asyncio

from utils.utils import debug_print, calc_status, quality_to_rank, card_data_from_db, get_sozai_flag, get_resources, get_urls
from utils.db import save_cards, get_card_from_pageid, get_all_achievements, update_achievement
from utils.ui import get_card_color, create_card_image
from utils.webapi import fetch_random_wiki_articles, fetch_wikirank_data, fetch_wiki_info_data, fetch_wiki_summary

class Gacha:
    def __init__(self, page):
        """初期化"""
        self.page = page
        # ローディングオーバーレイの参照を保持
        self.loading_overlay = page.overlay[0]
    def achievements_check(self, get_card_list):
        """実績チェック処理"""
        def do_update_achievement():
            """更新処理"""
            update_achievement(int(line[0]))
            msg.append(ft.Text(f"実績を達成：{line[2]}", color=ft.Colors.BLACK))
        ach_data = get_all_achievements()
        # あらかじめ条件に必要なデータを抽出する
        rank_statistics = {
            "--": 0,
            "C": 0,
            "UC": 0,
            "R": 0,
            "SR": 0,
            "SSR": 0,
            "UR": 0,
            "LR": 0,
        }
        hasPageIdZoro = False
        hasDoubleAtk = False
        hasDoubleDef = False
        for card in get_card_list:
            # 引いたカードのランクと数を集計
            if card["isSozai"] == 1:
                rank_statistics["--"] += 1
            else:
                rank_statistics[card["rank"]] += 1
            # DEFとATKの差を調べる
            if hasDoubleAtk == False:
                if card["ATK"] >= card["DEF"]*2 and card["isSozai"] == 0:
                    hasDoubleAtk = True
            if hasDoubleDef == False:
                if card["DEF"] >= card["ATK"]*2 and card["isSozai"] == 0:
                    hasDoubleDef = True
            # ページIDが3桁以上のゾロ目か調べる
            if hasPageIdZoro == False:
                is_all_same = len(set(str(card["pageId"]))) == 1
                if len(str(card["pageId"])) >= 3 and is_all_same == True:
                    hasPageIdZoro = True
        debug_print(self.page.debug, "########################################")
        debug_print(self.page.debug, "## statistics for achievement ##########")
        debug_print(self.page.debug, "########################################")
        debug_print(self.page.debug, f"引いたカードのランク内訳: {rank_statistics}")
        debug_print(self.page.debug, f"hasPageIdZoro: {hasPageIdZoro}")
        debug_print(self.page.debug, f"hasDoubleAtk: {hasDoubleAtk}")
        debug_print(self.page.debug, f"hasDoubleDef: {hasDoubleDef}")
        debug_print(self.page.debug, "########################################")
        msg = []
        for line in ach_data:
            if line[1] == "ガチャ" and line[4] == 0:
                if line[2] == "RED POWER":
                    #RED POWERが未達成ならSSRが含まれているか調べる
                    if rank_statistics["SSR"] >= 1:
                        do_update_achievement()
                if line[2] == "豪運":
                    #豪運が未達成ならURが含まれているか調べる
                    if rank_statistics["UR"] >= 1:
                        do_update_achievement()
                if line[2] == "伝説":
                    #伝説が未達成ならLRが含まれているか調べる
                    if rank_statistics["LR"] >= 1:
                        do_update_achievement()
                if line[2] == "奇跡":
                    #奇跡が未達成ならLRが2枚以上含まれているか調べる
                    if rank_statistics["LR"] >= 2:
                        do_update_achievement()
                if line[2] == "カス":
                    #カスが未達成なら全部Cかどうか調べる
                    if rank_statistics["C"] == 10:
                        do_update_achievement()
                if line[2] == "鉱脈を掘り当てた":
                    #鉱脈を掘り当てたが未達成なら素材カードの数が5枚以上か調べる
                    if rank_statistics["--"] >= 5:
                        do_update_achievement()
                if line[2] == "一撃の刃":
                    #一撃の刃が未達成ならATKとDEFの差を調べる
                    if hasDoubleAtk == True:
                        do_update_achievement()
                if line[2] == "鉄壁":
                    #鉄壁が未達成ならATKとDEFの差を調べる
                    if hasDoubleDef == True:
                        do_update_achievement()
                if line[2] == "BINGO":
                    #BINGOが未達成ならPageIdが3桁以上のゾロ目のカードを引いたか調べる
                    if hasPageIdZoro == True:
                        do_update_achievement()
        if msg != []:
            msg_container = ft.Column(
                controls=msg
            )
            self.page.show_dialog(
                ft.SnackBar(
                    content=msg_container, 
                    duration=1500,
                    bgcolor=ft.Colors.LIGHT_GREEN,
                )
            )
    async def draw(self, num):
        """ガチャ実行処理"""
        def _make_thumb_content(idx, selected):
            """サムネイルのコンテンツを生成するヘルパー"""
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
        def _select_gacha_result(n):
            """選択処理の更新"""
            # 外側の変数を変更するため nonlocal
            nonlocal selected_index, grid_controls, stack_controls
            selected_index = n
            # スタックの表示切替
            for idx, v in enumerate(self.dialog.content.controls[1].content.controls):
                v.visible = (idx == n)
            # サムネイルの再構築（選択枠を変更）
            for idx, c in enumerate(grid_controls):
                c.content = _make_thumb_content(idx, idx == selected_index)
            self.dialog.update()
        def _image_slide(col, idx):
            """ガチャ回してる時のイメージ切り替え"""
            for cnt in range(5):
                if cnt==idx:
                    col.controls[0].controls[cnt].visible = True
                else:
                    col.controls[0].controls[cnt].visible = False
        ####################
        # 処理開始
        ####################
        # ローディングオーバーレイ（進捗）を表示
        self.loading_overlay.visible = True
        # 初期化：counter と progress を 0 にする
        col = self.loading_overlay.content
        if hasattr(col, 'controls') and len(col.controls) >= 2:
            col.controls[1].controls[1].value = f"ガチャを回しています... 0/{num}"
            col.controls[1].controls[2].value = 0
        self.page.update()
        count = 0
        get_card_list = []
        force_stopped = False
        # 10枚記事をとってきて、途中の処理でエラーになったらスキップ
        while True:
            if count >= num:
                break
            col.controls[1].controls[3].value = f"ランダム記事取得中..."
            col.controls[1].controls[3].update()
            randList = await fetch_random_wiki_articles(self.page.debug, 10-count)
            # デバッグ用のdata固定 (コメントアウトされたデバッグデータはそのまま残す)
            #    randList[0] = {"id":"4059891", "title":"コニャ"}                      #素材(500エラーになる)
            #    randList[0] = {"id":"1662965", "title":"鎌倉山 (曖昧さ回避)"}         #素材(曖昧さ回避)
            #    randList[0] = {"id":"2717179", "title":"印象"}                        #素材(ソフトリダイレクト)
            #    randList[0] = {"id":"1610365", "title":"1-(5-ホスホリボシル)-5-((5-ホスホリボシルアミノ)メチリデンアミノ)イミダゾール-4-カルボキサミドイソメラーゼ"} #素材(バカ長い名前)
            #    randList[0] = {"id":"4690122", "title":"2024年アメリカ合衆国選挙"}    #C (svg画像)
            #    randList[0] = {"id":"673688",  "title":"カール9世 (スウェーデン王)"}  #C（tif画像）
            #    randList[0] = {"id":"24342",   "title":"ソロモン"}                    #UC
            #    randList[0] = {"id":"139036",  "title":"宇宙空母ブルーノア"}          #R
            #    randList[0] = {"id":"371",     "title":"愛媛県"}                      #SR
            #    randList[0] = {"id":"1492869", "title":"キンシャサノキセキ"}          #SSR
            #    randList[0] = {"id":"6205",    "title":"大和_(戦艦)"}                 #UR
            #    randList[0] = {"id":"24163",   "title":"武蔵_(戦艦)"}                 #UR
            #randList[0] = {"id":"333333", "title":"獄門島"}                      #R(ゾロ目)
            #randList[1] = {"id":"5145471", "title":"大谷翔平"}                      #UR
            #randList[2] = {"id":"10785", "title":"シャチ"}                      #UR
            #randList[3] = {"id":"16042", "title":"東條英機"}                      #UR
            #randList[4] = {"id":"3967", "title":"木星"}                      #UR
            #randList[5] = {"id":"2584807", "title":"マリリン・モンロー"}                      #UR
            #randList[6] = {"id":"228773",  "title":"ディープインパクト (競走馬)"} #LR
            if randList == []:
                force_stopped = True
                break
            for r in randList:
                query = False
                pageid = r["id"]
                title = r["title"]
                #すでに取得済みかどうかpageidで検索
                data_from_pageid = get_card_from_pageid(pageid)
                if len(data_from_pageid) >= 1:
                    full_url, image_url, rank, quality, isSozai, extract, hitPoint, atk, defence, a_resource, d_resource = card_data_from_db(data_from_pageid)
                    query = True
                else:
                    #かぶってない場合は通常処理(APIコールしてデータ取得)
                    t_quote = urllib.parse.quote(title)
                    col.controls[1].controls[3].value = f"ランクデータ取得中..."
                    col.controls[1].controls[3].update()
                    rank_data = await fetch_wikirank_data(self.page.debug, t_quote)
                    if rank_data == {}:
                        debug_print(self.page.debug, "ランクデータ取得失敗。リトライ")
                        continue
                    col.controls[1].controls[3].value = f"記事情報取得中..."
                    col.controls[1].controls[3].update()
                    info_data = await fetch_wiki_info_data(self.page.debug, t_quote)
                    if info_data == {}:
                        debug_print(self.page.debug, "記事情報取得失敗。リトライ")
                        continue
                    col.controls[1].controls[3].value = f"記事概要取得中..."
                    col.controls[1].controls[3].update()
                    extract  = await fetch_wiki_summary(self.page.debug, t_quote)
                    if extract == "ERROR":
                        debug_print(self.page.debug, "記事概要取得失敗。リトライ")
                        continue
                    try:
                        quality = float(rank_data["result"]["ja"]["quality"])
                    except Exception:
                        debug_print(self.page.debug, "ランクデータ読取失敗。リトライ")
                        debug_print(self.page.debug, f"Failed data: {rank_data}")
                        continue
                    rank = quality_to_rank(quality)
                    # 素材判定
                    try:
                        isSozai = get_sozai_flag(info_data, pageid)
                    except :
                        debug_print(self.page.debug, "カテゴリ取得失敗。リトライ")
                        debug_print(self.page.debug, f"Failed data: {info_data}")
                        continue
                    # リソース取得
                    try:
                        d_resource, a_resource = get_resources(info_data, pageid)
                    except:
                        debug_print(self.page.debug, "リソース取得失敗。リトライ")
                        debug_print(self.page.debug, f"Failed data: {info_data}")
                        continue
                    # URL取得
                    try:
                        image_url, full_url = get_urls(info_data, pageid)
                        query = True
                    except:
                        debug_print(self.page.debug, "URL取得失敗。リトライ")
                        debug_print(self.page.debug, f"Failed data: {info_data}")
                        continue
                if query:
                    if isSozai == 0:
                        defence, atk, hitPoint = calc_status(d_resource, a_resource, rank)
                    else:
                        defence = -1
                        atk = -1
                        hitPoint = -1
                    debug_print(self.page.debug, "#########################################################")
                    if isSozai == 1:
                        debug_print(self.page.debug, f"{pageid}: {title} [{rank}] ({quality}) (素材)")
                    else:
                        debug_print(self.page.debug, f"{pageid}: {title} [{rank}] ({quality})")
                    debug_print(self.page.debug, f"Page URL: {full_url}")
                    if extract == "":
                        debug_print(self.page.debug, "概要: なし")
                    else:
                        debug_print(self.page.debug, f"概要: {extract}")
                    debug_print(self.page.debug, f"画像URL: {image_url}")
                    debug_print(self.page.debug, f"HP :{hitPoint}")
                    debug_print(self.page.debug, f"ATK:{atk} ({a_resource})")
                    debug_print(self.page.debug, f"DEF:{defence} ({d_resource})")
                    debug_print(self.page.debug, "#########################################################")
                    get_card_list.append({
                        "pageId": pageid,
                        "title": title,
                        "pageUrl": full_url,
                        "imageUrl": image_url,
                        "rank": rank,
                        "quality": quality,
                        "isSozai": isSozai,
                        "extract": extract,
                        "HP": hitPoint,
                        "ATK": atk,
                        "DEF": defence,
                        "favorite": 0, #引いた直後なので必ず0
                        "resourceATK": a_resource,
                        "resourceDEF": d_resource,
                        "resourceRANK": rank, #引いた直後なので必ず現在のランク＝元のランク
                    })
                    count = count + 1
                    # 更新：プログレスとカウンタ
                    try:
                        col = self.loading_overlay.content
                        if hasattr(col, 'controls') and len(col.controls) >= 2:
                            _image_slide(col, count%5)
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
            self.page.show_dialog(ft.SnackBar(ft.Text("ランダム記事取得エラー。1時間程度時間を置いてからお試しください。"), duration=1500))
            self.page.update()
            return
        # DBに保存する
        save_cards(get_card_list)
        # ローディングオーバーレイを非表示
        self.loading_overlay.visible = False
        self.page.update()
        # 結果を閉じるボタンの準備
        self.close_button = ft.TextButton("Close", on_click=lambda e: (
            self.page.pop_dialog(), 
            self.achievements_check(get_card_list)
        ))
        # 選択インデックス（初期は0）
        selected_index = 0
        # Grid のサムネイルコントロール群を作る
        grid_controls = []
        for i in range(10):
            c = ft.Container(
                content=_make_thumb_content(i, i == selected_index),
                on_click=(lambda e, idx=i: _select_gacha_result(idx)),
            )
            grid_controls.append(c)
        # Stack の表示用コントロール群
        stack_controls = [create_card_image(get_card_list[i], i == selected_index, True) for i in range(10)]
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
                        bgcolor=ft.Colors.GREY_100,
                        border_radius=5,
                        padding=ft.Padding.all(5),
                    )
                ],
            ),
            actions=[self.close_button],
            actions_alignment=ft.MainAxisAlignment.END,
            title_padding=ft.Padding.all(10),
        )
        self.page.show_dialog(self.dialog)
    def create(self):
        """画面作成"""
        gacha_container=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("ガチャを回す",size=36),
                ft.Container(
                    width=200,
                    height=420,
                    content=ft.Image(
                        src="gacha.png",
                        fit=ft.BoxFit.CONTAIN,
                    ),
                    on_click=lambda: asyncio.create_task(self.draw(10))
                )
            ],
        )
        return gacha_container