import flet as ft
import asyncio

from zukan import Zukan
from gacha import Gacha
from powerup import PowerUp

from utils.db import initialize_db

async def main(page: ft.Page):
    # 前回選択したタブ(index)を保持
    last_tab_index = 0
    # event: タブ切り替え
    def change_tabs(e):
        nonlocal last_tab_index
        tabs_widget = e.control
        async def load_and_set_zukan():
            try:
                content = await zukan.create()
                tab_bar_view.controls[1] = ft.Container(
                    content=content,
                    alignment=ft.Alignment.CENTER,
                )
                tab_bar_view.update()
            except Exception as ex:
                tab_bar_view.controls[1] = ft.Column([
                    ft.Text("読み込みに失敗しました。"),
                    ft.Text(str(ex)),
                ])
                tab_bar_view.update()
            finally:
                try:
                    tabs_widget.disabled = False
                    tabs_widget.update()
                except Exception:
                    pass
                try:
                    ov = page.overlay[1]
                    ov.visible = False
                    page.update()
                except Exception:
                    pass
        async def load_and_set_powerup():
            try:
                content = await powerup.create()
                tab_bar_view.controls[2] = ft.Container(
                    content=content,
                    alignment=ft.Alignment.CENTER,
                )
                tab_bar_view.update()
            except Exception:
                tab_bar_view.controls[2] = ft.Column([
                    ft.Text("読み込みに失敗しました。"),
                ])
                tab_bar_view.update()
            finally:
                try:
                    tabs_widget.disabled = False
                    tabs_widget.update()
                except Exception:
                    pass
                try:
                    if overlay is not None:
                        overlay.visible = False
                        page.update()
                except Exception:
                    pass
        # 共通で参照する TabBarView のコンテナ参照
        tab_bar_view = e.control.content.controls[1]
        # ガチャのタブに切り替えたとき
        if e.control.selected_index == 0:
            # 図鑑・強化の中身をクリアしておく（メモリ節約）
            try:
                tab_bar_view.controls[1] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            except Exception:
                pass
            try:
                tab_bar_view.controls[2] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            except Exception:
                pass
            tab_bar_view.update()
        # 図鑑タブに切り替えたとき
        if e.control.selected_index == 1:
            # 強化のタブの中身をクリア
            try:
                tab_bar_view.controls[2] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            except Exception:
                pass
            # オーバーレイを即表示して画面操作をブロック
            try:
                ov = page.overlay[1]
                ov.visible = True
                page.update()
            except Exception:
                ov = None
            # 読み込み中はタブ切替を禁止
            try:
                tabs_widget.disabled = True
                tabs_widget.update()
            except Exception:
                pass
            # 図鑑タブの内容を非同期で読み込む
            try:
                zukan = Zukan(page)
                tab_bar_view.controls[1] = ft.Container(
                    content=ft.Text("読み込み中...", size=18),
                    alignment=ft.Alignment.CENTER,
                )
                tab_bar_view.update()
                asyncio.create_task(load_and_set_zukan())
            except:
                try:
                    tabs_widget.disabled = False
                    tabs_widget.update()
                except Exception:
                    pass
        # 強化タブに切り替えたとき
        if e.control.selected_index == 2:
            # 図鑑の中身をクリアしておく（メモリ節約）
            try:
                tab_bar_view.controls[1] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            except Exception:
                pass
            # 図鑑と同じオーバーレイを表示して読み込み中にUIを覆う
            try:
                overlay = page.overlay[1]
                overlay.visible = True
                page.update()
            except Exception:
                overlay = None
            # 読み込み中はタブ切替を禁止
            try:
                tabs_widget.disabled = True
                tabs_widget.update()
            except Exception:
                pass
            # 非同期で PowerUp.create() を呼んで差し替える
            try:
                powerup = PowerUp(page)
                tab_bar_view.controls[2] = ft.Container(
                    content=ft.Text("読み込み中...", size=18),
                    alignment=ft.Alignment.CENTER,
                )
                tab_bar_view.update()
                asyncio.create_task(load_and_set_powerup())
            except Exception:
                try:
                    tabs_widget.disabled = False
                    tabs_widget.update()
                except Exception:
                    pass
        # バトルのタブに切り替えたとき
        if e.control.selected_index == 3:
            # 図鑑・強化の中身をクリアしておく（メモリ節約）
            try:
                tab_bar_view.controls[1] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            except Exception:
                pass
            try:
                tab_bar_view.controls[2] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            except Exception:
                pass
            tab_bar_view.update()
        # 最後に last_tab_index を更新
        last_tab_index = e.control.selected_index
    ####################
    # 処理開始
    ####################
    # ページの設定
    page.window.width = 768
    page.window.height = 1024
    page.window.max_width = 768
    page.window.max_height = 1024
    page.window.min_width = 768
    page.window.min_height = 1024
    page.window.resizable = False
    page.window.maximizable = False
    page.window.visible = True
    page.bgcolor = ft.Colors.ON_PRIMARY
    page.title = "Wikipedia Card Collection"
    #page.theme_mode = ft.ThemeMode.DARK
    page.update()
    # 初期 last_tab_index を設定
    last_tab_index = 0
    # ガチャ用ローディングオーバーレイ（進捗バー＋カウンタ）
    gacha_overlay_counter = ft.Text("0/0", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE)
    gacha_overlay_progress = ft.ProgressBar(width=300, height=12, value=0)
    gacha_overlay = ft.Container(
        visible=False,
        expand=True,
        bgcolor=ft.Colors.with_opacity(0.88, ft.Colors.BLACK),
        alignment=ft.Alignment.CENTER,
        content=ft.Stack(
            alignment=ft.Alignment.CENTER,
            controls=[
                ft.Stack(
                    alignment=ft.Alignment.CENTER,
                    controls=[
                        ft.Image("gacha_spin1.png",scale=ft.Scale(scale_x=0.88, scale_y=0.88), visible=True),
                        ft.Image("gacha_spin2.png",scale=ft.Scale(scale_x=0.88, scale_y=0.88), visible=True),
                        ft.Image("gacha_spin3.png",scale=ft.Scale(scale_x=0.88, scale_y=0.88), visible=True),
                        ft.Image("gacha_spin4.png",scale=ft.Scale(scale_x=0.88, scale_y=0.88), visible=True),
                        ft.Image("gacha_spin5.png",scale=ft.Scale(scale_x=0.88, scale_y=0.88), visible=True),
                    ]
                ),
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
                    alignment=ft.MainAxisAlignment.CENTER, spacing=12,
                    controls=[
                        ft.Container(width=20, height=585),
                        gacha_overlay_counter,
                        gacha_overlay_progress,
                    ],
                ),
            ],
        ),
    )
    page.overlay.append(gacha_overlay)
    # 図鑑用ローディングオーバーレイ（従来のもの）
    zukan_overlay = ft.Container(
        visible=False,
        expand=True,
        bgcolor=ft.Colors.with_opacity(0.88, ft.Colors.GREY),
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
    # 強化タブの中身のクラス生成
    powerup = PowerUp(page)
    # DBがない場合初期作成する
    initialize_db()
    # ページに要素追加
    page.controls.append(
        ft.Tabs(
            selected_index=0,
            length=4,
            expand=True,
            on_change=change_tabs,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tab_alignment=ft.TabAlignment.CENTER,
                        tabs=[
                            ft.Tab(label="ガチャ", icon=ft.Icons.SHOPPING_BAG),
                            ft.Tab(label="図鑑", icon=ft.Icons.ARTICLE),
                            ft.Tab(label="強化", icon=ft.Icons.ADD_MODERATOR),
                            ft.Tab(label="バトル", icon=ft.Icons.BATCH_PREDICTION),
                        ],
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            ft.Container(   #ガチャ
                                alignment=ft.Alignment.CENTER,
                                content=gacha.create(), #最初の画面かつこの画面でデータの再読み個の必要はないのでこれでよい。
                            ),
                            ft.Container(   #図鑑
                                alignment=ft.Alignment.CENTER,
                                content=None, #初期状態は空
                            ),
                            ft.Container(   #強化
                                alignment=ft.Alignment.CENTER,
                                content=None, #初期状態は空
                            ),
                            ft.Container(   #バトル
                                alignment=ft.Alignment.CENTER,
                                content=ft.Text("未実装"), #まだ未実装なので・・・
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