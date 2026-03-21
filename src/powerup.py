import flet as ft

class PowerUp:
    # 初期化
    def __init__(self, page):
        self.page = page
        # ローディングオーバーレイの参照を保持(図鑑のものを使いまわし)
        self.loading_overlay = page.overlay[1]
    def create(self):
        ####################
        # 処理開始
        ####################
        # ローディングオーバーレイを表示
        self.loading_overlay.visible = True
        self.page.update()
        try:
            target_tab = ft.Tabs(
                selected_index=0,
                length=6,
                expand=True,
                #on_change=change_tabs,
                content=ft.Column(
                    expand=True,
                    controls=[
                        ft.TabBar(
                            tab_alignment=ft.TabAlignment.CENTER,
                            tabs=[
                                ft.Tab(label="UR"),
                                ft.Tab(label="SSR"),
                                ft.Tab(label="SR"),
                                ft.Tab(label="R"),
                                ft.Tab(label="UC"),
                                ft.Tab(label="C"),
                            ],
                        ),
                        ft.TabBarView(
                            expand=True,
                            controls=[
                                ft.Container(
                                    alignment=ft.Alignment.CENTER,
                                    content=ft.Text("未実装"),
                                ),
                                ft.Container(
                                    alignment=ft.Alignment.CENTER,
                                    content=ft.Text("未実装"),
                                ),
                                ft.Container(
                                    alignment=ft.Alignment.CENTER,
                                    content=ft.Text("未実装"),
                                ),
                                ft.Container(
                                    alignment=ft.Alignment.CENTER,
                                    content=ft.Text("未実装"),
                                ),
                                ft.Container(
                                    alignment=ft.Alignment.CENTER,
                                    content=ft.Text("未実装"),
                                ),
                                ft.Container(
                                    alignment=ft.Alignment.CENTER,
                                    content=ft.Text("未実装"),
                                ),
                            ],
                        ),
                    ],
                ),
            )
            #仮素材
            sozai_list = ft.ListView(
                controls=[
                ft.Row(
                    controls=[
                        ft.Text("aaa"),
                        ft.Text("bbb")
                    ]
                ),
                ft.Row(
                    controls=[
                        ft.Text("ccc"),
                        ft.Text("ddd")
                    ]
                ),
                ]
            )
            #sozai_list = 
            powerup_tab = ft.Column(
                controls=[
                    ft.Stack(
                        controls=[
                            ft.ShaderMask(
                                content=ft.Container(
                                    border=ft.Border.all(0),
                                    width=728,
                                    height=876,
                                    alignment=ft.Alignment.CENTER,
                                    bgcolor=ft.Colors.ON_PRIMARY,
                                    content=None
                                ),
                                blend_mode=ft.BlendMode.SRC_IN,
                                shader=ft.RadialGradient(
                                    center=ft.Alignment.CENTER,
                                    radius=0.22,
                                    colors=[ft.Colors.ON_PRIMARY, ft.Colors.PRIMARY_CONTAINER, ft.Colors.ON_PRIMARY],
                                    stops=[0.2, 0.8, 1.0],
                                    tile_mode=ft.GradientTileMode.REPEATED,
                                ),
                            ),
                            ft.Row(
                                width=728,
                                height=876,
                                alignment=ft.MainAxisAlignment.CENTER,
                                vertical_alignment=ft.CrossAxisAlignment.START,
                                controls=[
                                    ft.Container(
                                        width=450,
                                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREY_900),
                                        alignment=ft.Alignment.TOP_CENTER,
                                        content=ft.Column(
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                            controls=[
                                                ft.Text("対象"),
                                                ft.Divider(color=ft.Colors.GREY, height=1),
                                                target_tab
                                            ],
                                        ),
                                    ),
                                    sozai_list,
                                ],
                            ),
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
        return powerup_tab