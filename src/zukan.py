import flet as ft
from bs4 import BeautifulSoup

from utils.utils import doApi, rankIdToRank
from utils.db import getAllCards
from utils.ui import createCardImage

PAGE_PER_CARDS = 30

class Zukan:
    # 初期化
    def __init__(self, page):
        self.page = page
        # ローディングオーバーレイの参照を保持
        # page.overlay[0] はガチャ用、図鑑は後ろに追加しているため index 1 を使う
        self.loading_overlay = page.overlay[1]
    # 総数を取得する
    def getAllTargetCount(self):
        url = "https://ja.wikipedia.org/wiki/Special:Statistics"
        response = doApi(url)
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
    # カードイメージ表示
    def openCardImage(self, data):
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
                        createCardImage(data, True),
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
    # 画面作成
    async def create(self):
        # 図鑑リスト作成
        def buildZukanList(page):
            table.controls.clear()
            # ヘッダを作成
            header = ft.Row(
                spacing=12,
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
                ],
            )
            table.controls.append(header)
            table.controls.append(ft.Divider(
                color=ft.Colors.BLACK,
                height=1,
            ))
            if total_items == 0:
                #table.controls.append(ft.Text("データがありません"))
                return
            start = (page - 1) * PAGE_PER_CARDS
            end = min(start + PAGE_PER_CARDS, total_items)
            for idx in range(start, end):
                row_data = filtered_data[idx]
                # ランクを先に計算
                rank = rankIdToRank(row_data[5], row_data[7])
                row_data_for_image = {
                    "pageId": row_data[1],
                    "title": row_data[2],
                    "pageUrl": row_data[3],
                    "imageUrl": row_data[4],
                    "rank": rank,
                    "quality": row_data[6],
                    "isSozai": True if row_data[7]=="1" else False,
                    "extract": row_data[8],
                    "HP": row_data[9],
                    "ATK": row_data[10],
                    "DEF": row_data[11],
                }
                num_text = str(row_data[0]).ljust(8, " ")
                pageid_text = str(row_data[1]).ljust(8, " ")
                rank_text = str(rank).ljust(4, " ")
                nameText = row_data[2] if row_data[2] is not None else ""
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
                        spacing=12,
                        controls=[
                            ft.Text(num_text, font_family="Consolas"),
                            ft.Text(pageid_text, font_family="Consolas"),
                            ft.Text(rank_text, font_family="Consolas"),
                            ft.Container(
                                width=370,
                                content=ft.GestureDetector(
                                    mouse_cursor=ft.MouseCursor.CLICK,
                                    on_tap=(lambda e, r=row_data_for_image: self.openCardImage(r)),
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
                        ],
                    )
                )
        # ページラベルの更新
        def refreshPageLabel():
            # page_input を現在ページに合わせて更新
            try:
                page_input.value = str(current_page)
                page_input.update()
                page_info.value = f"/ {total_pages} ({total_items})"
                page_info.update()
            except Exception:
                pass
        # ページ操作
        def onPrev(e):
            nonlocal current_page
            if current_page > 1:
                current_page -= 1
                buildZukanList(current_page)
                refreshPageLabel()
                self.page.update()
        def onNext(e):
            nonlocal current_page
            if current_page < total_pages:
                current_page += 1
                buildZukanList(current_page)
                refreshPageLabel()
                self.page.update()
        def jumpToPage(e):
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
            buildZukanList(current_page)
            refreshPageLabel()
            self.page.update()
        # フィルタ適用
        def apply_filters():
            filtered = []
            for row in data:
                r = rankIdToRank(row[5], row[7])
                if r in selected_ranks:
                    filtered.append(row)
            return filtered
        # ソートの順序定義
        def name_sort_key(name):
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
        # ソート適用
        def apply_sort():
            nonlocal filtered_data
            key = None
            if sort_field == "id":
                key = lambda r: int(r[0]) if str(r[0]).isdigit() else 0
            elif sort_field == "pageid":
                key = lambda r: int(r[1]) if str(r[1]).isdigit() else 0
            elif sort_field == "rank":
                key = lambda r: rank_order.index(rankIdToRank(r[5], r[7])) if rankIdToRank(r[5], r[7]) in rank_order else 0
            elif sort_field == "name":
                key = lambda r: name_sort_key(r[2] or "")
            elif sort_field == "HP":
                key = lambda r: int(r[9]) if str(r[9]).lstrip("-+").isdigit() else (-999999 if r[9] == "-1" else 0)
            elif sort_field == "ATK":
                key = lambda r: int(r[10]) if str(r[10]).lstrip("-+").isdigit() else (-999999 if r[10] == "-1" else 0)
            elif sort_field == "DEF":
                key = lambda r: int(r[11]) if str(r[11]).lstrip("-+").isdigit() else (-999999 if r[11] == "-1" else 0)
            try:
                filtered_data = sorted(filtered_data, key=key, reverse=(not sort_ascending))
            except Exception:
                pass
        # ドロップダウン選択
        def on_dropdown_select(e):
            nonlocal sort_field
            sort_field = e.control.value
            apply_sort()
            buildZukanList(current_page)
            refreshPageLabel()
            self.page.update()
        # ラジオボタン切り替え
        def on_radio_change(e):
            nonlocal sort_ascending
            sort_ascending = (e.control.value == "asc")
            apply_sort()
            buildZukanList(current_page)
            refreshPageLabel()
            self.page.update()
        # フィルタ用チェックボックス作成（素材→C→... の順）
        def makeFilterCheckbox(rk):
            # 表示用のラベル（素材は見やすくする）
            display_label = "素材" if rk == "--" else rk
            cb = ft.Checkbox(label=display_label, label_position=ft.LabelPosition.RIGHT, value=True)
            def _on_change(e):
                nonlocal filtered_data, total_items, total_pages, current_page
                if e.control.value:
                    selected_ranks.add(rk)
                else:
                    selected_ranks.discard(rk)
                filtered_data = apply_filters()
                total_items = len(filtered_data)
                total_pages = (total_items + PAGE_PER_CARDS - 1) // PAGE_PER_CARDS if total_items > 0 else 1
                if current_page > total_pages:
                    current_page = 1
                buildZukanList(current_page)
                refreshPageLabel()
                self.page.update()
            cb.on_change = _on_change
            return cb
        # すべて選択にする
        def filterAllSelect():
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
            filtered_data = apply_filters()
            total_items = len(filtered_data)
            total_pages = (total_items + PAGE_PER_CARDS - 1) // PAGE_PER_CARDS if total_items > 0 else 1
            current_page = 1
            buildZukanList(current_page)
            refreshPageLabel()
            self.page.update()
        # すべて解除にする
        def filterAllUnselect():
            nonlocal filtered_data, total_items, total_pages, current_page, selected_ranks
            selected_ranks = set()
            for ctrl in filter_controls:
                try:
                    if isinstance(ctrl, ft.Checkbox):
                        ctrl.value = False
                        ctrl.update()
                except Exception:
                    pass
            filtered_data = apply_filters()
            total_items = len(filtered_data)
            total_pages = (total_items + PAGE_PER_CARDS - 1) // PAGE_PER_CARDS if total_items > 0 else 1
            if current_page > total_pages:
                current_page = 1
            buildZukanList(current_page)
            refreshPageLabel()
            self.page.update()
        #検索適用
        def applySearch():
            nonlocal filtered_data, total_items, total_pages, current_page
            q = ""
            try:
                q = str(search_field.value).strip()
            except Exception:
                q = ""
            # ベースはランクフィルタを通したデータ
            base = apply_filters()
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
            apply_sort()
            total_items = len(filtered_data)
            total_pages = (total_items + PAGE_PER_CARDS - 1) // PAGE_PER_CARDS if total_items > 0 else 1
            if current_page > total_pages:
                current_page = 1
            buildZukanList(current_page)
            refreshPageLabel()
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
                count = await __import__("asyncio").to_thread(self.getAllTargetCount)
            except Exception:
                count = -1
            #DBからデータを持ってくる
            data = getAllCards()
            # フィルタ設定（初期は全選択）
            rank_order = ["--", "C", "UC", "R", "SR", "SSR", "UR", "LR"]
            selected_ranks = set(rank_order)
            filtered_data = apply_filters()
            #for card in data:
            #    print(card)
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
            page_input = ft.TextField(
                value=str(current_page), 
                label="No.",
                label_style=ft.TextStyle(
                    size=12,
                ),
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
            page_info = ft.Text(f"/ {total_pages} ({total_items})")
            # on_submit をセット（Enterでジャンプ）
            page_input.on_submit = jumpToPage
            # --- ソート設定 ---
            sort_field = "id"  # default: 入手順(ID順)
            sort_ascending = True
            # 初期ソートとページを構築
            apply_sort()
            buildZukanList(current_page)
            # --- ソートUI: ドロップダウン + ラジオ（昇順/降順） ---
            dropdown = ft.Dropdown(
                width=160,
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
                ],
                editable=False,
            )
            dropdown.on_select = on_dropdown_select
            radio_group = ft.RadioGroup(
                content=ft.Column(
                    spacing=0,
                    controls=[
                        ft.Radio(label="昇順", value="asc"), 
                        ft.Radio(label="降順", value="desc")]
                    ),
                value="asc",
            )
            radio_group.on_change = on_radio_change
            filter_controls = [makeFilterCheckbox(r) for r in rank_order]
            filter_controls.append(
                ft.TextButton(
                    content=ft.Text("全選択"),
                    on_click=filterAllSelect
                )
            )
            filter_controls.append(
                ft.TextButton(
                    content=ft.Text("全解除"),
                    on_click=filterAllUnselect
                )
            )
            # フィルタを2段の丸角ボックスにまとめる
            filter_box = ft.Container(
                #bgcolor=ft.Colors.GREY_200,
                border=ft.Border.all(width=1, color=ft.Colors.GREY),
                border_radius=8,
                padding=ft.Padding.all(8),
                content=ft.Column(
                    spacing=0,
                    controls=[
                        ft.Row(controls=filter_controls[0:6],  spacing=1),
                        ft.Row(controls=filter_controls[6:10], spacing=1),
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
                min_lines=1, 
                max_lines=1, 
                height=36,
                text_size=13,
                expand=True,
            )
            search_field.on_submit = applySearch
            search_ui = ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    search_field,
                ],
            )
            zukan_tab = ft.Column(
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
                                    ft.Row(
                                        spacing=4,
                                        margin=4,
                                        controls=[
                                            dropdown,
                                            radio_group,
                                        ],
                                    ),
                                    ft.Row(
                                        spacing=4,
                                        controls=[
                                            ft.IconButton(
                                                icon=ft.Icons.ARROW_BACK, 
                                                scale=ft.Scale(scale_x=0.8, scale_y=0.8), 
                                                on_click=onPrev
                                            ),
                                            page_input,
                                            page_info,
                                            ft.IconButton(
                                                icon=ft.Icons.ARROW_FORWARD, 
                                                scale=ft.Scale(scale_x=0.8, scale_y=0.8), 
                                                on_click=onNext
                                            ),
                                            ft.Container(
                                                width=20
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            filter_box,
                        ],
                    ),
                    search_ui,
                    table,
                ]
            )
        finally:
            # ローディングオーバーレイを非表示（例外が起きても必ず閉じる）
            try:
                self.loading_overlay.visible = False
                self.page.update()
            except Exception:
                pass
        return zukan_tab