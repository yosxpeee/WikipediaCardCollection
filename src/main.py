import flet as ft
import asyncio

from zukan import Zukan
from gacha import Gacha
from utils.db import initializeDB

async def main(page: ft.Page):
    # event: タブ切り替え
    def changeTabs(e):
        async def loadAndSet():
            try:
                content = await zukan.create()
                tabBarView.controls[1] = ft.Container(
                    content=content,
                    alignment=ft.Alignment.CENTER,
                )
                tabBarView.update()
            except Exception as ex:
                tabBarView.controls[1] = ft.Column([
                    ft.Text("読み込みに失敗しました。"),
                    ft.Text(str(ex))
                ])
                tabBarView.update()
        # ガチャのタブに切り替えたとき
        if e.control.selected_index == 0:
            # 図鑑タブの中身をクリアしておく
            tabBarView = e.control.content.controls[1]
            tabBarView.controls[1] = ft.Container(
                content=None,
                alignment=ft.Alignment.CENTER,
            )
            tabBarView.update()
        # 図鑑タブに切り替えたとき
        if e.control.selected_index == 1:
            tabBarView = e.control.content.controls[1]
            if tabBarView.controls[1].content == None:
                # 図鑑タブの内容を非同期で読み込む
                zukan = Zukan(page)
                # 一旦プレースホルダを入れてから非同期で差し替え
                tabBarView.controls[1] = ft.Container(
                    content=ft.Text("読み込み中...", size=18),
                    alignment=ft.Alignment.CENTER,
                )
                tabBarView.update()
                asyncio.create_task(loadAndSet())
    ####################
    # 処理開始
    ####################
    # ページの設定
    page.window.width = 768
    page.window.height = 1024
    page.window.resizable = False
    page.window.maximizable = False
    page.window.visible = True
    page.title = "Wikipedia Card Collection"
    #page.theme_mode = ft.ThemeMode.DARK
    page.update()
    # ガチャ用ローディングオーバーレイ（進捗バー＋カウンタ）
    gacha_overlayCounter = ft.Text("0/0", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    gacha_overlay_progress = ft.ProgressBar(width=300, height=12, value=0)
    gacha_overlay = ft.Container(
        visible=False,
        expand=True,
        bgcolor=ft.Colors.with_opacity(0.88, ft.Colors.BLACK),
        alignment=ft.Alignment.CENTER,
        content=ft.Column([
                gacha_overlayCounter,
                gacha_overlay_progress,
                ft.ProgressRing(width=80, height=80, stroke_width=7, color=ft.Colors.CYAN_400),
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            alignment=ft.MainAxisAlignment.CENTER, spacing=12
        ),
    )
    page.overlay.append(gacha_overlay)
    # 図鑑用ローディングオーバーレイ（従来のもの）
    zukan_overlay = ft.Container(
        visible=False,
        expand=True,
        bgcolor=ft.Colors.with_opacity(0.88, ft.Colors.BLACK),
        alignment=ft.Alignment.CENTER,
        content=ft.Column([
                ft.Text("データを取得中…", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.ProgressRing(width=80, height=80, stroke_width=7, color=ft.Colors.CYAN_400),
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            alignment=ft.MainAxisAlignment.CENTER, spacing=24
        ),
    )
    page.overlay.append(zukan_overlay)
    # ガチャタブの中身のクラス生成
    gacha = Gacha(page)
    # DBがない場合初期作成する
    initializeDB()
    # ページに要素追加
    page.controls.append(
        ft.Tabs(
            selected_index=0,
            length=3,
            expand=True,
            on_change=changeTabs,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tab_alignment=ft.TabAlignment.CENTER,
                        tabs=[
                            ft.Tab(label="ガチャ", icon=ft.Icons.SHOPPING_BAG),
                            ft.Tab(label="図鑑", icon=ft.Icons.ARTICLE),
                            ft.Tab(label="バトル", icon=ft.Icons.SHIELD),
                        ],
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            ft.Container(
                                content=gacha.create(),
                                alignment=ft.Alignment.CENTER,
                            ),
                            ft.Container(
                                content=None, #初期状態は空
                                alignment=ft.Alignment.CENTER,
                            ),
                            ft.Container(
                                content=ft.Text("未実装"),
                                alignment=ft.Alignment.CENTER,
                            ),
                        ],
                    ),
                ],
            ),
        )
    )
    # 念のためここでも更新を掛ける
    page.update()
if __name__ == "__main__":
    ft.run(main, view=ft.AppView.FLET_APP_HIDDEN, assets_dir="assets")
    #ft.run(main, view=ft.AppView.WEB_BROWSER)