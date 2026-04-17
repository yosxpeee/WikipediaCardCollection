import flet as ft
import asyncio

from zukan import Zukan
from gacha import Gacha
from powerup import PowerUp
from mockbattle import MockBattle
from sortie import Sortie
from setting import Setting

from utils.db import initialize_db
from utils.manage_settings import get_dark_theme

DEBUG_MODE = False

async def main(page: ft.Page):
    """メイン"""
    def _change_tabs(e):
        """タブの切り替え"""
        async def __load_and_set_zukan():
            """図鑑タブのロード"""
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
            tabs_widget.disabled = False
            tabs_widget.update()
            ov = page.overlay[1]
            ov.visible = False
            page.update()
        async def __load_and_set_powerup():
            """強化タブのロード"""
            try:
                content = await powerup.create()
                tab_bar_view.controls[2] = ft.Container(
                    content=content,
                    alignment=ft.Alignment.CENTER,
                )
                tab_bar_view.update()
            except Exception as ex:
                tab_bar_view.controls[2] = ft.Column([
                    ft.Text("読み込みに失敗しました。"),
                    ft.Text(str(ex)),
                ])
                tab_bar_view.update()
            tabs_widget.disabled = False
            tabs_widget.update()
            ov = page.overlay[1]
            ov.visible = False
            page.update()
        async def __load_and_set_battle():
            """模擬戦タブのロード"""
            try:
                content = await battle.create()
                tab_bar_view.controls[3] = ft.Container(
                    content=content,
                    alignment=ft.Alignment.CENTER,
                )
                tab_bar_view.update()
            except Exception as ex:
                tab_bar_view.controls[3] = ft.Column([
                    ft.Text("読み込みに失敗しました。"),
                    ft.Text(str(ex)),
                ])
                tab_bar_view.update()
            tabs_widget.disabled = False
            tabs_widget.update()
            ov = page.overlay[1]
            ov.visible = False
        async def __load_and_set_sortie():
            """出撃タブのロード"""
            try:
                content = await sortie.create()
                tab_bar_view.controls[4] = ft.Container(
                    content=content,
                    alignment=ft.Alignment.CENTER,
                )
                tab_bar_view.update()
            except Exception as ex:
                tab_bar_view.controls[4] = ft.Column([
                    ft.Text("読み込みに失敗しました。"),
                    ft.Text(str(ex)),
                ])
                tab_bar_view.update()
            tabs_widget.disabled = False
            tabs_widget.update()
            ov = page.overlay[1]
            ov.visible = False
        # コントロール取得
        nonlocal last_tab_index
        tabs_widget = e.control
        # 共通で参照する TabBarView のコンテナ参照
        tab_bar_view = e.control.content.controls[1]
        # ガチャのタブに切り替えたとき
        if e.control.selected_index == 0:
            # 図鑑・強化の中身をクリアしておく（メモリ節約）
            tab_bar_view.controls[1] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            tab_bar_view.controls[2] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            tab_bar_view.controls[3] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            tab_bar_view.controls[4] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            tab_bar_view.update()
        # 図鑑タブに切り替えたとき
        if e.control.selected_index == 1:
            # 強化、模擬戦のタブの中身をクリア（メモリ節約）
            tab_bar_view.controls[2] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            tab_bar_view.controls[3] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            tab_bar_view.controls[4] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            # オーバーレイを即表示して画面操作をブロック
            ov = page.overlay[1]
            ov.visible = True
            page.update()
            # 読み込み中はタブ切替を禁止
            tabs_widget.disabled = True
            tabs_widget.update()
            # 図鑑タブの内容を非同期で読み込む
            try:
                zukan = Zukan(page)
                tab_bar_view.controls[1] = ft.Container(
                    content=ft.Text("読み込み中...", size=18),
                    alignment=ft.Alignment.CENTER,
                )
                tab_bar_view.update()
                asyncio.create_task(__load_and_set_zukan())
            except:
                tabs_widget.disabled = False
                tabs_widget.update()
        # 強化タブに切り替えたとき
        if e.control.selected_index == 2:
            # リロードが必要なタブの中身をクリアしておく（メモリ節約）
            tab_bar_view.controls[1] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            tab_bar_view.controls[3] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            tab_bar_view.controls[4] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            # 図鑑と同じオーバーレイを表示して読み込み中に UI を覆う
            overlay = page.overlay[1]
            overlay.visible = True
            page.update()
            # 読み込み中はタブ切替を禁止
            tabs_widget.disabled = True
            tabs_widget.update()
            # 非同期で PowerUp.create() を呼んで差し替える
            try:
                powerup = PowerUp(page)
                tab_bar_view.controls[2] = ft.Container(
                    content=ft.Text("読み込み中...", size=18),
                    alignment=ft.Alignment.CENTER,
                )
                tab_bar_view.update()
                asyncio.create_task(__load_and_set_powerup())
            except Exception:
                tabs_widget.disabled = False
                tabs_widget.update()
        # 模擬戦のタブに切り替えたとき
        if e.control.selected_index == 3:
            # リロードが必要なタブの中身をクリアしておく（メモリ節約）
            tab_bar_view.controls[1] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            tab_bar_view.controls[2] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            tab_bar_view.controls[4] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            # 図鑑と同じオーバーレイを表示して読み込み中に UI を覆う
            overlay = page.overlay[1]
            overlay.visible = True
            page.update()
            # 読み込み中はタブ切替を禁止
            tabs_widget.disabled = True
            tabs_widget.update()
            # 非同期で MockBattle.create() を呼んで差し替える
            try:
                battle = MockBattle(page)
                tab_bar_view.controls[3] = ft.Container(
                    content=ft.Text("読み込み中...", size=18),
                    alignment=ft.Alignment.CENTER,
                )
                tab_bar_view.update()
                asyncio.create_task(__load_and_set_battle())
            except Exception:
                tabs_widget.disabled = False
                tabs_widget.update()
        # 出撃タブに切り替えたとき
        if e.control.selected_index == 4:
            # リロードが必要なタブの中身をクリアしておく（メモリ節約）
            tab_bar_view.controls[1] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            tab_bar_view.controls[2] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            tab_bar_view.controls[3] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            # 図鑑と同じオーバーレイを表示して読み込み中に UI を覆う
            overlay = page.overlay[1]
            overlay.visible = True
            page.update()
            # 読み込み中はタブ切替を禁止
            tabs_widget.disabled = True
            tabs_widget.update()
            # 非同期で Sortie.create() を呼んで差し替える
            try:
                sortie = Sortie(page)
                tab_bar_view.controls[4] = ft.Container(
                    content=ft.Text("読み込み中...", size=18),
                    alignment=ft.Alignment.CENTER,
                )
                tab_bar_view.update()
                asyncio.create_task(__load_and_set_sortie())
            except Exception:
                tabs_widget.disabled = False
                tabs_widget.update()
        # 設定タブに切り替えたとき
        if e.control.selected_index == 5:
            # リロードが必要なタブの中身をクリアしておく（メモリ節約）
            tab_bar_view.controls[1] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            tab_bar_view.controls[2] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            tab_bar_view.controls[3] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
            tab_bar_view.controls[4] = ft.Container(content=None, alignment=ft.Alignment.CENTER)
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
    page.window.icon = "icon.ico" 
    page.title = "Wikipedia Card Collection"
    page.debug = DEBUG_MODE
    # ダークテーマ対応：初期化
    dark_theme_enabled = get_dark_theme()
    if dark_theme_enabled:
        page.theme_mode = ft.ThemeMode.DARK
    else:
        page.theme_mode = ft.ThemeMode.LIGHT
    page.update()
    # 初期 last_tab_index を設定
    last_tab_index = 0
    # オーバーレイ [0]：ガチャ用ローディング画面（進捗バー＋カウンタ）
    gacha_overlay_counter = ft.Text("0/0", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE)
    gacha_overlay_progress = ft.ProgressBar(width=300, height=12, value=0)
    gacha_overlay_msg_text = ft.Text("進捗表示", color=ft.Colors.WHITE)
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
                        ft.Image("gacha_spin1.png", scale=ft.Scale(scale_x=0.88, scale_y=0.88), visible=True),
                        ft.Image("gacha_spin2.png", scale=ft.Scale(scale_x=0.88, scale_y=0.88), visible=True),
                        ft.Image("gacha_spin3.png", scale=ft.Scale(scale_x=0.88, scale_y=0.88), visible=True),
                        ft.Image("gacha_spin4.png", scale=ft.Scale(scale_x=0.88, scale_y=0.88), visible=True),
                        ft.Image("gacha_spin5.png", scale=ft.Scale(scale_x=0.88, scale_y=0.88), visible=True),
                    ],
                ),
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
                    alignment=ft.MainAxisAlignment.CENTER, spacing=12,
                    controls=[
                        ft.Container(width=20, height=645), #位置調整用
                        gacha_overlay_counter,
                        gacha_overlay_progress,
                        gacha_overlay_msg_text,
                    ],
                ),
            ],
        ),
    )
    page.overlay.append(gacha_overlay)
    # オーバーレイ [1]：図鑑、強化用ローディング画面
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
    # オーバーレイ [2]：強化実行エフェクト用 (予約)
    powerup_overlay_dummy = ft.Container(visible=False, content=None)
    page.overlay.append(powerup_overlay_dummy)
    # ガチャタブ、設定タブの中身のクラス生成
    gacha = Gacha(page)
    setting = Setting(page)
    # DB がない場合初期作成する
    initialize_db()
    # ページに要素追加
    page.update()
    page.controls.append(
        ft.Tabs(
            selected_index=0,
            length=6,
            expand=True,
            on_change=_change_tabs,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tab_alignment=ft.TabAlignment.CENTER,
                        tabs=[
                            ft.Tab(
                                label=ft.Column(
                                    spacing=2,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Image(
                                            "icon_gacha.svg", 
                                            color=ft.Colors.ON_SURFACE,
                                            width=24, 
                                            height=24
                                        ),
                                        ft.Text("ガチャ"),
                                    ],
                                ),
                            ),
                            ft.Tab(
                                label=ft.Column(
                                    spacing=2,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Image(
                                            "icon_zukan.svg", 
                                            color=ft.Colors.ON_SURFACE,
                                            width=24, 
                                            height=24
                                        ),
                                        ft.Text("図鑑"),
                                    ],
                                ),
                            ),
                            ft.Tab(
                                label=ft.Column(
                                    spacing=2,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Image(
                                            "icon_powerup.svg", 
                                            color=ft.Colors.ON_SURFACE,
                                            width=24, 
                                            height=24
                                        ),
                                        ft.Text("強化"),
                                    ],
                                ),
                            ),
                            ft.Tab(
                                label=ft.Column(
                                    spacing=2,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Image(
                                            "icon_battle_mock.svg", 
                                            color=ft.Colors.ON_SURFACE,
                                            width=24, 
                                            height=24
                                        ),
                                        ft.Text("模擬戦"),
                                    ],
                                ),
                            ),
                            ft.Tab(
                                label=ft.Column(
                                    spacing=2,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Image(
                                            "icon_sortie.svg", 
                                            color=ft.Colors.ON_SURFACE,
                                            width=24, 
                                            height=24
                                        ),
                                        ft.Text("出撃"),
                                    ],
                                ),
                            ),
                            ft.Tab(
                                label=ft.Column(
                                    spacing=2,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Image(
                                            "icon_settings.svg", 
                                            color=ft.Colors.ON_SURFACE,
                                            width=24, 
                                            height=24
                                        ),
                                        ft.Text("設定"),
                                    ],
                                ),
                            ),
                        ],
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            ft.Container(   # ガチャ
                                alignment=ft.Alignment.CENTER,
                                content=gacha.create(),
                            ),
                            ft.Container(   # 図鑑
                                alignment=ft.Alignment.CENTER,
                                content=None,
                            ),
                            ft.Container(   # 強化
                                alignment=ft.Alignment.CENTER,
                                content=None,
                            ),
                            ft.Container(   # 模擬戦
                                alignment=ft.Alignment.CENTER,
                                content=None,
                            ),
                            ft.Container(   # 出撃
                                alignment=ft.Alignment.CENTER,
                                content=None,
                            ),
                            ft.Container(   # 設定
                                alignment=ft.Alignment.CENTER,
                                content=setting.create(),
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