import flet as ft
import asyncio

class Sortie:
    def __init__(self, page):
        """初期化"""
        self.page = page
        # ローディングオーバーレイの参照を保持(図鑑のものを使いまわし)
        self.loading_overlay = page.overlay[1]
    async def create(self):
        """画面作成"""
        def _create_card_panel():
            return ft.Container(
                width=400,
                height=100,
                bgcolor=ft.Colors.ON_PRIMARY,
                content=ft.Text("未配置"),
                border_radius=8,
                border=ft.Border.all(1, color=ft.Colors.GREY),
            )
        def _expansion_tile_control(level, toggle):
            """"アコーディオンメニュー制御"""
            if toggle:
                print(f"{level} が オープンされた")
                for item in sortie_tab.controls[1].controls[1].controls:
                    if item.title != level:
                        item.expanded = False
            else:
                print(f"{level} が クローズされた")
        def _create_level_ui(level):
            return ft.ExpansionTile(
                width=320,
                title=level,
                expanded=False,
                dense=True,
                expanded_alignment=ft.Alignment.TOP_LEFT,
                #expanded_cross_axis_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.FilledButton("Stage 1"),
                    ft.FilledButton("Stage 2"),
                    ft.FilledButton("Stage 3"),
                    ft.FilledButton("Stage 4"),
                    ft.FilledButton("Stage 5"),
                ],
                on_change=lambda x:_expansion_tile_control(level, x.data),
            )
        # ローディングオーバーレイを表示
        self.loading_overlay.visible = True
        self.page.update()
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
                                width=400,
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
                                        width=400,
                                        height=600,
                                        child_aspect_ratio=4,
                                        runs_count=1,
                                        run_spacing=0,
                                        spacing=0,
                                        controls=[
                                            ft.Container(
                                                width=400,
                                                height=100,
                                                bgcolor=ft.Colors.ON_PRIMARY,
                                                content=ft.Column(
                                                    spacing=0,
                                                    controls=[
                                                        ft.Row(
                                                            spacing=0,
                                                            controls=[
                                                                ft.Container(
                                                                    width=40,
                                                                    alignment=ft.Alignment.CENTER,
                                                                    content=ft.Text("SSR"),
                                                                ),
                                                                ft.Container(
                                                                    width=360,
                                                                    alignment=ft.Alignment.CENTER,
                                                                    content=ft.Text("ああああaaaaaaaあああああaaaaaaaaaaaaaaaああaaaaaaaaaaaaあaaaああああ",no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                                                                ),
                                                            ],
                                                        ),
                                                        ft.Row(
                                                            controls=[
                                                                ft.Image(
                                                                    width=100,
                                                                    height=74,
                                                                    src="icon.png",
                                                                    fit=ft.BoxFit.CONTAIN,
                                                                ),
                                                                ft.Column(
                                                                    spacing=0,
                                                                    controls=[
                                                                        ft.Text("HP : 11111"),
                                                                        ft.Text("DEF: 11111"),
                                                                        ft.Text("ATK: 11111"),
                                                                    ],
                                                                ),
                                                            ],
                                                        ),
                                                    ],
                                                ),
                                                border_radius=8,
                                                border=ft.Border.all(1, color=ft.Colors.GREY),
                                            ),
                                            _create_card_panel(),
                                            _create_card_panel(),
                                            _create_card_panel(),
                                            _create_card_panel(),
                                            _create_card_panel(),
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
                                    _create_level_ui("NORMAL"),    #C
                                    _create_level_ui("HARD"),      #UC
                                    _create_level_ui("VERY HARD"), #R
                                    _create_level_ui("HARD CORE"), #SR
                                    _create_level_ui("EXTREME"),   #SSR
                                    _create_level_ui("INSANE"),    #UR
                                    _create_level_ui("TORMENT"),   #LR
                                    _create_level_ui("LUNATIC"),   #LR+ (まともにやったら勝てないだろうからどうするかね)
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
                            ft.Button("出撃", expand=True),
                        ],
                    ),
                ],
            )
        finally:
            # ローディングオーバーレイを非表示（例外が起きても必ず閉じる）
            try:
                self.loading_overlay.visible = False
                self.page.update()
            except Exception:
                pass
        return sortie_tab