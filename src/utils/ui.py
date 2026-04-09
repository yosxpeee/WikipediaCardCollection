import flet as ft
import webbrowser

from utils.db import update_favorite
from utils.utils import rankid_to_rank

def get_card_color(rank, isSozai):
    """ランクからカードの色を決める"""
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

def create_rank_text(rank):
    if rank == "LR":
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
        rank_text = ft.ShaderMask(
            content=ft.Text(
                f"{rank}", 
                size=14,
                weight=ft.FontWeight.BOLD, 
                italic=True
            ),
            blend_mode=ft.BlendMode.SRC_IN,
            shader=color_gradient,
        )
    elif rank == "SSR" or rank == "UR":
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
                f"{rank}", 
                size=14,
                weight=ft.FontWeight.BOLD, 
            ),
            blend_mode=ft.BlendMode.SRC_IN,
            shader=color_gradient,
        )
    elif rank == "R" or rank == "SR":
        rank_text = ft.Text(
            f"{rank}",
            color=ft.Colors.BLACK,
            weight=ft.FontWeight.BOLD
        )
    else:
        rank_text = ft.Text(
            f"{rank}",
            color=ft.Colors.BLACK,
        )
    return ft.Container(
        alignment=ft.Alignment.CENTER,
        width=40,
        bgcolor=ft.Colors.GREY_200,
        content=rank_text,
    )

