import flet as ft
import webbrowser

from utils.db import update_favorite

# ランクからカードの色を決める
def get_card_color(rank, isSozai):
    if isSozai == 1:
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
        color_gradient = ft.LinearGradient(
            begin=ft.Alignment.CENTER_LEFT,
            end=ft.Alignment.CENTER_RIGHT,
            colors=[
                ft.Colors.RED,
                ft.Colors.ORANGE,
                ft.Colors.YELLOW,
                ft.Colors.GREEN,
                ft.Colors.BLUE,
                ft.Colors.INDIGO,
                ft.Colors.PURPLE,
            ],
        )
        if data["rank"] == "LR":
            rank_text = ft.ShaderMask(
                content=ft.Text(
                    f"{data['rank']}", 
                    size=14,
                    weight=ft.FontWeight.BOLD, 
                    italic=True
                ),
                blend_mode=ft.BlendMode.SRC_IN,
                shader=color_gradient,
            )
        elif data["rank"] == "SSR" or data["rank"] == "UR":
            color_gradient = ft.LinearGradient(
                begin=ft.Alignment.CENTER_LEFT,
                end=ft.Alignment.CENTER_RIGHT,
                colors=[
                    ft.Colors.GREY,
                    ft.Colors.LIGHT_BLUE,
                    ft.Colors.GREY,
                ],
            )
            rank_text = ft.ShaderMask(
                content=ft.Text(
                    f"{data['rank']}", 
                    size=14,
                    weight=ft.FontWeight.BOLD, 
                ),
                blend_mode=ft.BlendMode.SRC_IN,
                shader=color_gradient,
            )
        elif data["rank"] == "R" or data["rank"] == "SR":
            rank_text = ft.Text(
                f"{data['rank']}", 
                weight=ft.FontWeight.BOLD
            )
        else:
            rank_text = ft.Text(
                f"{data['rank']}"
            )
        title = ft.Row(
            spacing=0,
            controls=[
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    width=40,
                    bgcolor=ft.Colors.GREY_200,
                    content=rank_text,
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
                        bgcolor=ft.Colors.WHITE,
                        content=ft.Image(
                            src=data["imageUrl"],
                            width=300,
                            height=300,
                            fit=ft.BoxFit.CONTAIN,
                        ),
                        alignment=ft.Alignment.CENTER,
                    )
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
        bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.WHITE),
    )
    fav_icon.on_click = _on_fav_click
    # 強化済みアイコン
    if data["rank"] != data["resourceRANK"]:
        uppered = ft.Container(
            ft.Text("🔨"),
            margin=5,
            bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.WHITE),
            shape=ft.BoxShape.CIRCLE,
            tooltip=f"強化前のランク: {data["resourceRANK"]}"
        )
    else:
        uppered = ft.Text("")
    image_stack = ft.Stack(
        width=310,
        height=310,
        margin=0,
        alignment=ft.Alignment.CENTER,
        controls=[
            image,
            ft.Column(
                width=310,
                height=310,
                spacing=0,
                controls=[
                    ft.Container(
                        width=310,
                        height=40,
                        alignment=ft.Alignment.TOP_RIGHT,
                        content=fav_icon,
                    ),
                    ft.Container(
                        width=310,
                        height=240,
                    ),
                    ft.Container(
                        width=310,
                        height=30,
                        alignment=ft.Alignment.BOTTOM_LEFT,
                        content=uppered,
                    ),
                ]
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
    #カードのベース色
    if data["rank"] == "LR":
        base_gradient = ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=[
                ft.Colors.with_opacity(0.2, ft.Colors.RED),
                ft.Colors.with_opacity(0.2, ft.Colors.ORANGE),
                ft.Colors.with_opacity(0.2, ft.Colors.YELLOW),
                ft.Colors.with_opacity(0.2, ft.Colors.GREEN),
                ft.Colors.with_opacity(0.2, ft.Colors.BLUE),
                ft.Colors.with_opacity(0.2, ft.Colors.INDIGO),
                ft.Colors.with_opacity(0.2, ft.Colors.PURPLE),
            ],
        )
    elif data["rank"] == "SSR" or data["rank"] == "UR":
        base_gradient = ft.LinearGradient(
            begin=ft.Alignment.TOP_RIGHT,
            end=ft.Alignment.BOTTOM_LEFT,
            colors=[
                ft.Colors.with_opacity(0.2, ft.Colors.GREY),
                ft.Colors.with_opacity(0.2, ft.Colors.GREEN),
                ft.Colors.with_opacity(0.2, ft.Colors.LIGHT_BLUE),
                ft.Colors.with_opacity(0.2, ft.Colors.GREEN),
                ft.Colors.with_opacity(0.2, ft.Colors.GREY),
            ],
        )
    else:
        base_gradient = ft.LinearGradient(
            begin=ft.Alignment.TOP_CENTER,
            end=ft.Alignment.BOTTOM_CENTER,
            colors=[
                ft.Colors.with_opacity(0.75, ft.Colors.GREY_100),
                ft.Colors.with_opacity(0.75, ft.Colors.GREY_300),
                ft.Colors.with_opacity(0.75, ft.Colors.GREY_600),
                ft.Colors.with_opacity(0.75, ft.Colors.GREY_300),
                ft.Colors.with_opacity(0.75, ft.Colors.GREY_100),
            ],
        )
    # 外側の Stack 自体を isShow で切り替えて、非表示要素でも ShaderMask が描画されないようにする
    view = ft.Stack(
        visible=isShow,
        controls=[
            ft.ShaderMask(
                content=ft.Container(
                    width=310,
                    height=470,
                    bgcolor=ft.Colors.WHITE,
                ),
                blend_mode=ft.BlendMode.SRC_IN,
                shader=base_gradient,
            ),
            ft.Container(
                alignment=ft.Alignment.CENTER,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        title,                          # カード名
                        image_stack,                    # 画像関連
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
            ),
        ],
    )
    return view