import flet as ft
import asyncio
from zukan.zukan import Zukan
from gacha.gacha import Gacha

def main(page: ft.Page):
    # event: タブ切り替え
    def changeTabs(e):
        #print(e)
        # ガチャのタブに切り替えたとき
        if e.control.selected_index == 0:
            # 図鑑タブの中身をクリアしておく
            tab_bar_view = e.control.content.controls[1]
            tab_bar_view.controls[1] = ft.Container(
                content=[],
                alignment=ft.Alignment.CENTER,
            )
            tab_bar_view.update()
        # 図鑑タブに切り替えたとき
        if e.control.selected_index == 1:
            # 図鑑タブの内容を非同期で読み込む
            zukan = Zukan(page)
            tab_bar_view = e.control.content.controls[1]
            # 一旦プレースホルダを入れてから非同期で差し替え
            tab_bar_view.controls[1] = ft.Container(
                content=ft.Text("読み込み中...", size=18),
                alignment=ft.Alignment.CENTER,
            )
            tab_bar_view.update()

            async def load_and_set():
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
                        ft.Text(str(ex))
                    ])
                    tab_bar_view.update()

            asyncio.create_task(load_and_set())

    # ページの設定
    page.window.width=768
    page.window.height=1024
    page.window.resizable = False
    # ローディングオーバーレイ
    loading_overlay = ft.Container(
        visible=False,
        expand=True,
        bgcolor=ft.Colors.with_opacity(0.88, ft.Colors.BLACK),
        alignment=ft.Alignment.CENTER,
        content=ft.Column([
                ft.Text("結果を取得中…", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.ProgressRing(width=80, height=80, stroke_width=7, color=ft.Colors.CYAN_400),
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            alignment=ft.MainAxisAlignment.CENTER, spacing=24
        ),
    )
    page.overlay.append(loading_overlay)
    # ガチャタブの中身のクラス生成
    gacha = Gacha(page)
    # DBがない場合初期作成する(TBD)
    
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
                                content=[], #初期状態は空
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
    page.window.visible = True
    page.update()

if __name__ == "__main__":
    ft.run(main, view=ft.AppView.FLET_APP_HIDDEN)
    #ft.run(main, view=ft.AppView.WEB_BROWSER)