def create_ranked_tabs(ranks, all_cards_by_rank, on_select_callback=None):
    """ランク別のタブ付きカード選択リストを作成して返す。

    Args:
        ranks: ランクのリスト（例: ["LR","UR",...]
        all_cards_by_rank: dict mapping rank->rows (DB行リスト)
        on_select_callback: 呼ばれるコールバック (cid, name, rank...)

    Returns:
        ft.Tabs オブジェクト
    """
    tab_views = []
    # 全タブで共有する現在選択中のカードID（タブ横断で1つだけハイライト）
    selected_cid = {"val": None}
    # 各タブの refresh 関数を保持して、選択変更時に全タブを再描画する
    refresh_funcs = []
    for rk in ranks:
        lv = ft.ListView(
            expand=True,
            spacing=0,
            auto_scroll=False,
            controls=[],
        )
        # ページング用の状態（1ページあたり28件）
        page = {"idx": 0}
        PAGE_SIZE = 28
        # 各タブ内の選択コンテナをローカルに管理（表示中の行のみ）
        target_containers = []
        sort_dd = ft.Dropdown(
            margin=ft.Margin.all(0),
            border_color=ft.Colors.GREY,
            value="id",
            options=[
                ft.DropdownOption(key="id", text="ID順"),
                ft.DropdownOption(key="name", text="名前順"),
                ft.DropdownOption(key="HP", text="HP順"),
                ft.DropdownOption(key="ATK", text="ATK順"),
                ft.DropdownOption(key="DEF", text="DEF順"),
            ],
            editable=False,
        )
        sort_rg = ft.RadioGroup(
            content=ft.Column(
                spacing=0,
                scale=ft.Scale(scale=0.75),
                controls=[ft.Radio(label="昇順", value="asc"), ft.Radio(label="降順", value="desc")],
            ),
            value="asc",
        )
        search_tf = ft.TextField(
            value="",
            label="カード名検索",
            label_style=ft.TextStyle(size=14),
            border_color=ft.Colors.GREY,
            min_lines=1,
            max_lines=1,
            height=36,
            text_size=13,
            suffix_icon=ft.IconButton(icon=ft.Icons.BACKSPACE, scale=ft.Scale(scale=0.75), opacity=0.5,),
            expand=True,
        )
        def build_row_cont(row):
            cid = row[0]
            name = row[2] or ""
            hp = row[9] if row[9] is not None else "-"
            atk = row[10] if row[10] is not None else "-"
            deff = row[11] if row[11] is not None else "-"
            rank = rankid_to_rank(row[5], row[7])
            img = row[4]
            cont = ft.Container(
                padding=ft.Padding(top=0, left=6, right=6, bottom=0),
                bgcolor=None,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(str(cid).ljust(8, " "), font_family="Consolas"),
                        ft.Container(width=10),
                        ft.Text(name, expand=True, tooltip=f"[{rank}] {name}", no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Container(width=10),
                        ft.Text(str(hp).ljust(5, " "), font_family="Consolas"),
                        ft.Text(str(atk).ljust(5, " "), font_family="Consolas"),
                        ft.Text(str(deff).ljust(5, " "), font_family="Consolas"),
                    ],
                ),
            )
            def _on_target_click(e, cid=cid, name=name, rk=rk, cont=cont):
                # グローバル選択IDを更新して全タブの一覧を再描画する
                selected_cid["val"] = cid
                for f in refresh_funcs:
                    try:
                        f()
                    except Exception:
                        pass
                if callable(on_select_callback):
                    try:
                        on_select_callback(cid, name, rank, hp, atk, deff, img)
                    except Exception:
                        pass
            cont.on_click = _on_target_click
            # もしこの行が現在選択されているカードならハイライトしておく
            try:
                if selected_cid.get("val") == cid:
                    cont.bgcolor = ft.Colors.YELLOW_100
                    try:
                        cont.content.controls[0].color = ft.Colors.BLACK
                        cont.content.controls[2].color = ft.Colors.BLACK
                        cont.content.controls[4].color = ft.Colors.BLACK
                        cont.content.controls[5].color = ft.Colors.BLACK
                        cont.content.controls[6].color = ft.Colors.BLACK
                    except Exception:
                        pass
            except Exception:
                pass
            return cont
        # ページング用 UI を作る
        page_label = ft.Text("1/1")
        prev_btn = ft.IconButton(icon=ft.Icons.ARROW_BACK)
        next_btn = ft.IconButton(icon=ft.Icons.ARROW_FORWARD)
        def refresh_lv(e=None, rk=rk, lv=lv, sort_dd=sort_dd, sort_rg=sort_rg, search_tf=search_tf, page=page, page_label=page_label, prev_btn=prev_btn, next_btn=next_btn):
            rows = all_cards_by_rank.get(rk, [])
            q = (search_tf.value or "").strip().lower()
            key = sort_dd.value or "id"
            order_desc = (sort_rg.value == "desc")
            filtered = []
            for row in rows:
                name = (row[2] or "").lower()
                if q == "" or q in name:
                    filtered.append(row)
            def keyfunc(r):
                try:
                    if key == "id":
                        return int(r[0])
                    if key == "name":
                        return (r[2] or "").lower()
                    if key == "HP":
                        return int(r[9]) if r[9] is not None and str(r[9]).isdigit() else -1
                    if key == "ATK":
                        return int(r[10]) if r[10] is not None and str(r[10]).isdigit() else -1
                    if key == "DEF":
                        return int(r[11]) if r[11] is not None and str(r[11]).isdigit() else -1
                except Exception:
                    return 0
                return 0
            filtered.sort(key=keyfunc, reverse=order_desc)
            # ページ計算
            total = len(filtered)
            total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE if total > 0 else 1
            if page["idx"] < 0:
                page["idx"] = 0
            if page["idx"] >= total_pages:
                page["idx"] = total_pages - 1
            start = page["idx"] * PAGE_SIZE
            end_idx = start + PAGE_SIZE
            display_rows = filtered[start:end_idx]
            lv.controls.clear()
            # 表示前に可視コンテナの参照をリセット
            target_containers.clear()
            for row in display_rows:
                cont = build_row_cont(row)
                lv.controls.append(cont)
                target_containers.append(cont)
            if len(lv.controls) == 0:
                lv.controls.append(ft.Container(padding=ft.Padding.all(8), content=ft.Text("対象が見つかりません")))
            # ページ表示更新
            page_label.value = f"{page['idx']+1}/{total_pages}"
            try:
                page_label.update()
                prev_btn.disabled = (page["idx"] == 0)
                next_btn.disabled = (page["idx"] >= total_pages - 1)
                prev_btn.update()
                next_btn.update()
                lv.update()
            except Exception:
                pass
        # このタブの refresh 関数をグローバル配列に追加
        refresh_funcs.append(refresh_lv)
        sort_ui = ft.Row(spacing=4, alignment=ft.MainAxisAlignment.CENTER, controls=[sort_dd, sort_rg, search_tf])
        # ページ切替 UI
        pagination_row = ft.Row(
            margin=ft.Margin.all(0),
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                prev_btn,
                ft.Container(expand=True),
                page_label,
                ft.Container(expand=True),
                next_btn,
            ],
        )
        header = ft.Container(
            padding=ft.Padding.all(6),
            bgcolor=None,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text("ID".ljust(8, " "), font_family="Consolas"),
                    ft.Container(width=10),
                    ft.Text("カード名", expand=True, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Container(width=10),
                    ft.Text("HP".ljust(5, " "), font_family="Consolas"),
                    ft.Text("ATK".ljust(5, " "), font_family="Consolas"),
                    ft.Text("DEF".ljust(5, " "), font_family="Consolas"),
                ],
            ),
        )
        tab_views.append(
            ft.Container(
                alignment=ft.Alignment.CENTER,
                content=ft.Column(
                    spacing=1, 
                    margin=ft.Margin.all(0),
                    controls=[
                        sort_ui, 
                        pagination_row, 
                        ft.Divider(height=1), 
                        header, 
                        ft.Divider(height=1), 
                        lv
                    ],
                ),
            ),
        )
        sort_dd.on_select = refresh_lv
        sort_rg.on_change = refresh_lv
        search_tf.on_submit = refresh_lv
        # ページ操作ハンドラ
        def _on_prev(e, page=page, ref=refresh_lv):
            if page["idx"] > 0:
                page["idx"] -= 1
                ref()
        def _on_next(e, page=page, ref=refresh_lv, total_rows_getter=lambda rk=rk: len([r for r in all_cards_by_rank.get(rk, []) if (search_tf.value or "").strip().lower() in ((r[2] or "").lower()) or (search_tf.value or "").strip()==""])):
            # next は refresh 内で上限チェックが入るのでインクリメントして更新
            page["idx"] += 1
            ref()
        prev_btn.on_click = _on_prev
        next_btn.on_click = _on_next
        def _on_search_clear(e, tf=search_tf, ref=refresh_lv):
            try:
                tf.value = ""
                ref()
                tf.update()
            except Exception:
                pass
        if hasattr(search_tf, 'suffix_icon') and search_tf.suffix_icon is not None:
            try:
                search_tf.suffix_icon.on_click = _on_search_clear
            except Exception:
                pass
        refresh_lv()
    tabs = ft.Tabs(
        selected_index=0,
        length=len(ranks),
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[ft.TabBar(tab_alignment=ft.TabAlignment.CENTER, tabs=[ft.Tab(label=r) for r in ranks]), ft.TabBarView(expand=True, controls=tab_views)],
        ),
    )
    return tabs

