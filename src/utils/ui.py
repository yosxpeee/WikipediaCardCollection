import flet as ft
import webbrowser

# ランクからカードの色を決める
def getCardColor(rank, isSozai):
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
def createCardImage(data, isShow):
    # ランクとカードタイトル
    linkText =  ft.GestureDetector(
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
    if data["isSozai"]:
        title = ft.Row(
            controls=[
                ft.Text("--"),
                ft.Container(width=300, content=linkText),
            ]
        )
    else:
        if data["rank"] == "SSR" or data["rank"] == "UR" or data["rank"] == "LR":
            title = ft.Row(
                controls=[
                    ft.Text(f"{data['rank']}",weight=ft.FontWeight.BOLD),
                    ft.Container(width=300, content=linkText),
                ]
            )
        else:
            title = ft.Row(
                controls=[
                    ft.Text(f"{data['rank']}"),
                    ft.Container(width=300, content=linkText),
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
                    bgcolor=getCardColor(data["rank"], data["isSozai"]),
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
            bgcolor=getCardColor(data["rank"], data["isSozai"]),
            alignment=ft.Alignment.CENTER,
            content=ft.Container(
                width=300,
                height=300,
                bgcolor=ft.Colors.WHITE,
                content=ft.Text("NO IMAGE",size=30),
                alignment=ft.Alignment.CENTER,
            )
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
                image,
                ft.Row(
                    controls=[
                        # ステータス
                        statuses,
                        # 概要
                        ft.Container(
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