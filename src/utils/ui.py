import flet as ft
import webbrowser

from utils.db import update_favorite

# ランクからカードの色を決める
def get_card_color(rank, isSozai):
    if isSozai:
        color = ft.Colors.ORANGE
    else:
        if rank == "LR":
            color = ft.Colors.PURPLE
        elif rank == "UR":
            color = ft.Colors.YELLOW
        elif rank == "SSR":
            color = ft.Colors.RED
        elif rank == "SR":
            color = ft.Colors.LIGHT_BLUE
        elif rank == "R":
            color = ft.Colors.LIGHT_GREEN
        elif rank == "UC":
            color = ft.Colors.GREY
        else: #C
            color = ft.Colors.LIME_900
    return color
# カードイメージの作成
def create_card_image(data, isShow, on_fav_changed=None):
    def _on_fav_click(e):
        # 一時的に無効化して多重クリックを防ぐ
        try:
            fav_icon.disabled = True
            fav_icon.update()
        except Exception:
            pass
        # 切り替え値を決定
        try:
            curr = int(data.get("favorite", 0))
        except Exception:
            curr = 0
        new_val = 0 if curr == 1 else 1
        try:
            update_favorite(data.get("id"), new_val)
            # ローカルデータを更新してアイコンを切替
            data["favorite"] = new_val
            fav_icon.icon = ft.Icons.STAR if new_val == 1 else ft.Icons.STAR_BORDER
            try:
                fav_icon.update()
            except Exception:
                pass
            # 親に変更通知（図鑑など）
            if callable(on_fav_changed):
                try:
                    # external_update=True を伝える（DB は既に更新済み）
                    on_fav_changed(data.get("id"), new_val, True)
                except Exception:
                    pass
            else:
                pass
        except Exception:
            pass
        finally:
            try:
                fav_icon.disabled = False
                fav_icon.update()
            except Exception:
                pass
    # ランクとカードタイトル
    link_text = ft.GestureDetector(
        mouse_cursor=ft.MouseCursor.CLICK,
        on_tap=lambda e:webbrowser.open(data["pageUrl"]),
        content=ft.Text(
            data["title"],
            tooltip=data["title"],
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
            no_wrap=True,
            style=ft.TextStyle(
                color=ft.Colors.BLUE,
                decoration=ft.TextDecoration.UNDERLINE,
            ),
        ),
    )
    if data["isSozai"] == 1:
        title = ft.Row(
            spacing=0,
            controls=[
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    width=40,
                    bgcolor=ft.Colors.GREY_200,
                    content=ft.Text("--"),
                ),
                ft.Container(
                    width=270,
                    bgcolor=ft.Colors.YELLOW,
                    content=link_text,
                ),
            ],
        )
    else:
        if data["rank"] == "SSR" or data["rank"] == "UR" or data["rank"] == "LR":
            title = ft.Row(
                spacing=0,
                controls=[
                    ft.Container(
                        alignment=ft.Alignment.CENTER,
                        width=40,
                        bgcolor=ft.Colors.GREY_200,
                        content=ft.Text(f"{data['rank']}", weight=ft.FontWeight.BOLD),
                    ),
                    ft.Container(
                        width=270,
                        bgcolor=ft.Colors.YELLOW,
                        content=link_text,
                    ),
                ]
            )
        else:
            title = ft.Row(
                spacing=0,
                controls=[
                    ft.Container(
                        alignment=ft.Alignment.CENTER,
                        width=40,
                        bgcolor=ft.Colors.GREY_200,
                        content=ft.Text(f"{data['rank']}"),
                    ),
                    ft.Container(
                        width=270,
                        bgcolor=ft.Colors.YELLOW,
                        content=link_text,
                    ),
                ]
            )
    # 画像
    if data["imageUrl"] != "":
        image = ft.Stack(
            alignment=ft.Alignment.CENTER,
            controls=[
                ft.Container(
                    width=310,
                    height=310,
                    bgcolor=get_card_color(data["rank"], data["isSozai"]),
                    alignment=ft.Alignment.CENTER,
                    content=ft.Container(
                        width=300,
                        height=300,
                        bgcolor=ft.Colors.WHITE
                    )
                ),
                ft.Image(
                    src=data["imageUrl"],
                    width=300,
                    height=300,
                    fit=ft.BoxFit.CONTAIN,
                ),
            ],
        )
    else:
        image = ft.Container(
            width=310,
            height=310,
            bgcolor=get_card_color(data["rank"], data["isSozai"]),
            alignment=ft.Alignment.CENTER,
            content=ft.Container(
                width=300,
                height=300,
                bgcolor=ft.Colors.WHITE,
                content=ft.Text("NO IMAGE",size=30),
                alignment=ft.Alignment.CENTER,
            )
        )
    # 安全なクリックハンドラを作成（連打時の不整合を防ぐ）
    fav_icon = ft.IconButton(
        icon=ft.Icons.STAR if data.get("favorite") == 1 else ft.Icons.STAR_BORDER,
        scale=ft.Scale(scale=0.75),
    )
    fav_icon.on_click = _on_fav_click
    image_stack = ft.Stack(
        controls=[
            image,
            ft.Container(
                alignment=ft.Alignment.TOP_RIGHT,
                content=fav_icon,
            )
        ]
    )
    #ステータス
    if data["isSozai"]:
        statuses = ft.Column(
            controls=[
                ft.Text(f"HP : -    ",size=24, font_family="Consolas"),
                ft.Text(f"ATK: -    ",size=24, font_family="Consolas"),
                ft.Text(f"DEF: -    ",size=24, font_family="Consolas"),
            ],
        )
    else:
        statuses = ft.Column(
            controls=[
                ft.Text(f"HP : {data["HP"]}".ljust(10," "),  size=24,font_family="Consolas"),
                ft.Text(f"ATK: {data["ATK"]}".ljust(10," "), size=24,font_family="Consolas"),
                ft.Text(f"DEF: {data["DEF"]}".ljust(10," "), size=24,font_family="Consolas"),
            ],
        )
    view = ft.Container(
        alignment=ft.Alignment.CENTER,
        visible=isShow,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.START,
            controls=[
                title,
                image_stack,
                ft.Row(
                    controls=[
                        statuses,               # ステータス
                        ft.Container(           # 概要
                            expand=True,
                            content=ft.Text(
                                data["extract"],
                                tooltip=data["extract"],
                                max_lines=5,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ),
                    ],
                ),
            ],
        ),
    )
    return view