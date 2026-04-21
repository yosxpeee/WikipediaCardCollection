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
            # 表示順を種別→ID昇順にソート
            type_order = {"ガチャ": 0, "図鑑":1, "出撃": 2, "強化": 3}
            achievements_data.sort(key=lambda a: (type_order.get(a[1], 99), a[0]))
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
                    shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.GREY if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.WHITE),
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
            def _apply_filters(e=None):
                """フィルターを適用する"""
                selected = [cb.label for cb in checkboxes if cb.value]
                filtered = [a for a in self._achievements_data if a[1] in selected]
                # 表示順を再保証（種別→ID）
                filtered.sort(key=lambda a: (type_order.get(a[1], 99), a[0]))
                grid.controls = [_build_achievement_card(a) for a in filtered]
                try:
                    self.page.update()
                except Exception:
                    pass
            # 全ての実績カード元データを保持
            self._achievements_data = achievements_data
            # フィルタ用チェックボックスを作成し、変更時に表示を更新する
            grid = ft.GridView(
                scroll=ft.ScrollMode.AUTO,
                expand=True,
                padding=ft.Padding.all(15),
                runs_count=3,     # 3列指定
                spacing=15,       # カード間の間隔
                run_spacing=15,   # 行間の間隔
                controls=[],
            )
            cb_gacha = ft.Checkbox(label="ガチャ", value=True)
            cb_zukan = ft.Checkbox(label="図鑑", value=True)
            cb_sortie = ft.Checkbox(label="出撃", value=True)
            cb_strength = ft.Checkbox(label="強化", value=True)
            checkboxes = [cb_gacha, cb_zukan, cb_sortie, cb_strength]
            for cb in checkboxes:
                cb.on_change = _apply_filters
            # 初期表示（全表示）
            _apply_filters()
            achievements_view = ft.Column(
                spacing=0,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("🏆 実績一覧 🏆", size=28, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            cb_gacha,
                            cb_zukan,
                            cb_sortie,
                            cb_strength,
                        ]
                    ),
                    ft.Text("※ガチャの実績は出撃の報酬獲得では達成されません。",size=14),
                    ft.Divider(color=ft.Colors.GREY),
                    grid,
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