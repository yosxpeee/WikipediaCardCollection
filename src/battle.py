import flet as ft

from utils.utils import rankid_to_rank
from utils.db import get_cards_by_sozai

class Battle:
    def __init__(self, page):
        """初期化"""
        self.page = page
    def create(self):
        """画面作成"""
        def toggle_button(caller):
            upper_menu.content.controls[0].bgcolor = ft.Colors.GREY
            upper_menu.content.controls[1].bgcolor = ft.Colors.GREY
            upper_menu.content.controls[2].bgcolor = ft.Colors.GREY
            upper_menu.content.controls[3].bgcolor = ft.Colors.GREY
            lower_screen.controls[0].visible = False
            lower_screen.controls[1].visible = False
            lower_screen.controls[2].visible = False
            lower_screen.controls[3].visible = False
            if caller == "mock":
                upper_menu.content.controls[0].bgcolor = ft.Colors.BLUE
                lower_screen.controls[0].visible = True
            elif caller == "unimplemented1":
                upper_menu.content.controls[1].bgcolor = ft.Colors.BLUE
                lower_screen.controls[1].visible = True
            elif caller == "unimplemented2":
                upper_menu.content.controls[2].bgcolor = ft.Colors.BLUE
                lower_screen.controls[2].visible = True
            else:
                upper_menu.content.controls[3].bgcolor = ft.Colors.BLUE
                lower_screen.controls[3].visible = True
            self.page.update()
        ####################
        # 処理開始
        ####################
        # DBから全カード取得
        all_cards = get_cards_by_sozai(0)
        # 上部
        upper_menu = ft.Container(
            alignment=ft.Alignment.CENTER,
            width=738,
            height=150,
            bgcolor=ft.Colors.LIGHT_BLUE,
            border_radius=50,
            content=ft.Row(
                spacing=0,
                alignment=ft.MainAxisAlignment.CENTER,
                expand=True,
                controls=[
                    ft.Container(
                        bgcolor=ft.Colors.GREY,
                        content=ft.Stack(
                            alignment=ft.Alignment.CENTER,
                            controls=[
                                ft.Image(
                                    src="battle_mock.png",
                                    width=150,
                                    height=150,
                                ),
                                ft.Text("模擬戦", size=30, color=ft.Colors.WHITE),
                            ],
                        ),
                        tooltip="所有するカード同士での1vs1のバトルを行います。",
                        on_click=lambda:toggle_button("mock"),
                    ),
                    ft.Container(
                        bgcolor=ft.Colors.GREY,
                        content=ft.Stack(
                            alignment=ft.Alignment.CENTER,
                            controls=[
                                ft.Icon(
                                    ft.Icons.BLOCK,
                                    size=150,
                                ),
                                ft.Text("未実装", size=30, color=ft.Colors.WHITE)
                            ],
                        ),
                        on_click=lambda:toggle_button("unimplemented1"),
                    ),
                    ft.Container(
                        bgcolor=ft.Colors.GREY,
                        content=ft.Stack(
                            alignment=ft.Alignment.CENTER,
                            controls=[
                                ft.Icon(
                                    ft.Icons.BLOCK,
                                    size=150,
                                ),
                                ft.Text("未実装", size=30, color=ft.Colors.WHITE)
                            ],
                        ),
                        on_click=lambda:toggle_button("unimplemented2"),
                    ),
                    ft.Container(
                        bgcolor=ft.Colors.GREY,
                        content=ft.Stack(
                            alignment=ft.Alignment.CENTER,
                            controls=[
                                ft.Icon(
                                    ft.Icons.BLOCK,
                                    size=150,
                                ),
                                ft.Text("未実装", size=30, color=ft.Colors.WHITE)
                            ],
                        ),
                        on_click=lambda:toggle_button("unimplemented3"),
                    ),
                ]
            )
        )
        # 下部
        # 模擬戦（シングル）のパーツ
        # 左のリスト
        mogi_leftlist = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text("ここにリスト表示する"),
                ft.Text("ここにリスト表示する"),
                ft.Text("ここにリスト表示する"),
                ft.Text("ここにリスト表示する"),
            ],
        )
        # 右の相手を選ぶボタン
        mogi_rightlist = ft.Column(
            expand=True,
            controls=[
                ft.Button(content="C級からランダム"),
                ft.Button(content="UC級からランダム"),
                ft.Button(content="R級からランダム"),
                ft.Button(content="SR級からランダム"),
                ft.Button(content="SSR級からランダム"),
                ft.Button(content="UR級からランダム"),
                ft.Button(content="LR級からランダム"),
                ft.Divider(height=1),
            ]
        )
        lower_screen = ft.Stack(
            controls=[
                ft.Container(       #模擬戦(シングル)
                    alignment=ft.Alignment.CENTER,
                    width=738,
                    height=720,
                    bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.GREY),
                    border_radius=8,
                    border=ft.Border.all(width=1, color=ft.Colors.GREY),
                    visible=False,
                    content=ft.Row(
                        controls=[
                            mogi_leftlist,
                            mogi_rightlist
                        ],
                    ),
                ),
                ft.Container(       #未実装
                    alignment=ft.Alignment.CENTER,
                    width=738,
                    height=720,
                    bgcolor=ft.Colors.ORANGE,
                    border_radius=8,
                    border=ft.Border.all(width=1, color=ft.Colors.GREY),
                    visible=False,
                ),
                ft.Container(       #未実装
                    alignment=ft.Alignment.CENTER,
                    width=738,
                    height=720,
                    bgcolor=ft.Colors.GREEN,
                    border_radius=8,
                    border=ft.Border.all(width=1, color=ft.Colors.GREY),
                    visible=False,
                ),
                ft.Container(       #未実装
                    alignment=ft.Alignment.CENTER,
                    width=738,
                    height=720,
                    bgcolor=ft.Colors.PURPLE,
                    border_radius=8,
                    border=ft.Border.all(width=1, color=ft.Colors.GREY),
                    visible=False,
                ),
            ]
        )
        # バトルタブ本体
        battle_tab = ft.Column(
            controls=[
                upper_menu,
                lower_screen,
            ],
        )
        #選択しておく
        toggle_button("mock"),
        return battle_tab