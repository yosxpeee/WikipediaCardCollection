import flet as ft
import asyncio
from utils.db import get_all_achievements

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
            await asyncio.sleep(0.5)
            achievements_data = await asyncio.to_thread(get_all_achievements)
            def _build_achievement_card(achievement):
                """単一の実績カードを生成するヘルパー関数"""
                # achievement: (id, type, title, description, done, date) のタプル
                _, a_type, a_title, a_desc, is_done, a_date = achievement
                status_text = "達成済み" if is_done else "未達成"
                status_color = ft.Colors.GREEN_700 if is_done else ft.Colors.RED_500
                # カードの見た目を定義
                card = ft.Container(
                    padding=ft.Padding.all(15),
                    bgcolor=ft.Colors.WHITE,
                    border_radius=8,
                    shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.BLACK_26),
                    content=ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text(a_title, size=18, color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD),
                            ft.Divider(color=ft.Colors.GREY),
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        width=50, 
                                        height=24, 
                                        bgcolor=status_color, 
                                        border_radius=4, 
                                        content=ft.Icon(
                                            ft.Icons.CHECK_CIRCLE if is_done else ft.Icons.DO_NOT_DISTURB, 
                                            scale=ft.Scale(scale=0.75),
                                            color=ft.Colors.WHITE
                                        ),
                                    ),
                                    ft.Text(status_text, color=status_color, weight=ft.FontWeight.BOLD),
                                ],
                            ),
                            ft.Text(a_desc, size=14, color=ft.Colors.BLACK_54),
                            ft.Text("種別: " + a_type, size=12, color=ft.Colors.BLACK),
                            ft.Text(f"登録日: {a_date if a_date else '----/--/--'}", size=12, color=ft.Colors.BLACK)
                        ],
                    ),
                )
                return card
            # 全ての実績カードを生成
            achievement_cards = [_build_achievement_card(a) for a in achievements_data]
            achievements_view = ft.Column(
                scroll=ft.ScrollMode.AUTO,
                spacing=0,
                controls=[
                    ft.Text("🏆 実績一覧 🏆", size=28, weight=ft.FontWeight.BOLD),
                    ft.Text("※ガチャの実績は出撃の報酬獲得では達成されません。",size=14),
                    ft.Divider(color=ft.Colors.GREY),
                    ft.GridView(
                        expand=True,
                        runs_count=3, # 3列指定
                        spacing=15, # カード間の間隔
                        run_spacing=15, # 行間の間隔
                        controls=achievement_cards,
                    )
                ]
            )
        except Exception as e:
            # エラー発生時はエラーメッセージを表示
            achievements_view = ft.Container(
                content=ft.Text(f"実績データの読み込み中にエラーが発生しました: {e}", color=ft.Colors.RED),
            )
        finally:
            # ローディングオーバーレイを非表示（例外が起きても必ず閉じる）
            try:
                self.loading_overlay.visible = False
                self.page.update()
            except Exception:
                pass
        return achievements_view