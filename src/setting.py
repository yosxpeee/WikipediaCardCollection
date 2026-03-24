import flet as ft
from utils.manage_settings import get_dark_theme, toggle_dark_theme

class Setting:
    def __init__(self, page):
        """初期化"""
        self.page = page
    def apply_theme_change(self):
        """テーマ切り替え"""
        dark_theme_enabled = get_dark_theme()
        if dark_theme_enabled:
            self.page.theme_mode = ft.ThemeMode.DARK
        else:
            self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.update()
    def create(self):
        """画面作成"""
        setting_container=ft.Column(
            expand=True,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Text("アプリ設定", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=1),
                ft.Row(
                    controls=[
                        ft.Text("テーマ", size=16, weight=ft.FontWeight.BOLD),
                        ft.Switch(
                            label=ft.Text("ダークモード"),
                            value=get_dark_theme(),
                            on_change=lambda e: {toggle_dark_theme(e.control.value), self.apply_theme_change()},
                        ),
                    ],
                ),
            ],
        )
        return setting_container