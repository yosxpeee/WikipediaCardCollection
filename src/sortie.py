import flet as ft
import asyncio
import random
import json
import flet.canvas as cv
import math
import urllib

from utils.utils import debug_print, rankid_to_rank, rank_to_rankid, calc_damage, quality_to_rank, get_sozai_flag, get_resources, get_urls, card_data_from_db, calc_status, resource_path, switch_BGM, stop_BGM
from utils.db import get_cards_by_rankid, get_cards_by_favorite, save_cards, get_card_from_pageid, get_card_from_id, update_favorite, get_all_achievements, update_achievement
from utils.ui import create_ranked_tabs, create_sortie_formation_image, create_card_image, create_reward_items_carousel, get_card_color
from utils.webapi import fetch_random_wiki_articles, fetch_wikirank_data, fetch_wiki_info_data, fetch_wiki_summary
from utils.manage_settings import get_volume

class Sortie:
    def __init__(self, page):
        """初期化"""
        self.page = page
        # ローディングオーバーレイの参照を保持(図鑑のものを使いまわし)
        self.loading_overlay = page.overlay[1]
        self.current_select_card = {}
        # 編集中のスロット番号(0-5)
        self.current_slot_no = -1
        # 現在表示している編成タブ番号(0-7)
        self.current_tab = 0
        self.current_formation_dialog = None
        # 編成リスト: 最大8編成、それぞれ6スロット
        self.formations = [[{},{},{},{},{},{}] for _ in range(8)]
        self.current_enemies_formation = [{},{},{},{},{},{}]
        self.accordion_opened = "NORMAL"
        self.current_battle_winner = "ENEMY"
        # 編集ダイアログ内の選択状態記憶
        self._remembered_rank_index = 0
        self._remembered_sort_key = "id"
        self._remembered_sort_order = "asc"
    def achievements_check(self, level, stage):
        """実績解除処理"""
        def do_update_achievement():
            """更新処理"""
            update_achievement(int(line[0]))
            msg.append(ft.Text(f"実績を達成：{line[2]}", color=ft.Colors.BLACK))
        ach_data = get_all_achievements()
        msg = []
        for line in ach_data:
            if line[1] == "出撃" and line[4] == 0:
                if line[2] == "出撃NORMAL制覇"    and level == "NORMAL"    and stage == "Stage 3":
                    do_update_achievement()
                if line[2] == "出撃HARD制覇"      and level == "HARD"      and stage == "Stage 3":
                    do_update_achievement()
                if line[2] == "出撃VERY HARD制覇" and level == "VERY HARD" and stage == "Stage 3":
                    do_update_achievement()
                if line[2] == "出撃HARD CORE制覇" and level == "HARD CORE" and stage == "Stage 3":
                    do_update_achievement()
                if line[2] == "出撃EXTREME制覇"   and level == "EXTREME"   and stage == "Stage 3":
                    do_update_achievement()
                if line[2] == "出撃INSANE制覇"    and level == "INSANE"    and stage == "Stage 3":
                    do_update_achievement()
                if line[2] == "出撃TORMENT制覇"   and level == "TORMENT"   and stage == "Stage 3":
                    do_update_achievement()
                if line[2] == "出撃LUNATIC制覇"   and level == "LUNATIC"   and stage == "Stage 3":
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
    async def create(self):
        """画面作成"""
        def _set_current_formation(no):
            """編成しようとしているスロット番号を記憶"""
            self.current_slot_no = no
        formation_grid = None
        def _load_sortie_formation_image(data, num):
            """編成用カードイメージをロードする"""
            try:
                nonlocal formation_grid
            except Exception:
                pass
            try:
                if formation_grid is not None:
                    formation_grid.controls[num].content = create_sortie_formation_image(data, False)
                    self.page.update()
            except Exception:
                pass
        def _load_sortie_formation_blank(num):
            """編成用カード(未配属)をロードする"""
            try:
                nonlocal formation_grid
            except Exception:
                pass
            try:
                if formation_grid is not None:
                    formation_grid.controls[num].content = ft.Text("未配属")
                    self.page.update()
            except Exception:
                pass
        def _create_formation_dialog():
            """編成用画面のダイアログ作成"""
            def _on_rank_sort_changed(rank_idx, sort_key, sort_order):
                try:
                    if rank_idx is not None:
                        self._remembered_rank_index = int(rank_idx)
                except Exception:
                    pass
                try:
                    if sort_key is not None:
                        self._remembered_sort_key = sort_key
                except Exception:
                    pass
                try:
                    if sort_order is not None:
                        self._remembered_sort_order = sort_order
                except Exception:
                    pass
                try:
                    self.page.update()
                except Exception:
                    pass
            formation_dialog = ft.AlertDialog(
                modal=True,
                title=f"編成スロット：{self.current_slot_no+1} (編成{self.current_tab+1})",
                content=ft.Container(
                    width=700,
                    expand=True,
                    content=create_ranked_tabs(
                        ranks,
                        all_cards_by_rank,
                        on_select_callback=_on_target_selected,
                        initial_state={
                            "rank_index": self._remembered_rank_index,
                            "sort_key": self._remembered_sort_key,
                            "sort_order": self._remembered_sort_order,
                        },
                        on_state_change=_on_rank_sort_changed,
                    ),
                ),
                actions=[
                    self.formation_close_button,
                    self.formation_clear_button,
                    self.formation_ok_button,
                ],
            )
            self.current_formation_dialog = formation_dialog
        def _create_blank_panel(no):
            """編成の空パネル作成"""
            return ft.Container(
                width=300,
                height=100,
                bgcolor=ft.Colors.ON_PRIMARY,
                content=ft.Text("未配置"),
                border_radius=8,
                border=ft.Border.all(1, color=ft.Colors.GREY),
                on_click=lambda x:{
                    _set_current_formation(no),
                    _create_formation_dialog(),
                    self.page.show_dialog(self.current_formation_dialog),
                },
            )
        def _expansion_tile_control(level, toggle):
            """"アコーディオンメニュー制御"""
            if toggle:
                for item in sortie_tab.controls[3].controls[1].controls:
                    if item.title.value != level:
                        item.expanded = False
                    else:
                        item.expanded = True
                        self.accordion_opened = level
                        _save_sortie_info()
            else:
                if level == self.accordion_opened:
                    for item in sortie_tab.controls[3].controls[1].controls:
                        if item.title.value == level:
                            item.expanded = True
        def _create_formation_grid(formation_data, isEnemy):
            """戦闘画面用の編成表示"""
            data_images = []
            for info in formation_data:
                image = create_sortie_formation_image(info, isEnemy)
                data_images.append(image)
            data = []
            for image in data_images:
                if isEnemy:
                    data.append(
                        ft.Row(
                            expand=True,
                            spacing=1,
                            controls=[
                                ft.RotatedBox(
                                    quarter_turns=3,
                                    content=ft.ProgressBar(
                                        width=100,
                                        height=5,
                                        bar_height=5,
                                        value=1.0,
                                        color=ft.Colors.BLUE,
                                    ),
                                ),
                                ft.Container(
                                    width=16,
                                    height=20,
                                ),
                                image,
                            ],
                        ),
                    )
                else:
                    data.append(
                        ft.Row(
                            expand=True,
                            spacing=1,
                            controls=[
                                image,
                                ft.RotatedBox(
                                    quarter_turns=3,
                                    content=ft.ProgressBar(
                                        width=100,
                                        height=5,
                                        bar_height=5,
                                        value=1.0,
                                        color=ft.Colors.BLUE,
                                    ),
                                ),
                            ],
                        ),
                    )
            return ft.GridView(
                width=200,
                height=606,
                child_aspect_ratio=2,
                runs_count=1,
                run_spacing=0,
                spacing=1,
                controls=[
                    data[0],
                    data[1],
                    data[2],
                    data[3],
                    data[4],
                    data[5],
                ],
            )
        def _start_battle(level, stage):#data, title):
            """戦闘ダイアログを表示する"""
            async def _reload_sortie_tab():
                """画面リロード"""
                try:
                    # タブを一時的に無効化する
                    tabs_widget = self.page.controls[0]
                    tabs_widget.disabled = True
                    tabs_widget.update()
                    # create() は自身でオーバーレイを表示/非表示するのでそのまま await する
                    content = await self.create()
                    tab_bar_view = tabs_widget.content.controls[1]
                    tab_bar_view.controls[4] = ft.Container(
                        content=content,
                        alignment=ft.Alignment.CENTER,
                    )
                    tab_bar_view.update()
                    # タブを再有効化する
                    tabs_widget.disabled = False
                    tabs_widget.update()
                except Exception:
                    tabs_widget = self.page.controls[0]
                    tab_bar_view = tabs_widget.content.controls[1]
                    tab_bar_view.controls[4] = ft.Column([ft.Text("読み込みに失敗しました。")])
                    tab_bar_view.update()
                    tabs_widget.disabled = False
                    tabs_widget.update()
            async def _get_reward(rewards):
                """報酬取得"""
                def _draw_hexagram(type):
                    """魔法陣の描画"""
                    def get_star_points(n, r, offset_angle=0):
                        """描画位置を取得"""
                        return [
                            ft.Offset(
                                center + r * math.cos((2 * math.pi * i / n) + offset_angle),
                                center + r * math.sin((2 * math.pi * i / n) + offset_angle)
                            ) for i in range(n)
                        ]
                    def create_triangle_path(points):
                        """ヘキサグラム（六角星）のパスを生成する関数"""
                        elements = [cv.Path.MoveTo(points[0].x, points[0].y)]
                        for p in points[1:]:
                            elements.append(cv.Path.LineTo(p.x, p.y))
                        elements.append(cv.Path.Close())
                        return cv.Path(elements, stroke_paint)
                    size = 400
                    center = size / 2
                    radius = 180
                    # Paintオブジェクトの設定
                    stroke_paint = ft.Paint(
                        stroke_width=2,
                        style=ft.PaintingStyle.STROKE,
                        color=ft.Colors.WHITE,
                    )
                    # 描画要素のリスト
                    shapes = [
                        cv.Circle(center, center, radius, stroke_paint),
                        cv.Circle(center, center, radius - 10, stroke_paint),
                        create_triangle_path(get_star_points(3, radius - 20, -math.pi/2)),
                        create_triangle_path(get_star_points(3, radius - 20, math.pi/2)),
                        cv.Circle(center, center, radius * 0.4, stroke_paint),
                    ]
                    canvas = cv.Canvas(
                        shapes=shapes,
                        width=size,
                        height=size,
                    )
                    return ft.Container(content=canvas, alignment=ft.Alignment.CENTER, expand=True, scale=ft.Scale(0.75) if type=="sub" else ft.Scale(1))
                def _on_fav_changed(card_id, current_fav, external_update=False):
                    """報酬ダイアログ内でお気に入りが変更されたときのハンドラ
                    - DB の更新は外部呼び出し側が既に行っている場合があるので
                      external_update フラグを尊重する
                    - ローカルの items_for_db リスト内の該当エントリの favorite を更新する
                    """
                    try:
                        new_val = int(current_fav)
                    except Exception:
                        new_val = 1
                    # 外部が更新していない場合はここで DB を更新
                    if not external_update:
                        try:
                            update_favorite(card_id, new_val)
                        except Exception:
                            pass
                    # ローカルの保存リストを更新して UI 一貫性を保つ
                    try:
                        for d in items_for_db:
                            # saved cards have 'id' (DB PK) or 'pageId'
                            if d.get("id") is not None and str(d.get("id")) == str(card_id):
                                d["favorite"] = new_val
                            elif str(d.get("pageId")) == str(card_id):
                                d["favorite"] = new_val
                    except Exception:
                        pass
                    try:
                        self.page.update()
                    except Exception:
                        pass
                    # 全体 UI を最新化（編成タブ等を再読み込み）
                    try:
                        asyncio.create_task(_reload_sortie_tab())
                    except Exception:
                        pass
                def revert_hexagram_color():
                    """魔法陣の色を元に戻す"""
                    canvas_shapes = self.loading_overlay.controls[1].content.content.shapes
                    for i in range(len(canvas_shapes)):
                        canvas_shapes[i].paint = ft.Paint(
                            stroke_width=2,
                            style=ft.PaintingStyle.STROKE,
                            color=ft.Colors.WHITE,
                        )
                    self.loading_overlay.controls[1].content.content.update()
                await asyncio.sleep(0.2)
                await stop_BGM(self.page)
                if self.current_battle_winner == "ENEMY":
                    switch_BGM(self.page, "bgm_sortie", get_volume())
                    return
                if rewards == []:
                    switch_BGM(self.page, "bgm_sortie", get_volume())
                    return
                items_for_db = []
                switch_BGM(self.page, "bgm_sortie_reward", get_volume())
                for item in rewards:
                    if str(item).startswith("gacha"):
                        #ガチャを回す場合
                        gacha_num = int(str(item).replace("gacha", ""))
                        reward_overlay = ft.Stack(
                            expand=True,
                            controls=[
                                # 下地
                                ft.ShaderMask(
                                    content=ft.Container(
                                        border=ft.Border.all(0),
                                        alignment=ft.Alignment.CENTER,
                                        bgcolor=ft.Colors.with_opacity(0.88, ft.Colors.BLACK),
                                        content=None
                                    ),
                                    blend_mode=ft.BlendMode.SRC_IN,
                                    shader=ft.RadialGradient(
                                        center=ft.Alignment.CENTER,
                                        radius=0.5,
                                        colors=[ft.Colors.DEEP_PURPLE_900, ft.Colors.INDIGO_900, ft.Colors.DEEP_PURPLE_900],
                                        stops=[0.2, 0.8, 1.0],
                                        tile_mode=ft.GradientTileMode.REPEATED,
                                    ),
                                ),
                                # 魔法陣
                                ft.Container(
                                    content=_draw_hexagram("main"),
                                    alignment=ft.Alignment.CENTER,
                                    expand=True
                                ),
                                ft.Container(
                                    content=_draw_hexagram("sub"),
                                    top=0,
                                    left=0,
                                    expand=True
                                ),
                                ft.Container(
                                    content=_draw_hexagram("sub"),
                                    top=0,
                                    left=768-400-20,
                                    expand=True
                                ),
                                ft.Container(
                                    content=_draw_hexagram("sub"),
                                    top=1024-400-40,
                                    left=0,
                                    expand=True
                                ),
                                ft.Container(
                                    content=_draw_hexagram("sub"),
                                    top=1024-400-40,
                                    left=768-400-20,
                                    expand=True
                                ),
                                # メッセージ
                                ft.Container(
                                    alignment=ft.Alignment.CENTER,
                                    expand=True,
                                    content=ft.Text("状態更新",color=ft.Colors.WHITE),
                                ),
                            ]
                        )
                        self.page.overlay[2] = reward_overlay
                        # オーバーレイの切り替え
                        self.loading_overlay = self.page.overlay[2]
                        self.page.update()
                        # ここから実際にガチャを回す
                        count = 0
                        get_card_list = []
                        force_stopped = False
                        while True:
                            if count >= gacha_num:
                                break
                            self.loading_overlay.controls[6].content.value = f"ランダム記事取得中..."
                            self.loading_overlay.controls[6].update()
                            randList = await fetch_random_wiki_articles(self.page.debug, gacha_num-count)
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
                                    t_quote = urllib.parse.quote(title)
                                    self.loading_overlay.controls[6].content.value = f"ランクデータ取得中..."
                                    self.loading_overlay.controls[6].update()
                                    rank_data = await fetch_wikirank_data(self.page.debug, t_quote)
                                    if rank_data == {}:
                                        debug_print(self.page.debug, "ランクデータ取得失敗。リトライ")
                                        continue
                                    self.loading_overlay.controls[6].content.value = f"記事情報取得中..."
                                    self.loading_overlay.controls[6].update()
                                    info_data = await fetch_wiki_info_data(self.page.debug, t_quote)
                                    if info_data == {}:
                                        debug_print(self.page.debug, "記事情報取得失敗。リトライ")
                                        continue
                                    # 魔法陣の色を変えたいのでここでランクの決定と素材判定を行う
                                    try:
                                        quality = float(rank_data["result"]["ja"]["quality"])
                                    except Exception:
                                        debug_print(self.page.debug, "ランクデータ読取失敗。リトライ")
                                        debug_print(self.page.debug, f"Failed data: {rank_data}")
                                        continue
                                    rank = quality_to_rank(quality)
                                    try:
                                        isSozai = get_sozai_flag(info_data, pageid)
                                    except :
                                        debug_print(self.page.debug, "カテゴリ取得失敗。リトライ")
                                        debug_print(self.page.debug, f"Failed data: {info_data}")
                                        continue
                                    # 魔法陣の色を変える（各シェイプに新しいPaintを割り当てる）
                                    canvas_shapes = self.loading_overlay.controls[1].content.content.shapes
                                    for i in range(len(canvas_shapes)):
                                        canvas_shapes[i].paint = ft.Paint(
                                            stroke_width=2,
                                            style=ft.PaintingStyle.STROKE,
                                            color=get_card_color(rank, isSozai),
                                        )
                                    self.loading_overlay.controls[1].content.content.update()
                                    self.loading_overlay.controls[6].content.value = f"記事概要取得中..."
                                    self.loading_overlay.controls[6].update()
                                    # UI を反映してから演出を一定時間表示する
                                    await asyncio.sleep(2)
                                    extract  = await fetch_wiki_summary(self.page.debug, t_quote)
                                    if extract == "ERROR":
                                        debug_print(self.page.debug, "記事概要取得失敗。リトライ")
                                        revert_hexagram_color()
                                        continue
                                    # リソース取得
                                    try:
                                        d_resource, a_resource = get_resources(info_data, pageid)
                                    except:
                                        debug_print(self.page.debug, "リソース取得失敗。リトライ")
                                        debug_print(self.page.debug, f"Failed data: {info_data}")
                                        revert_hexagram_color()
                                        continue
                                    # URL取得
                                    try:
                                        image_url, full_url = get_urls(info_data, pageid)
                                        query = True
                                    except:
                                        debug_print(self.page.debug, "URL取得失敗。リトライ")
                                        debug_print(self.page.debug, f"Failed data: {info_data}")
                                        revert_hexagram_color()
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
                                    # 1枚引き終わったら魔法陣の色を元に戻す
                                    revert_hexagram_color()
                        if force_stopped == True:
                            self.loading_overlay.visible = False
                            self.page.show_dialog(ft.SnackBar(ft.Text("ランダム記事取得エラー。今回はガチャ報酬を取得できませんでした。"), duration=1500))
                            self.page.update()
                        # DB保存用配列に詰めなおす
                        for db_data in get_card_list:
                            items_for_db.append(db_data)
                        # オーバーレイを解いてローディングのものに戻しておく
                        self.loading_overlay.visible = False
                        self.loading_overlay = self.page.overlay[1]
                        self.page.update()
                    elif item > 99995000:
                        #マスターデータから取ってくる場合(現状は素材のみ)
                        for data in master_data:
                            if data["pageId"] == item:
                                data["rank"] = rankid_to_rank(data["rank"], data["isSozai"])
                                data["resourceRANK"] = rankid_to_rank(data["resourceRANK"], data["isSozai"])
                                items_for_db.append(data)
                    else:
                        #ここに来たらバグです…
                        pass
                if len(items_for_db) != 0:
                    #まずDBに保存して `id` を割り振る（create_card_image の _on_fav_click が id を参照するため）
                    save_cards(items_for_db)
                    #ここで一括してカードイメージを作る
                    items = []
                    for db_data in items_for_db:
                        img = create_card_image(db_data, True, True, _on_fav_changed)
                        view_data = ft.Container(
                            width=320,
                            height=480,
                            content=ft.Stack(
                                controls=[img],
                            ),
                            bgcolor=ft.Colors.GREY_100,
                            border_radius=5,
                            padding=ft.Padding.all(5),
                        )
                        items.append(view_data)
                    reward_items_view = create_reward_items_carousel(items)
                    reward_close_button = ft.TextButton("Close", disabled=True, on_click=lambda x:{
                        self.page.pop_dialog(),
                        self.achievements_check(level, stage),
                        switch_BGM(self.page, "bgm_sortie", get_volume())
                    })
                    reward_dialog =ft.AlertDialog(
                        modal=True,
                        title="戦闘報酬",
                        content=reward_items_view,
                        actions=[
                            reward_close_button
                        ]
                    )
                    self.page.show_dialog(reward_dialog)
                    reward_close_button.disabled = False
                    #ページを再読み込みする
                    asyncio.create_task(_reload_sortie_tab())
                else:
                    #ここに来ることはないはずだが念のため
                    switch_BGM(self.page, "bgm_sortie", get_volume())
            async def _sortie(player_data, enemy_data):
                """戦闘処理"""
                def append_log(s):
                    """戦闘ログ書き込み"""
                    log_list.controls.append(s)
                    self.page.update()
                def get_player_pb(idx):
                    """進行中のプログレスバー参照取得(プレイヤー側)"""
                    try:
                        return grid_player.controls[idx].controls[1].content
                    except Exception:
                        return None
                def get_enemy_pb(idx):
                    """進行中のプログレスバー参照取得(敵側)"""
                    try:
                        return grid_enemy.controls[idx].controls[0].content
                    except Exception:
                        return None
                def mark_dead_image(isEnemy, idx):
                    """指定スロットのカード画像を半透明オーバーレイと赤×印を重ねたものに差し替える"""
                    try:
                        if isEnemy:
                            row = grid_enemy.controls[idx]
                            img_index = 2
                            left = 0
                            top = 0
                        else:
                            row = grid_player.controls[idx]
                            img_index = 0
                            left = -12
                            top = 0
                        if img_index >= len(row.controls):
                            return
                        img = row.controls[img_index]
                        if getattr(img, '_dead_overlay', False):
                            return
                        overlay = ft.Container(
                            width=200,
                            height=100,
                            left=left,
                            top=top,
                            bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.GREY)
                        )
                        x_icon = ft.Container(
                            width=200,
                            height=100,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(ft.CupertinoIcons.CLEAR_THICK, color=ft.Colors.RED, size=100),
                        )
                        stack = ft.Stack(
                            alignment=ft.Alignment.CENTER,
                            controls=[img, overlay, x_icon],
                        )
                        stack._dead_overlay = True
                        row.controls[img_index] = stack
                        try:
                            self.page.update()
                        except Exception:
                            pass
                    except Exception:
                        pass
                def update_pb_color(pb, pct):
                    """プログレスバーの色更新"""
                    try:
                        if pct > 0.5:
                            pb.color = ft.Colors.BLUE
                        elif pct > 0.3:
                            pb.color = ft.Colors.YELLOW
                        elif pct > 0.1:
                            pb.color = ft.Colors.ORANGE
                        else:
                            pb.color = ft.Colors.RED
                    except Exception:
                        pass
                ####################
                # 戦闘処理開始
                ####################
                # 初期化
                await asyncio.sleep(0.2)
                await stop_BGM(self.page)
                switch_BGM(self.page, "bgm_sortie_fight", get_volume())
                log_list = battle_dialog.content.controls[1].content.controls[2]
                # 準備：最大HPと現在HPを収集
                p_max = [0]*6
                p_cur = [0]*6
                e_max = [0]*6
                e_cur = [0]*6
                for i in range(6):
                    pd = player_data[i] if i < len(player_data) else {}
                    ed = enemy_data[i] if i < len(enemy_data) else {}
                    p_max[i] = int(pd.get("HP", 0)) if pd != {} else 0
                    p_cur[i] = float(p_max[i])
                    e_max[i] = int(ed.get("HP", 0)) if ed != {} else 0
                    e_cur[i] = float(e_max[i])
                # 戦闘ループ（最大5ターン） -- 各位置ごとにプレイヤーi → 敵i の順で交互に行動
                winner = None
                for turn in range(1, 6):
                    append_log(ft.Text(f"--- ターン {turn} 開始 ---"))
                    for i in range(6):
                        # プレイヤー i の行動
                        if p_cur[i] > 0 and p_max[i] > 0:
                            alive = [j for j in range(6) if e_cur[j] > 0 and e_max[j] > 0]
                            if not alive:
                                winner = "PLAYER"
                                break
                            tgt = random.choice(alive)
                            dmg, d_type = calc_damage(self.page.debug, player_data[i], enemy_data[tgt], e_cur[tgt])
                            e_cur[tgt] = max(0.0, e_cur[tgt] - dmg)
                            append_log(ft.Text(f"プレイヤー[{player_data[i].get('title','?')}] が 敵[{enemy_data[tgt].get('title','?')}] に攻撃、{dmg}のダメージを与えた。 ({d_type})"))
                            pb = get_enemy_pb(tgt)
                            if pb is not None and e_max[tgt] > 0:
                                try:
                                    val = max(0.0, e_cur[tgt] / e_max[tgt])
                                    pb.value = val
                                    update_pb_color(pb, val)
                                except Exception:
                                    pass
                            # HP が 0 になったら画像にオーバーレイを付ける
                            if e_cur[tgt] == 0:
                                mark_dead_image(True, tgt)
                            self.page.update()
                            await asyncio.sleep(0.20)
                        # 敵 i の行動（プレイヤー i の行動後に行う）
                        if e_cur[i] > 0 and e_max[i] > 0:
                            alive_p = [j for j in range(6) if p_cur[j] > 0 and p_max[j] > 0]
                            if not alive_p:
                                winner = "ENEMY"
                                break
                            tgt_p = random.choice(alive_p)
                            dmg, d_type = calc_damage(self.page.debug, enemy_data[i], player_data[tgt_p], p_cur[tgt_p])
                            p_cur[tgt_p] = max(0.0, p_cur[tgt_p] - dmg)
                            append_log(ft.Text(f"敵[{enemy_data[i].get('title','?')}] が プレイヤー[{player_data[tgt_p].get('title','?')}] に攻撃、{dmg}のダメージを与えた。({d_type})"))
                            pbp = get_player_pb(tgt_p)
                            if pbp is not None and p_max[tgt_p] > 0:
                                try:
                                    valp = max(0.0, p_cur[tgt_p] / p_max[tgt_p])
                                    pbp.value = valp
                                    update_pb_color(pbp, valp)
                                except Exception:
                                    pass
                            # HP が 0 になったら画像にオーバーレイを付ける
                            if p_cur[tgt_p] == 0:
                                mark_dead_image(False, tgt_p)
                            self.page.update()
                            await asyncio.sleep(0.20)
                    if winner == "PLAYER":
                        append_log(ft.Text("敵を全滅させました。プレイヤー勝利！", color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE))
                        break
                    if winner == "ENEMY":
                        append_log(ft.Text("編成が全滅しました。プレイヤー敗北…", color=ft.Colors.WHITE, bgcolor=ft.Colors.RED))
                        break
                # 判定（5ターン終了）
                if winner is None:
                    p_alive = sum(1 for v in p_cur if v > 0)
                    e_alive = sum(1 for v in e_cur if v > 0)
                    if p_alive > e_alive:
                        winner = "PLAYER"
                        reason = "生存数判定"
                    elif e_alive > p_alive:
                        winner = "ENEMY"
                        reason = "生存数判定"
                    else:
                        p_hp_sum = sum(p_cur)
                        e_hp_sum = sum(e_cur)
                        if p_hp_sum > e_hp_sum:
                            winner = "PLAYER"
                            reason = "残HP合計"
                        elif e_hp_sum > p_hp_sum:
                            winner = "ENEMY"
                            reason = "残HP合計"
                        else:
                            winner = "ENEMY"
                            reason = "戦略的敗北"
                    if winner == "PLAYER":
                        append_log(ft.Text(f"--- 結果: プレイヤー勝利({reason}) ---", color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE))
                    if winner == "ENEMY":
                        append_log(ft.Text(f"--- 結果: プレイヤー敗北({reason}) ---", color=ft.Colors.WHITE, bgcolor=ft.Colors.RED))
                battle_close_button.disabled = False
                self.current_battle_winner = winner
                self.page.update()
            ####################
            # 戦闘開始画面の表示
            ####################
            data = stage_data[level][stage]
            #6枚編成済みかチェック(現在のタブ)
            for chk_data in self.formations[self.current_tab]:
                if chk_data == {}:
                    self.page.show_dialog(ft.SnackBar(ft.Text(f"必ず6枚のカードすべてを編成してください。"), duration=1500))
                    return
            num = 0
            for enemy_id in data["enemies"]:
                for enemy in master_data:
                    if enemy_id == enemy["pageId"]:
                        image_data = {
                            "id"   :enemy["pageId"],
                            "title":enemy["title"],
                            "rank" :rankid_to_rank(enemy["rank"], 0),
                            "image":enemy["imageUrl"],
                            "HP"   :enemy["HP"],
                            "ATK"  :enemy["ATK"],
                            "DEF"  :enemy["DEF"],
                        }
                        self.current_enemies_formation[num] = image_data
                        num = num + 1
                        break
            #選択した難易度に対する条件を満たしているかチェック
            for chk_data in self.formations[self.current_tab]:
                #敵の先頭のランク以上のカードが編成されていたらNG
                if rank_to_rankid(chk_data["rank"]) > rank_to_rankid(self.current_enemies_formation[0]["rank"]):
                    self.page.show_dialog(ft.SnackBar(ft.Text(f"難易度別の出撃条件を満たしていません。編成を変えてください。"), duration=1500))
                    return
            grid_player = _create_formation_grid(self.formations[self.current_tab], False)
            grid_enemy  = _create_formation_grid(self.current_enemies_formation, True )
            battle_close_button = ft.TextButton("Close", disabled=True, on_click=lambda x:{
                self.page.pop_dialog(),
                asyncio.create_task(_get_reward(data["reward"]))
            })
            battle_dialog = ft.AlertDialog(
                modal=True,
                title=f"出撃：{level} ({stage})",
                content=ft.Column(
                    controls=[
                        ft.Row(
                            spacing=0,
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                grid_player,
                                ft.Container(
                                    width=11,
                                    height=10,
                                ),
                                ft.Container(
                                    width=70,
                                    alignment=ft.Alignment.CENTER,
                                    content=ft.Text("vs", size=60),
                                ),
                                grid_enemy,
                            ],
                        ),
                        ft.Container(
                            alignment=ft.Alignment.CENTER,
                            width=640,
                            height=180,
                            bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.GREY_100),
                            content=ft.Column(
                                spacing=0,
                                controls=[
                                    ft.Text("＜＜＜戦闘ログ＞＞＞"),
                                    ft.Divider(color=ft.Colors.GREY, height=1),
                                    ft.ListView(
                                        width=640,
                                        height=160,
                                        spacing=0,
                                        auto_scroll=True,
                                        scroll=ft.ScrollMode.AUTO,
                                        controls=[],
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
                actions=[
                    battle_close_button
                ]
            )
            self.page.show_dialog(battle_dialog)
            asyncio.create_task(_sortie(self.formations[self.current_tab], self.current_enemies_formation))
        def _create_level_ui(level, subtitle, opened, disabled):
            """レベルデザイン"""
            return ft.ExpansionTile(
                width=320,
                title=ft.Text(level, weight=ft.FontWeight.BOLD, style=ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE)),
                subtitle=subtitle,
                expanded=opened,
                disabled=disabled,
                dense=True,
                controls_padding=ft.Padding.all(0),
                expanded_alignment=ft.Alignment.TOP_LEFT,
                shape=ft.BeveledRectangleBorder(side=ft.BorderSide(width=1, color=ft.Colors.ON_SURFACE)),
                collapsed_shape=ft.BeveledRectangleBorder(side=ft.BorderSide(width=1, color=ft.Colors.ON_SURFACE)),
                controls=[
                    ft.Row(
                        controls=[
                            ft.OutlinedButton(
                                "Stage 1", 
                                width=100,
                                style=ft.ButtonStyle(shape=ft.BeveledRectangleBorder()),
                                on_click=lambda x:_start_battle(level, "Stage 1"),
                            ),
                            ft.Text(stage_data[level]["Stage 1"]["description"]),
                        ]
                    ),
                    ft.Row(
                        controls=[
                            ft.OutlinedButton(
                                "Stage 2", 
                                width=100,
                                style=ft.ButtonStyle(shape=ft.BeveledRectangleBorder()),
                                on_click=lambda x:_start_battle(level, "Stage 2"),
                            ),
                            ft.Text(stage_data[level]["Stage 2"]["description"]),
                        ]
                    ),
                    ft.Row(
                        controls=[
                            ft.OutlinedButton(
                                "Stage 3", 
                                width=100,
                                style=ft.ButtonStyle(shape=ft.BeveledRectangleBorder()),
                                on_click=lambda x:_start_battle(level, "Stage 3"),
                            ),
                            ft.Text(stage_data[level]["Stage 3"]["description"]),
                        ]
                    ),
                ],
                on_change=lambda x:_expansion_tile_control(level, x.data),
            )
        def _on_target_selected(id, name, rk, hp, atk, deff, img):
            """選んだカード"""
            self.current_select_card = {
                "id"   :id,
                "title":name,
                "rank" :rk,
                "image":img,
                "HP"   :hp,
                "ATK"  :atk,
                "DEF"  :deff,
            }
            return
        def _refresh_formation_panels():
            """現在のタブに表示される編成パネルを更新する（グリッドとタブのハイライト）"""
            for i in range(6):
                data = self.formations[self.current_tab][i]
                if data == {}:
                    _load_sortie_formation_blank(i)
                else:
                    _load_sortie_formation_image(data, i)
            # タブボタンのハイライト更新
            for idx, btn in enumerate(tab_buttons):
                if idx == self.current_tab:
                    btn.bgcolor        = ft.Colors.ON_SURFACE
                    btn.content.color  = ft.Colors.ON_PRIMARY
                    btn.content.weight = ft.FontWeight.BOLD
                else:
                    btn.bgcolor        = ft.Colors.ON_PRIMARY
                    btn.content.color  = ft.Colors.ON_SURFACE
                    btn.content.weight = ft.FontWeight.NORMAL
        def _save_sortie_info():
            try:
                # 保存は軽量化して DB の id のみを保存する
                minimal = []
                for tab in self.formations:
                    t = []
                    for slot in tab:
                        if slot == {} or slot is None:
                            t.append({})
                        else:
                            # 優先して DB の主キー id を保存
                            if isinstance(slot, dict) and slot.get("id") is not None:
                                t.append({"id": slot.get("id")})
                            elif isinstance(slot, dict) and slot.get("pageId") is not None:
                                t.append({"pageId": slot.get("pageId")})
                            else:
                                # それ以外は空にする
                                t.append({})
                    minimal.append(t)
                with open('sortie_info.json', 'w', encoding='utf-8') as f:
                    tmp = {
                        "last_select_formation": self.current_tab,
                        "last_select_level" : self.accordion_opened,
                        "formation": minimal
                    }
                    json.dump(tmp, f, indent=4, ensure_ascii=False)
            except Exception:
                pass
        def _formation_dialog_common_update():
            """編成ダイアログの共通更新処理"""
            _set_current_formation(-1)
            self.current_select_card = {}
            _save_sortie_info()
            self.page.pop_dialog()
            _refresh_formation_panels()
            self.page.update()
        def _cancel_load_formation():
            """編成ダイアログのキャンセルボタン"""
            _set_current_formation(-1)
            self.current_select_card = {}
            self.page.pop_dialog()
            self.page.update()
        def _clear_formation():
            """編成ダイアログのクリアボタン(編成から外す)"""
            # 現在のタブのスロットをクリア
            if 0 <= self.current_slot_no < 6:
                self.formations[self.current_tab][self.current_slot_no] = {}
                _load_sortie_formation_blank(self.current_slot_no)
            _formation_dialog_common_update()
        def _apply_load_formation():
            """編成ダイアログのOKボタン"""
            hit = False
            # 同じタブ内で重複チェックしてスワップあるいは追加
            for num in range(len(self.formations[self.current_tab])):
                organized = self.formations[self.current_tab][num]
                if organized == {}:
                    continue
                if organized.get("id") == self.current_select_card.get("id"):
                    if num != self.current_slot_no:
                        # スワップ
                        if self.formations[self.current_tab][self.current_slot_no] == {}:
                            # 未配属と入れ替え
                            self.formations[self.current_tab][num] = {}
                            _load_sortie_formation_blank(num)
                            self.formations[self.current_tab][self.current_slot_no] = self.current_select_card
                            _load_sortie_formation_image(self.current_select_card, self.current_slot_no)
                        else:
                            # 編成済みと入れ替え
                            tmp = self.formations[self.current_tab][self.current_slot_no]
                            self.formations[self.current_tab][self.current_slot_no] = self.current_select_card
                            _load_sortie_formation_image(self.current_select_card, self.current_slot_no)
                            self.formations[self.current_tab][num] = tmp
                            _load_sortie_formation_image(tmp, num)
                    _formation_dialog_common_update()
                    hit = True
                    break
            # 当てはまらなければ追加
            if not hit:
                if 0 <= self.current_slot_no < 6:
                    self.formations[self.current_tab][self.current_slot_no] = self.current_select_card
                    _load_sortie_formation_image(self.current_select_card, self.current_slot_no)
                    _formation_dialog_common_update()
        ####################
        # 処理開始
        ####################
        # ローディングオーバーレイを表示
        self.loading_overlay.visible = True
        self.page.update()
        try:
            # ステージデータ読み出し
            stage_path = resource_path('src/stage_data.json')
            with open(stage_path, 'r', encoding='utf-8') as f:
                stage_data = json.load(f)
            # 対戦相手のマスターデータ読み出し
            enemy_path = resource_path('src/enemy_master_data.json')
            with open(enemy_path, 'r', encoding='utf-8') as f:
                master_data = json.load(f)
            # ダイアログのボタン作成
            self.formation_close_button = ft.TextButton(
                "キャンセル", 
                on_click=lambda e:{
                    _cancel_load_formation()
                }
            )
            self.formation_clear_button = ft.TextButton(
                "外す", 
                on_click=lambda e:{
                    _clear_formation()
                }
            )
            self.formation_ok_button = ft.TextButton(
                "編成する", 
                on_click=lambda e: {
                    _apply_load_formation()
                }
            )
            # ランクごとにDBからカード一覧を取得
            ranks = ["LR", "UR", "SSR", "SR", "R", "UC", "C", "★"]
            all_cards_by_rank = {}
            for rk in ranks:
                if rk == "★":
                    rows = await asyncio.to_thread(get_cards_by_favorite)
                else:
                    rid = rank_to_rankid(rk)
                    rows = await asyncio.to_thread(get_cards_by_rankid, rid, 0)
                all_cards_by_rank[rk] = rows
            await asyncio.sleep(1)
            # タブボタン参照リスト（作成前に宣言）
            tab_buttons = []
            for i in range(8):
                # Buttonオブジェクトだと中央寄せテキストにならないのでContainerでボタン自作
                btn = ft.Container(
                    alignment=ft.Alignment.CENTER,
                    border=ft.Border.all(1, ft.Colors.ON_SURFACE),
                    content=ft.Text(str(i+1), text_align=ft.TextAlign.CENTER),
                    width=40,
                    height=36,
                    on_click=(lambda e, idx=i: (setattr(self, 'current_tab', idx), _save_sortie_info(), _refresh_formation_panels(), self.page.update())),
                )
                tab_buttons.append(btn)
            sortie_tab = ft.Column(
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            ft.Container(
                                width=630,
                                border=ft.Border.all(width=2, color=ft.Colors.ON_SURFACE),
                                border_radius=8,
                                content=ft.Column(
                                    alignment=ft.MainAxisAlignment.START,
                                    horizontal_alignment=ft.CrossAxisAlignment.START,
                                    spacing=0,
                                    width=620,
                                    margin=ft.Margin.all(5),
                                    controls=[
                                        ft.Text("<<< 注意事項 >>>"),
                                        ft.Text("出撃には6枚のカードを編成すること。"),
                                        ft.Text("難易度別に編成できるカードに制限があります。"),
                                    ],
                                ),
                            ),
                        ],
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                        controls=[
                            ft.Container(
                                alignment=ft.Alignment.CENTER,
                                width=200,
                                content=ft.Text("編成"),
                            ),
                            ft.Container(
                                alignment=ft.Alignment.CENTER,
                                width=360,
                                content=ft.Text("出撃先"),
                            ),
                        ],
                    ),
                    ft.Divider(height=1,),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                        controls=[
                            # 編成タブ (1-8) と編成グリッド
                            ft.Column(
                                alignment=ft.MainAxisAlignment.START,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    # タブボタン: 1..8
                                    ft.Row(
                                        spacing=0,
                                        controls=tab_buttons,
                                    ),
                                    # グリッド本体 (参照は closure の formation_grid を使う)
                                    ft.GridView(
                                        width=200,
                                        height=600,
                                        child_aspect_ratio=2,
                                        runs_count=1,
                                        run_spacing=0,
                                        spacing=0,
                                        controls=[
                                            # 編成変更用のトリガー付きコンテナをロードする
                                            _create_blank_panel(0),
                                            _create_blank_panel(1),
                                            _create_blank_panel(2),
                                            _create_blank_panel(3),
                                            _create_blank_panel(4),
                                            _create_blank_panel(5),
                                        ],
                                    ),
                                ],
                            ),
                            ft.Column(
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                width=360,
                                height=600,
                                controls=[
                                    _create_level_ui("NORMAL",    "出撃制限：Cのみ",   True , False), #C
                                    _create_level_ui("HARD",      "出撃制限：UCまで",  False, False), #UC
                                    _create_level_ui("VERY HARD", "出撃制限：Rまで",   False, False), #R
                                    _create_level_ui("HARD CORE", "出撃制限：SRまで",  False, False), #SR
                                    _create_level_ui("EXTREME",   "出撃制限：SSRまで", False, False), #SSR (今のところここまで実装)
                                    _create_level_ui("INSANE",    "出撃制限：URまで",  False, False), #UR
                                    _create_level_ui("TORMENT",   "出撃制限：なし",    False, False), #LR
                                    _create_level_ui("LUNATIC",   "出撃制限：なし",    False, False), #LR+
                                ],
                            ),
                        ],
                    ),
                ],
            )
            # GridView 参照を closure 側に保持
            try:
                formation_grid = sortie_tab.controls[3].controls[0].controls[1]
            except Exception:
                formation_grid = None
            # 以前に編成したデータをそっくり読みだして編成を再現する
            try:
                with open('sortie_info.json', 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    raw = loaded.get("formation", [])
                    converted = []
                    # 新仕様: 各スロットは {} または {"id": <int>} のみを想定
                    for tab in raw:
                        new_tab = []
                        for slot in tab:
                            if not slot:
                                new_tab.append({})
                                continue
                            # {"id": N} を想定して DB から展開する
                            cid = None
                            if isinstance(slot, dict) and slot.get("id") is not None:
                                cid = slot.get("id")
                            elif isinstance(slot, int):
                                cid = slot
                            if cid is not None:
                                try:
                                    rows = await asyncio.to_thread(get_card_from_id, cid)
                                except Exception:
                                    rows = []
                                if rows and len(rows) > 0:
                                    row = rows[0]
                                    new_tab.append({
                                        "id": row[0],
                                        "title": row[2],
                                        "rank": rankid_to_rank(row[5], row[7]),
                                        "image": row[4],
                                        "HP": row[9],
                                        "ATK": row[10],
                                        "DEF": row[11],
                                    })
                                else:
                                    new_tab.append({})
                            else:
                                # 仕様外のデータは無視して空スロットにする
                                new_tab.append({})
                        converted.append(new_tab)
                    # 正規化: 常に8タブ×6スロットの構造に整える
                    normalized = [[{} for _ in range(6)] for _ in range(8)]
                    for i, tab in enumerate(converted):
                        if i >= 8:
                            break
                        for j in range(min(6, len(tab))):
                            v = tab[j]
                            normalized[i][j] = v if isinstance(v, dict) else {}
                    self.formations = normalized
                    # 表示更新
                    self.current_tab = loaded.get("last_select_formation", 0)
                    _expansion_tile_control(loaded.get("last_select_level", self.accordion_opened), True)
                    _refresh_formation_panels()
            except Exception:
                # ファイルがなかった場合（新規プレイ時）編成パネルの更新処理だけは行う
                _refresh_formation_panels()
        finally:
            # ローディングオーバーレイを非表示（例外が起きても必ず閉じる）
            try:
                self.loading_overlay.visible = False
                self.page.update()
            except Exception:
                pass
        # 他タブと雰囲気を揃えた淡い背景グラデーションでラップして返す
        view = ft.Stack(
            controls=[
                ft.ShaderMask(
                    content=ft.Container(
                        border=ft.Border.all(0),
                        width=738,
                        height=910,
                        alignment=ft.Alignment.CENTER,
                        bgcolor=ft.Colors.ON_PRIMARY,
                        content=None,
                    ),
                    blend_mode=ft.BlendMode.SRC_IN,
                    shader=ft.RadialGradient(
                        center=ft.Alignment.CENTER,
                        radius=0.5,
                        colors=[
                            ft.Colors.with_opacity(0.5, ft.Colors.ON_PRIMARY),
                            ft.Colors.with_opacity(0.5, ft.Colors.PRIMARY_CONTAINER),
                            ft.Colors.with_opacity(0.5, ft.Colors.ON_PRIMARY),
                            ft.Colors.with_opacity(0.5, ft.Colors.PRIMARY_CONTAINER),
                            ft.Colors.with_opacity(0.5, ft.Colors.ON_PRIMARY),
                        ],
                        stops=[0.2, 0.4, 0.6, 0.8, 1.0],
                        tile_mode=ft.GradientTileMode.REPEATED,
                    ),
                ),
                ft.Container(
                    content=sortie_tab,
                ),
            ],
        )
        return view
