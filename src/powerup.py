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
            color_gradient = ft.LinearGradient(
                begin=ft.Alignment.TOP_CENTER,
                end=ft.Alignment.BOTTOM_CENTER,
                colors=[
                    ft.Colors.with_opacity(0.3,ft.Colors.GREY_600),
                    ft.Colors.with_opacity(0.3,ft.Colors.GREY),
                    ft.Colors.with_opacity(0.3,ft.Colors.GREY_600),
                    ft.Colors.with_opacity(0.3,ft.Colors.GREY),
                    ft.Colors.with_opacity(0.3,ft.Colors.GREY_600),
                    ft.Colors.with_opacity(0.3,ft.Colors.GREY),
                    ft.Colors.with_opacity(0.3,ft.Colors.GREY_600),
                    ft.Colors.with_opacity(0.3,ft.Colors.GREY),
                    ft.Colors.with_opacity(0.3,ft.Colors.GREY_600),
                    ft.Colors.with_opacity(0.3,ft.Colors.GREY),
                    ft.Colors.with_opacity(0.3,ft.Colors.GREY_600),
                ],
            )
            powerup_tab = ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Stack(
                        controls=[
                            ft.ShaderMask(
                                content=ft.Container(
                                    width=728,
                                    height=876,
                                    alignment=ft.Alignment.CENTER,
                                    bgcolor=ft.Colors.GREY,
                                    content=[]
                                ),
                                blend_mode=ft.BlendMode.SRC_IN,
                                shader=color_gradient,
                            ),
                            ft.Column(
                                width=728,
                                height=876,
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Button("工事中", height=48)
                                ]
                            )
                        ]
                    ),
                ]
            )
        finally:
            # ローディングオーバーレイを非表示（例外が起きても必ず閉じる）
            try:
                self.loading_overlay.visible = False
                self.page.update()
            except Exception:
                pass
        return powerup_tab