import flet as ft
import asyncio

class Achievements:
    def __init__(self, page):
        """初期化"""
        self.page = page
        # ローディングオーバーレイの参照を保持(図鑑のものを使いまわし)
        self.loading_overlay = page.overlay[1]
    async def create(self):
        """画面作成"""
        # ローディングオーバーレイを表示
        self.loading_overlay.visible = True
        self.page.update()
        try:
            await asyncio.sleep(1)
            achievements_view = ft.Container(
                content=ft.Text("実装中")
            )
        finally:
            # ローディングオーバーレイを非表示（例外が起きても必ず閉じる）
            try:
                self.loading_overlay.visible = False
                self.page.update()
            except Exception:
                pass
        return achievements_view