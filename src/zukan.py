import flet as ft
import asyncio
from bs4 import BeautifulSoup

from utils.utils import do_api, rankid_to_rank, create_card_image_data
from utils.db import get_all_cards, update_favorite
from utils.ui import create_card_image

PAGE_PER_CARDS = 30

class Zukan:
    def __init__(self, page):
        """初期化"""
        self.page = page
        # ローディングオーバーレイの参照を保持
        # page.overlay[0] はガチャ用、図鑑は後ろに追加しているため index 1 を使う
        self.loading_overlay = page.overlay[1]
    def get_all_target_count(self):
        """総数を取得する(APIコール)"""
        url = "https://ja.wikipedia.org/wiki/Special:Statistics"
        response = do_api(self.page.debug, url)
        soup = BeautifulSoup(response.text, "html.parser")
        # コンテンツページ数の部分を探す（class名で特定）
        stats = soup.find("table", class_="mw-statistics-table")
        if stats:
            rows = stats.find_all("tr")
            for row in rows:
                cells = row.find_all(["th", "td"])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True)
                    if "コンテンツページ数" in label or "記事" in label:
                        count_text = cells[1].get_text(strip=True)
                        count = int(''.join(filter(str.isdigit, count_text)))
                        return count
        else:
            return -1
    def open_card_image(self, data, on_fav_changed=None):
        """カードイメージ表示"""
        self.close_button = ft.TextButton("Close", on_click=lambda e: self.page.pop_dialog())
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("カードイメージ"),
            content=ft.Container(
                width=320,
                height=480,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True,
                    controls=[
                        create_card_image(data, True, True, on_fav_changed),
                    ],
                ),
                bgcolor=ft.Colors.GREY_100, border_radius=5,
                padding=ft.Padding.all(5),
            ),
            actions=[self.close_button],
            actions_alignment=ft.MainAxisAlignment.END,
            title_padding=ft.Padding.all(10),
        )
        self.page.show_dialog(self.dialog)
    async def create(self):
        """画面作成"""
        def _build_zukan_list(page):
            """図鑑リスト作成"""
            table.controls.clear()
            # ヘッダを作成
            header = ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4,
                controls=[
                    ft.Text("ID".ljust(8, " "), font_family="Consolas"),
                    ft.Text("Page ID".ljust(8, " "), font_family="Consolas"),
                    ft.Text("RANK".ljust(4, " "), font_family="Consolas"),
                    ft.Container(
                        width=370,
                        content=ft.Text("カード名"),
                    ),
                    ft.Text("HP".ljust(5, " "), font_family="Consolas"),
                    ft.Text("ATK".ljust(5, " "), font_family="Consolas"),
                    ft.Text("DEF".ljust(5, " "), font_family="Consolas"),
                    ft.Container(
                        width=14,
                        content=ft.Text("★"),
                    )
                ],
            )
            table.controls.append(header)
            table.controls.append(
                ft.Divider(
                    color=ft.Colors.GREY,
                    height=1,
                )
            )
            if total_items == 0:
                #対象データがない場合即終了
                return
            start = (page - 1) * PAGE_PER_CARDS
            end = min(start + PAGE_PER_CARDS, total_items)
            for idx in range(start, end):
                row_data = filtered_data[idx]
                # ランクを先に計算
                row_data_for_image = create_card_image_data(row_data)
                rank = rankid_to_rank(row_data[5], row_data[7])
                rank_origin = rankid_to_rank(row_data[15], row_data[7])
                num_text = str(row_data[0]).ljust(8, " ")
                pageid_text = str(row_data[1]).ljust(8, " ")
                rank_text = str(rank).ljust(4, " ")
                if rank == rank_origin:
                    nameText = row_data[2] if row_data[2] is not None else ""
                else:
                    nameText = "🔨"+row_data[2] if row_data[2] is not None else ""
                if row_data[9] == "-1":
                    hp_text = "-".ljust(5, " ") if row_data[9] is not None else "".ljust(5, " ")
                else:
                    hp_text = str(row_data[9]).ljust(5, " ") if row_data[9] is not None else "".ljust(5, " ")
                if row_data[10] == "-1":
                    atk_text = "-".ljust(5, " ") if row_data[10] is not None else "".ljust(5, " ")
                else:
                    atk_text = str(row_data[10]).ljust(5, " ") if row_data[10] is not None else "".ljust(5, " ")
                if row_data[11] == "-1":
                    def_text = "-".ljust(5, " ") if row_data[11] is not None else "".ljust(5, " ")
                else:
                    def_text = str(row_data[11]).ljust(5, " ") if row_data[11] is not None else "".ljust(5, " ")
                table.controls.append(
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=4,
                        controls=[
                            ft.Text(num_text, font_family="Consolas"),
                            ft.Text(pageid_text, font_family="Consolas"),
                            ft.Text(rank_text, font_family="Consolas"),
                            ft.Container(
                                width=370,
                                content=ft.GestureDetector(
                                    mouse_cursor=ft.MouseCursor.CLICK,
                                    on_tap=(lambda e, r=row_data_for_image: self.open_card_image(r, _toggle_favorite)),
                                    content=ft.Text(
                                        nameText,
                                        tooltip=nameText,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                        no_wrap=True,
                                        style=ft.TextStyle(
                                            color=ft.Colors.BLUE,
                                            decoration=ft.TextDecoration.UNDERLINE,
                                        ),
                                    ),
                                ),
                            ),
                            ft.Text(hp_text, font_family="Consolas"),
                            ft.Text(atk_text, font_family="Consolas"),
                            ft.Text(def_text, font_family="Consolas"),
                            ft.Container(
                                width=14,
                                content=ft.GestureDetector(
                                    mouse_cursor=ft.MouseCursor.CLICK,
                                    on_tap=(lambda e, rid=row_data[0], fav=row_data[12]: _toggle_favorite(rid, fav)),
                                    content=ft.Text("★") if row_data[12]==1 else ft.Text("☆"),
                                ),
                            )
                        ],
                    )
                )
                #区切り(10件ごとに濃く)
                if idx % 10 == 9:
                    table.controls.append(
                        ft.Divider(
                            color=ft.Colors.GREY,
                            height=1,
                        )
                    )
                else:
                    table.controls.append(
                        ft.Divider(
                            color=ft.Colors.GREY_300,
                            height=1,
                        )
                    )
        def _refresh_page_label():
            """ページラベルの更新"""
            # page_input を現在ページに合わせて更新
            try:
                page_input.value = str(current_page)
                page_input.update()
                page_info.value = f"/ {total_pages} ({total_items})"
                page_info.update()
            except Exception:
                pass
        def _on_prev(e):
            """ページ操作(前)"""
            nonlocal current_page
            if current_page > 1:
                current_page -= 1
                _build_zukan_list(current_page)
                _refresh_page_label()
                self.page.update()
        def _on_next(e):
            """ページ操作(後ろ)"""
            nonlocal current_page
            if current_page < total_pages:
                current_page += 1
                _build_zukan_list(current_page)
                _refresh_page_label()
                self.page.update()
        def _jump_to_page(e):
            """ページジャンプ"""
            nonlocal current_page
            # e.control は TextField
            v = str(e.control.value).strip()
            try:
                n = int(v)
            except Exception:
                e.control.value = str(current_page)
                e.control.update()
                return
            if n < 1 or n > total_pages:
                e.control.value = str(current_page)
                e.control.update()
                return
            current_page = n
            _build_zukan_list(current_page)
            _refresh_page_label()
            self.page.update()
        def _apply_filters():
            """フィルタ適用"""
            filtered = []
            for row in data:
                r = rankid_to_rank(row[5], row[7])
                if r in selected_ranks:
                    try:
                        if favorites_only and int(row[12]) != 1:
                            continue
                    except Exception:
                        pass
                    filtered.append(row)
            return filtered
        def _name_sort_key(name):
            """ソートの順序定義"""
            if not name:
                return (3, "")
            first = name[0]
            # category: symbol/punct=0, digit=1, ascii alpha=2, others=3
            if first.isdigit():
                cat = 1
            elif ('A' <= first <= 'Z') or ('a' <= first <= 'z'):
                cat = 2
            elif ord(first) < 128 and not first.isalnum():
                cat = 0
            else:
                cat = 3
            return (cat, name)
        def _apply_sort():
            """ソート適用"""
            nonlocal filtered_data
            key = None
            if sort_field == "id":
                key = lambda r: int(r[0]) if str(r[0]).isdigit() else 0
            elif sort_field == "pageid":
                key = lambda r: int(r[1]) if str(r[1]).isdigit() else 0
            elif sort_field == "rank":
                key = lambda r: rank_order.index(rankid_to_rank(r[5], r[7])) if rankid_to_rank(r[5], r[7]) in rank_order else 0
            elif sort_field == "name":
                key = lambda r: _name_sort_key(r[2] or "")
            elif sort_field == "HP":
                key = lambda r: int(r[9]) if str(r[9]).lstrip("-+").isdigit() else (-999999 if r[9] == "-1" else 0)
            elif sort_field == "ATK":
                key = lambda r: int(r[10]) if str(r[10]).lstrip("-+").isdigit() else (-999999 if r[10] == "-1" else 0)
            elif sort_field == "DEF":
                key = lambda r: int(r[11]) if str(r[11]).lstrip("-+").isdigit() else (-999999 if r[11] == "-1" else 0)
            elif sort_field == "favorite":
                key = lambda r: int(r[12]) if str(r[12]).isdigit() else 0
            try:
                filtered_data = sorted(filtered_data, key=key, reverse=(not sort_ascending))
            except Exception:
                pass
        def _on_dropdown_select(e):
            """ドロップダウン選択"""
            nonlocal sort_field
            sort_field = e.control.value
            _apply_sort()
            _build_zukan_list(current_page)
            _refresh_page_label()
            self.page.update()
        def _on_radio_change(e):
            """ラジオボタン切り替え"""
            nonlocal sort_ascending
            sort_ascending = (e.control.value == "asc")
            _apply_sort()
            _build_zukan_list(current_page)
            _refresh_page_label()
            self.page.update()
        def _make_filter_checkbox(rk):
            """フィルタ用チェックボックス作成（素材→C→... の順）"""
            def __on_change(e):
                nonlocal filtered_data, total_items, total_pages, current_page
                if e.control.value:
                    selected_ranks.add(rk)
                else:
                    selected_ranks.discard(rk)
                filtered_data = _apply_filters()
                total_items = len(filtered_data)
                total_pages = (total_items + PAGE_PER_CARDS - 1) // PAGE_PER_CARDS if total_items > 0 else 1
                if current_page > total_pages:
                    current_page = 1
                _build_zukan_list(current_page)
                _refresh_page_label()
                _apply_search()
                self.page.update()
            # 表示用のラベル（素材は見やすくする）
            display_label = "素材" if rk == "--" else rk
            cb = ft.Checkbox(
                label=display_label, 
                label_position=ft.LabelPosition.RIGHT, 
                scale=ft.Scale(scale_x=0.85, scale_y=0.85),
                value=True
            )
            cb.on_change = __on_change
            return cb
        def _filter_all_select():
            """すべて選択にする"""
            nonlocal filtered_data, total_items, total_pages, current_page, selected_ranks
            selected_ranks = set(rank_order)
            # 各チェックボックスを更新（filter_controls にはチェックボックスとボタンが混在）
            for ctrl in filter_controls:
                try:
                    if isinstance(ctrl, ft.Checkbox):
                        ctrl.value = True
                        ctrl.update()
                except Exception:
                    pass
            # フィルタ反映・ページ再計算
            filtered_data = _apply_filters()
            total_items = len(filtered_data)
            total_pages = (total_items + PAGE_PER_CARDS - 1) // PAGE_PER_CARDS if total_items > 0 else 1
            current_page = 1
            _build_zukan_list(current_page)
            _refresh_page_label()
            _apply_search()
            self.page.update()
        def _filter_all_unselect():
            """すべて解除にする"""
            nonlocal filtered_data, total_items, total_pages, current_page, selected_ranks
            selected_ranks = set()
            for ctrl in filter_controls:
                try:
                    if isinstance(ctrl, ft.Checkbox):
                        ctrl.value = False
                        ctrl.update()
                except Exception:
                    pass
            filtered_data = _apply_filters()
            total_items = len(filtered_data)
            total_pages = (total_items + PAGE_PER_CARDS - 1) // PAGE_PER_CARDS if total_items > 0 else 1
            if current_page > total_pages:
                current_page = 1
            _build_zukan_list(current_page)
            _refresh_page_label()
            _apply_search()
            self.page.update()
        def _apply_search():
            """検索適用"""
            nonlocal filtered_data, total_items, total_pages, current_page
            q = ""
            try:
                q = str(search_field.value).strip()
            except Exception:
                q = ""
            # ベースはランクフィルタを通したデータ
            base = _apply_filters()
            if q == "":
                filtered_data = base
            else:
                qlow = q.lower()
                results = []
                for row in base:
                    title = (row[2] or "")
                    matched = False
                    # タイトル部分一致（大文字小文字無視）
                    if qlow in title.lower():
                        matched = True
                    if matched:
                        results.append(row)
                filtered_data = results
            # ソート・ページ再計算
            _apply_sort()
            total_items = len(filtered_data)
            total_pages = (total_items + PAGE_PER_CARDS - 1) // PAGE_PER_CARDS if total_items > 0 else 1
            if current_page > total_pages:
                current_page = 1
            _build_zukan_list(current_page)
            _refresh_page_label()
            self.page.update()
        def _toggle_favorite(card_id, current_fav, external_update=False):
            """お気に入り切替ハンドラ（DB更新して再読み込み）"""
            nonlocal data, filtered_data, total_items, total_pages, current_page
            # external_update=True の場合は既に DB が更新済みなので再更新しない
            if external_update:
                try:
                    new_val = int(current_fav)
                except Exception:
                    new_val = 1
            else:
                try:
                    new_val = 0 if int(current_fav) == 1 else 1
                except Exception:
                    new_val = 1
                try:
                    update_favorite(card_id, new_val)
                except Exception:
                    pass
            try:
                data = get_all_cards()
                filtered_data = _apply_filters()
                _apply_sort()
                total_items = len(filtered_data)
                total_pages = (total_items + PAGE_PER_CARDS - 1) // PAGE_PER_CARDS if total_items > 0 else 1
                if current_page > total_pages:
                    current_page = 1
                _build_zukan_list(current_page)
                _refresh_page_label()
                self.page.update()
            except Exception:
                pass
        def _on_fav_change(e):
            """お気に入りの登録を切り替えたときの裏処理"""
            nonlocal filtered_data, total_items, total_pages, current_page, favorites_only
            favorites_only = e.control.value
            filtered_data = _apply_filters()
            total_items = len(filtered_data)
            total_pages = (total_items + PAGE_PER_CARDS - 1) // PAGE_PER_CARDS if total_items > 0 else 1
            if current_page > total_pages:
                current_page = 1
            _build_zukan_list(current_page)
            _refresh_page_label()
            _apply_search()
            self.page.update()
        ####################
        # 処理開始
        ####################
        # ローディングオーバーレイを表示
        self.loading_overlay.visible = True
        self.page.update()
        try:
            # 総記事数はブロッキングなのでバックグラウンドで取得
            try:
                count = await asyncio.to_thread(self.get_all_target_count)
            except Exception as e:
                print(e)
                count = -1
            # DBからデータを持ってくる
            data = get_all_cards()
            # フィルタ設定（初期は全選択）
            rank_order = ["--", "C", "UC", "R", "SR", "SSR", "UR", "LR"]
            selected_ranks = set(rank_order)
            # お気に入りのみ表示フラグ
            favorites_only = False
            filtered_data = _apply_filters()
            # 図鑑本体を作っておく
            table = ft.ListView(
                expand=True,
                spacing=0,
                controls=[],
            )
            # ページネーション設定（filtered_data に基づく）
            total_items = len(filtered_data)
            total_pages = (total_items + PAGE_PER_CARDS - 1) // PAGE_PER_CARDS if total_items > 0 else 1
            current_page = 1
            # ページ入力（現在ページを入力してジャンプできる）
            page_info = ft.Text(f"/ {total_pages} ({total_items})")
            page_input = ft.TextField(
                value=str(current_page), 
                label="No.",
                label_style=ft.TextStyle(
                    size=12,
                ),
                border_color=ft.Colors.GREY,
                min_lines=1, 
                max_lines=1, 
                height=24,
                width=80,
                margin=0,
                text_size=13,
                text_align=ft.TextAlign.CENTER,
                text_vertical_align=ft.VerticalAlignment.CENTER,
                content_padding=ft.Padding.all(0),
            )
            page_input.on_submit = _jump_to_page
            # ソート設定
            sort_field = "id"  # default: 入手順(ID順)
            sort_ascending = True
            # 初期ソートとページを構築
            _apply_sort()
            _build_zukan_list(current_page)
            # ソートUI: ドロップダウン + ラジオ（昇順/降順）
            dropdown = ft.Dropdown(
                width=160,
                border_color=ft.Colors.GREY,
                value="id",
                label="ソート",
                options=[
                    ft.DropdownOption(key="id", text="入手順(ID順)"),
                    ft.DropdownOption(key="pageid", text="PageID順"),
                    ft.DropdownOption(key="rank", text="ランク順"),
                    ft.DropdownOption(key="name", text="名前順"),
                    ft.DropdownOption(key="HP", text="HP順"),
                    ft.DropdownOption(key="ATK", text="ATK順"),
                    ft.DropdownOption(key="DEF", text="DEF順"),
                    ft.DropdownOption(key="favorite", text="お気に入り順"),
                ],
                editable=False,
            )
            dropdown.on_select = _on_dropdown_select
            radio_group = ft.RadioGroup(
                content=ft.Column(
                    spacing=0,
                    controls=[
                        ft.Radio(label="昇順", value="asc"), 
                        ft.Radio(label="降順", value="desc")
                    ]
                ),
                value="asc",
            )
            radio_group.on_change = _on_radio_change
            filter_controls = [_make_filter_checkbox(r) for r in rank_order]
            filter_controls.append(
                ft.TextButton(
                    content=ft.Text("全選択"),
                    on_click=_filter_all_select
                )
            )
            filter_controls.append(
                ft.TextButton(
                    content=ft.Text("全解除"),
                    on_click=_filter_all_unselect
                )
            )
            # お気に入りのみ表示チェックボックス
            favorite_only_cb = ft.Checkbox(
                label="★のみ",
                label_position=ft.LabelPosition.RIGHT,
                value=False,
                scale=ft.Scale(scale_x=0.85, scale_y=0.85),
            )
            favorite_only_cb.on_change = _on_fav_change
            filter_box = ft.Container(
                border=ft.Border.all(width=1, color=ft.Colors.GREY),
                border_radius=8,
                content=ft.Column(
                    spacing=0,
                    controls=[
                        ft.Text("  フィルタ", size=10),
                        ft.Row(controls=filter_controls[0:6],  spacing=1),
                        ft.Row(controls=filter_controls[6:10], spacing=1),
                        ft.Container(expand=True, height=1, width=360,bgcolor=ft.Colors.GREY_300, margin=ft.Margin.only(top=1, bottom=1)),
                        ft.Row(controls=[favorite_only_cb], spacing=1),
                    ],
                ),
            )
            # 検索UI
            search_field = ft.TextField(
                value="",
                label="カード名検索",
                label_style=ft.TextStyle(
                    size=14,
                ),
                border_color=ft.Colors.GREY,
                min_lines=1, 
                max_lines=1, 
                height=36,
                text_size=13,
                suffix_icon=ft.IconButton(
                    icon=ft.Icons.BACKSPACE,
                    scale=ft.Scale(scale=0.75),
                    opacity=0.5,
                    on_click=lambda e: {setattr(search_field, "value", ""), _apply_search()}
                ),
                expand=True,
            )
            search_field.on_submit = _apply_search
            search_ui = ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    search_field,
                ],
            )
            # 図鑑タブ全体
            zukan_tab = ft.Column(
                controls=[
                    ft.Stack(
                        controls=[
                            ft.ShaderMask(
                                content=ft.Container(
                                    border=ft.Border.all(0),
                                    width=738,
                                    height=876,
                                    alignment=ft.Alignment.CENTER,
                                    bgcolor=ft.Colors.ON_PRIMARY,
                                    content=None
                                ),
                                blend_mode=ft.BlendMode.SRC_IN,
                                shader=ft.RadialGradient(
                                    center=ft.Alignment.CENTER,
                                    radius=0.5,
                                    colors=[ft.Colors.ON_PRIMARY, ft.Colors.PRIMARY_CONTAINER, ft.Colors.ON_PRIMARY],
                                    stops=[0.2, 0.8, 1.0],
                                    tile_mode=ft.GradientTileMode.REPEATED,
                                ),
                            ),
                            ft.Column(
                                controls=[
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        controls=[ft.Text(f"Wikipedia 日本語版 取得対象総記事数：{count}")],
                                    ),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        spacing=0,
                                        controls=[
                                            ft.Column(
                                                spacing=0,
                                                controls=[
                                                    ft.Row(         #ソート
                                                        spacing=4,
                                                        margin=4,
                                                        controls=[
                                                            dropdown,
                                                            radio_group,
                                                        ],
                                                    ),
                                                    ft.Row(         #ページ送り
                                                        spacing=4,
                                                        alignment=ft.MainAxisAlignment.CENTER,
                                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                                        controls=[
                                                            ft.IconButton(
                                                                icon=ft.Icons.ARROW_BACK, 
                                                                scale=ft.Scale(scale_x=0.8, scale_y=0.8), 
                                                                on_click=_on_prev
                                                            ),
                                                            page_input,
                                                            page_info,
                                                            ft.IconButton(
                                                                icon=ft.Icons.ARROW_FORWARD, 
                                                                scale=ft.Scale(scale_x=0.8, scale_y=0.8), 
                                                                on_click=_on_next
                                                            ),
                                                            ft.Container(
                                                                width=20,
                                                            ),
                                                        ],
                                                    ),
                                                ],
                                            ),
                                            filter_box,             #フィルタ
                                        ],
                                    ),
                                    search_ui,                      #検索ボックス
                                    table,                          #図鑑本体
                                ],
                            ),
                        ],
                    ),
                ],
            )
        finally:
            # ローディングオーバーレイを非表示（例外が起きても必ず閉じる）
            try:
                self.loading_overlay.visible = False
                self.page.update()
            except Exception:
                pass
        return zukan_tab