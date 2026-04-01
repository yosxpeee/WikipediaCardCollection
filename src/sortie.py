import flet as ft
import asyncio

from utils.utils import RANK_TABLE, debug_print, rankid_to_rank, rank_to_rankid, calc_status, create_card_image_data
from utils.db import get_card_from_id, rankup_card, get_cards_by_rankid, get_cards_by_sozai, get_cards_by_favorite
from utils.ui import create_ranked_tabs, create_sortie_formation_image

class Sortie:
    def __init__(self, page):
        """初期化"""
        self.page = page
        # ローディングオーバーレイの参照を保持(図鑑のものを使いまわし)
        self.loading_overlay = page.overlay[1]
        self.current_formation_no = -1
        self.current_select_card = {}
        self.current_formation_dialog = None
        self.current_formation = [{},{},{},{},{},{}]
        self.accordion_opened = "NORMAL"
    async def create(self):
        """画面作成"""
        def _set_current_formation(no):
            """編成しようとしている編隊番号を記憶"""
            self.current_formation_no = no
        def _load_sortie_formation_image(data):
            """編成用カードイメージをロードする"""
            sortie_tab.controls[1].controls[0].controls[0].controls[self.current_formation_no].content = create_sortie_formation_image(data)
            sortie_tab.update()
        def _create_formation_dialog():
            """編成用画面のダイアログ作成"""
            formation_dialog = ft.AlertDialog(
                modal=True,
                title=f"編成：{self.current_formation_no+1}",
                content=ft.Container(
                    width=700,
                    expand=True,
                    content=create_ranked_tabs(ranks, all_cards_by_rank, on_select_callback=_on_target_selected),
                ),
                actions=[
                    self.close_button,
                    self.ok_button,
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
                for item in sortie_tab.controls[1].controls[1].controls:
                    if item.title != level:
                        item.expanded = False
                    else:
                        self.accordion_opened = level
            else:
                if level == self.accordion_opened:
                    for item in sortie_tab.controls[1].controls[1].controls:
                        if item.title == level:
                            item.expanded = True

        def _create_level_ui(level, opened):
            """レベルデザイン"""
            return ft.ExpansionTile(
                width=320,
                title=level,
                expanded=opened,
                dense=True,
                expanded_alignment=ft.Alignment.TOP_LEFT,
                shape=ft.BeveledRectangleBorder(side=ft.BorderSide(width=2, color=ft.Colors.ON_SURFACE)),
                collapsed_shape=ft.BeveledRectangleBorder(side=ft.BorderSide(width=2, color=ft.Colors.ON_SURFACE)),
                controls=[
                    ft.FilledButton("Stage 1"),
                    ft.FilledButton("Stage 2"),
                    ft.FilledButton("Stage 3"),
                    ft.FilledButton("Stage 4"),
                    ft.FilledButton("Stage 5"),
                ],
                on_change=lambda x:_expansion_tile_control(level, x.data),
            )
        def _on_target_selected(id, name, rk, hp, atk, deff, img):
            """選んだカード"""
            print(f"編成対象：{self.current_formation_no+1}")
            print(f"{id}, {name}, {rk}, {hp}, {atk}, {deff}, {img}")
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
        def _cancel_load_formation():
            """編成ダイアログのキャンセルボタン"""
            _set_current_formation(-1)
            self.current_select_card = {}
            self.page.pop_dialog()
        def _apply_load_formation():
            """編成ダイアログのOKボタン"""
            canceled = False
            for organized in self.current_formation:
                if organized == {}:
                    continue
                if organized["id"] == self.current_select_card["id"]:
                    self.page.pop_dialog()
                    self.page.show_dialog(ft.SnackBar(ft.Text("同一カードを複数枚編成することはできません。"), duration=1500))
                    _set_current_formation(-1)
                    self.current_select_card = {}
                    canceled = True
                    break
            if canceled == False:
                self.current_formation[self.current_formation_no] = self.current_select_card
                _load_sortie_formation_image(self.current_select_card)
                _set_current_formation(-1)
                self.current_select_card = {}
                self.page.pop_dialog()
        ####################
        # 処理開始
        ####################
        # ローディングオーバーレイを表示
        self.loading_overlay.visible = True
        self.page.update()
        # ダイアログのボタン作成
        self.close_button = ft.TextButton(
            "Cancel", 
            on_click=lambda e:{
                _cancel_load_formation()
            }
        )
        self.ok_button = ft.TextButton(
            "OK", 
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
        try:
            await asyncio.sleep(1)
            sortie_tab = ft.Column(
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                alignment=ft.Alignment.CENTER,
                                width=300,
                                content=ft.Text("編成"),
                            ),
                            ft.Container(
                                alignment=ft.Alignment.CENTER,
                                width=320,
                                content=ft.Text("出撃先"),
                            ),
                        ],
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Column(
                                alignment=ft.MainAxisAlignment.START,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.GridView(
                                        width=300,
                                        height=600,
                                        child_aspect_ratio=3,
                                        runs_count=1,
                                        run_spacing=0,
                                        spacing=0,
                                        controls=[      #Note:編成後のデータをそっくり戦闘画面に持っていく必要がある
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
                                width=320,
                                height=600,
                                controls=[
                                    _create_level_ui("NORMAL", True),     #C
                                    _create_level_ui("HARD", False),      #UC
                                    _create_level_ui("VERY HARD", False), #R
                                    _create_level_ui("HARD CORE", False), #SR
                                    _create_level_ui("EXTREME", False),   #SSR
                                    _create_level_ui("INSANE", False),    #UR
                                    _create_level_ui("TORMENT", False),   #LR
                                    _create_level_ui("LUNATIC", False),   #LR+ (まともにやったら勝てないだろうからどうするかね)
                                ],
                            ),
                        ],
                    ),
                    ft.Row(
                        width=720,
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True,
                        controls=[
                            ft.Button(
                                "出撃", 
                                expand=True, 
                                on_click=lambda x:{
                                    print(self.current_formation)
                                }
                            ),
                        ],
                    ),
                ],
            )
            #Note:以前に編成したデータをそっくり読みだして編成を再現する必要がある

        finally:
            # ローディングオーバーレイを非表示（例外が起きても必ず閉じる）
            try:
                self.loading_overlay.visible = False
                self.page.update()
            except Exception:
                pass
        return sortie_tab