def create_card_image(data, isShow, isFbButton, on_fav_changed=None):
    """カードイメージの作成"""
    def _on_fav_click(e):
        """お気に入りボタンクリックの処理"""
        # 一時的に無効化して多重クリックを防ぐ
        fav_icon.disabled = True
        fav_icon.update()
        # 切り替え値を決定
        curr = int(data.get("favorite", 0))
        new_val = 0 if curr == 1 else 1
        update_favorite(data.get("id"), new_val)
        # ローカルデータを更新してアイコンを切替
        data["favorite"] = new_val
        fav_icon.icon = ft.Icons.STAR if new_val == 1 else ft.Icons.STAR_BORDER
        fav_icon.update()
        # 親に変更通知（図鑑など）
        if callable(on_fav_changed):
            # external_update=True を伝える（DB は既に更新済み）
            on_fav_changed(data.get("id"), new_val, True)
        fav_icon.disabled = False
        fav_icon.update()
    # ランクとカードタイトル
    if data["pageUrl"] == "":
        link_text = ft.Text(
            data["title"],
            tooltip=data["title"],
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
            no_wrap=True,
            style=ft.TextStyle(
                color=ft.Colors.BLUE,
                decoration=ft.TextDecoration.UNDERLINE,
            ),
        )
    else:
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
        title = ft.Row(
            spacing=0,
            controls=[
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    width=40,
                    bgcolor=ft.Colors.GREY_200,
                    content=create_rank_text(data['rank']),
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
        icon_color=ft.Colors.BLACK,
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
                        content=fav_icon if isFbButton == True else None,
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
                ft.Text(f"HP : -    ",size=24, font_family="Consolas",color=ft.Colors.BLACK ),
                ft.Text(f"ATK: -    ",size=24, font_family="Consolas",color=ft.Colors.BLACK ),
                ft.Text(f"DEF: -    ",size=24, font_family="Consolas",color=ft.Colors.BLACK ),
            ],
        )
    else:
        statuses = ft.Column(
            controls=[
                ft.Text(f"HP : {data["HP"]}".ljust(10," "),  size=24,font_family="Consolas",color=ft.Colors.BLACK ),
                ft.Text(f"ATK: {data["ATK"]}".ljust(10," "), size=24,font_family="Consolas",color=ft.Colors.BLACK ),
                ft.Text(f"DEF: {data["DEF"]}".ljust(10," "), size=24,font_family="Consolas",color=ft.Colors.BLACK ),
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
                                        color=ft.Colors.BLACK,
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

def create_sortie_formation_image(data, isEnemy):
    """出撃タブ：編成用カードイメージ作成"""
    card_image = None
    if data["image"] == "" or data["image"] == None:
        #画像あり
        card_image = ft.Container(
            alignment=ft.Alignment.CENTER,
            border=ft.Border.all(2, color=get_card_color(data["rank"], 0)),
            bgcolor=ft.Colors.WHITE if isEnemy == False else ft.Colors.GREY,
            width=74,
            height=74,
            content=ft.Text("NO IMAGE"),
        )
    else:
        #画像なし
        card_image = ft.Container(
            alignment=ft.Alignment.CENTER,
            border=ft.Border.all(2, color=get_card_color(data["rank"], 0)),
            bgcolor=ft.Colors.WHITE if isEnemy == False else ft.Colors.GREY,
            width=74,
            height=74,
            content=ft.Image(
                width=100,
                height=74,
                src=data["image"],
                fit=ft.BoxFit.CONTAIN,
            ),
        )
    if isEnemy:
        #対戦相手側
        status_row = [
            card_image,
            ft.Container(
                height=10,
                expand=True,
            ),
            ft.Column(
                spacing=0,
                controls=[
                    ft.Text(f"HP : {data["HP"]}".ljust(10),font_family="Consolas", size=16),
                    ft.Text(f"ATK: {data["ATK"]}".ljust(10),font_family="Consolas", size=16),
                    ft.Text(f"DEF: {data["DEF"]}".ljust(10),font_family="Consolas", size=16),
                ]
            )
        ]
    else:
        #プレイヤー側
        status_row = [
            ft.Column(
                spacing=0,
                controls=[
                    ft.Text(f"HP : {data["HP"]}".ljust(10),font_family="Consolas", size=16),
                    ft.Text(f"ATK: {data["ATK"]}".ljust(10),font_family="Consolas", size=16),
                    ft.Text(f"DEF: {data["DEF"]}".ljust(10),font_family="Consolas", size=16),
                ],
            ),
            ft.Container(
                height=10,
                expand=True,
            ),
            card_image
        ]
    view = ft.Column(
        spacing=0,
        controls=[
            ft.Row(
                spacing=0,
                controls=[
                    ft.Container(
                        width=40,
                        alignment=ft.Alignment.CENTER,
                        content=create_rank_text(data['rank']),
                    ),
                    ft.Container(
                        width=5,
                    ),
                    ft.Container(
                        width=160,
                        alignment=ft.Alignment.TOP_LEFT,
                        content=ft.Text(data["title"],no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ),
                ],
            ),
            ft.Divider(height=1, color=ft.Colors.GREY),
            ft.Row(
                margin=ft.Margin.all(2),
                alignment=ft.MainAxisAlignment.END,
                controls=status_row,
            ),
        ]
    )
    return view

def create_reward_items_carousel(items):
    """戦闘報酬のカルーセル表示"""
    def carousel_event(type):
        """ページ送りイベント"""
        nonlocal current_visible
        if type == "back":
            if current_visible == start:
                return
            current_visible -= 1
        else: #forward
            if current_visible == end-1:
                return
            current_visible += 1
        for num in range(end):
            if num == current_visible:
                view.controls[0].content.value = f"<<< {current_visible+1}/{end} >>>"
                view.controls[1].controls[num].visible = True
            else:
                view.controls[0].content.value = f"<<< {current_visible+1}/{end} >>>"
                view.controls[1].controls[num].visible = False
        view.update()
    start = 0
    end = len(items)
    current_visible = 0
    view = ft.Column(
        tight=True,
        controls=[
            ft.Container(
                width=320,
                alignment=ft.Alignment.CENTER,
                content=ft.Text(f"<<< {start+1}/{end} >>>",weight=ft.FontWeight.BOLD)
            ),
            ft.Stack(
                controls=[],
            ),
        ],
    )
    for num in range(end):
        if num == start:
            items[num].visible = True
        else:
            items[num].visible = False
        view.controls[1].controls.append(items[num])
    view.controls[1].controls.append(
        ft.Row(
            width=320,
            height=480,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=ft.Colors.LIGHT_BLUE,
                    bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.GREY),
                    on_click=lambda x:carousel_event("back"),
                ),
                ft.Container(
                    expand=True
                ),
                ft.IconButton(
                    icon=ft.Icons.ARROW_FORWARD,
                    icon_color=ft.Colors.LIGHT_BLUE,
                    bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.GREY),
                    on_click=lambda x:carousel_event("forward"),
                ),
            ],
        )
    )
    return view