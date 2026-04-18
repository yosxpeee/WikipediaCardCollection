import flet as ft
import asyncio
from utils.manage_settings import get_dark_theme, get_volume, change_volume, toggle_dark_theme, load_settings, save_settings

BGM_MAPPING = [
    "bgm_gacha",
    "bgm_zukan",
    "bgm_mockbattle",
    "bgm_mockbattle_fight",
    "bgm_powerup",
    "bgm_sortie",
    "bgm_sortie_fight",
    "bgm_sortie_reward",
]

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
        def _create_textfield():
            """BGM変更用のテキストフィールド"""
            textfield = []
            for a in range(8):
                tf = ft.TextField(
                    value="",
                    height=24,
                    width=440,
                    content_padding=ft.Padding.all(0),
                    text_size=12,
                    text_vertical_align=ft.VerticalAlignment.START,
                    text_align=ft.TextAlign.RIGHT,
                    max_lines=1,
                    min_lines=1,
                    read_only=True,
                    border_color=ft.Colors.GREY,
                )
                textfield.append(tf)
            return textfield
        def _reset_value(num):
            """BGMを初期値に戻す（settings.json へ反映）"""
            bgm_textfields[num].value = ""
            try:
                settings = load_settings()
                if 0 <= num < len(BGM_MAPPING):
                    settings[BGM_MAPPING[num]] = ""
                    save_settings(settings)
            except Exception:
                pass
        async def _change_bgm_file(idx: int):
            """指定BGMに変更する（mp3のみ許可） - 非同期で FilePicker を呼ぶ"""
            try:
                files = await ft.FilePicker().pick_files(
                    file_type=ft.FilePickerFileType.CUSTOM,
                    allowed_extensions=["mp3"],
                    allow_multiple=False,
                )
            except Exception:
                files = None
            if not files:
                return
            f = files[0]
            path = getattr(f, 'path', None) or getattr(f, 'name', '')
            try:
                bgm_textfields[idx].value = path
                bgm_textfields[idx].update()
                # 選択を settings.json に保存
                try:
                    settings = load_settings()
                    if 0 <= idx < len(BGM_MAPPING):
                        settings[BGM_MAPPING[idx]] = path
                        save_settings(settings)
                except Exception:
                    pass
            except Exception:
                pass
        bgm_textfields = _create_textfield()
        # 初期値を settings.json から読み出してフィールドに反映
        try:
            settings = load_settings()
            for i, key in enumerate(BGM_MAPPING):
                try:
                    bgm_textfields[i].value = settings.get(key, "")
                except Exception:
                    pass
        except Exception:
            pass
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
                ft.Row(
                    controls=[
                        ft.Text("音量", size=16, weight=ft.FontWeight.BOLD),
                        ft.Slider(value=get_volume(), on_change_end=lambda e:{change_volume(e.control.value)}),
                    ]
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                spacing=2,
                                controls=[
                                    ft.Container(
                                        width=120,
                                        content=ft.Text("ガチャ"),
                                    ),
                                    bgm_textfields[0],
                                    ft.OutlinedButton(
                                        content="リセット",
                                        on_click=lambda x:_reset_value(0),
                                    ),
                                    ft.OutlinedButton(
                                        content="変更",
                                        on_click=lambda e, n=0: asyncio.create_task(_change_bgm_file(n)),
                                    ),
                                ],
                            ),
                            ft.Row(
                                spacing=2,
                                controls=[
                                    ft.Container(
                                        width=120,
                                        content=ft.Text("図鑑"),
                                    ),
                                    bgm_textfields[1],
                                    ft.OutlinedButton(
                                        content="リセット",
                                        on_click=lambda x:_reset_value(1),
                                    ),
                                    ft.OutlinedButton(
                                        content="変更",
                                        on_click=lambda e, n=1: asyncio.create_task(_change_bgm_file(n)),
                                    ),
                                ],
                            ),
                            ft.Row(
                                spacing=2,
                                controls=[
                                    ft.Container(
                                        width=120,
                                        content=ft.Text("模擬戦"),
                                    ),
                                    bgm_textfields[2],
                                    ft.OutlinedButton(
                                        content="リセット",
                                        on_click=lambda x:_reset_value(2),
                                    ),
                                    ft.OutlinedButton(
                                        content="変更",
                                        on_click=lambda e, n=2: asyncio.create_task(_change_bgm_file(n)),
                                    ),
                                ],
                            ),
                            ft.Row(
                                spacing=2,
                                controls=[
                                    ft.Container(
                                        width=120,
                                        content=ft.Text("模擬戦(戦闘中)"),
                                    ),
                                    bgm_textfields[3],
                                    ft.OutlinedButton(
                                        content="リセット",
                                        on_click=lambda x:_reset_value(3),
                                    ),
                                    ft.OutlinedButton(
                                        content="変更",
                                        on_click=lambda e, n=3: asyncio.create_task(_change_bgm_file(n)),
                                    ),
                                ],
                            ),
                            ft.Row(
                                spacing=2,
                                controls=[
                                    ft.Container(
                                        width=120,
                                        content=ft.Text("強化"),
                                    ),
                                    bgm_textfields[4],
                                    ft.OutlinedButton(
                                        content="リセット",
                                        on_click=lambda x:_reset_value(4),
                                    ),
                                    ft.OutlinedButton(
                                        content="変更",
                                        on_click=lambda e, n=4: asyncio.create_task(_change_bgm_file(n)),
                                    ),
                                ],
                            ),
                            ft.Row(
                                spacing=2,
                                controls=[
                                    ft.Container(
                                        width=120,
                                        content=ft.Text("出撃"),
                                    ),
                                    bgm_textfields[5],
                                    ft.OutlinedButton(
                                        content="リセット",
                                        on_click=lambda x:_reset_value(5),
                                    ),
                                    ft.OutlinedButton(
                                        content="変更",
                                        on_click=lambda e, n=5: asyncio.create_task(_change_bgm_file(n)),
                                    ),
                                ],
                            ),
                            ft.Row(
                                spacing=2,
                                controls=[
                                    ft.Container(
                                        width=120,
                                        content=ft.Text("出撃(戦闘中)"),
                                    ),
                                    bgm_textfields[6],
                                    ft.OutlinedButton(
                                        content="リセット",
                                        on_click=lambda x:_reset_value(6),
                                    ),
                                    ft.OutlinedButton(
                                        content="変更",
                                        on_click=lambda e, n=6: asyncio.create_task(_change_bgm_file(n)),
                                    ),
                                ],
                            ),
                            ft.Row(
                                spacing=2,
                                controls=[
                                    ft.Container(
                                        width=120,
                                        content=ft.Text("出撃(報酬獲得)"),
                                    ),
                                    bgm_textfields[7],
                                    ft.OutlinedButton(
                                        content="リセット",
                                        on_click=lambda x:_reset_value(7),
                                    ),
                                    ft.OutlinedButton(
                                        content="変更",
                                        on_click=lambda e, n=7: asyncio.create_task(_change_bgm_file(n)),
                                    ),
                                ],
                            ),
                        ],
                    ),
                ),
            ],
        )
        return setting_container