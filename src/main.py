import flet as ft

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
            # 図鑑タブの内容を更新
            zukan = Zukan()
            tab_bar_view = e.control.content.controls[1]
            tab_bar_view.controls[1] = ft.Container(
                content=zukan.create(),
                alignment=ft.Alignment.CENTER,
            )
            tab_bar_view.update()

    # ページの設定
    page.window.width=768
    page.window.height=1024

    # ガチャタブの中身のクラス生成
    gacha = Gacha()

    # DBがない場合初期作成する
    
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