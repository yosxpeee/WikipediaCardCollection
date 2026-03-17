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
        self.loadingOverlay = page.overlay[1]
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
        self.closeButton = ft.TextButton("Close", on_click=lambda e: self.page.pop_dialog())
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
            actions=[self.closeButton],
            actions_alignment=ft.MainAxisAlignment.END,
            title_padding=ft.Padding.all(10),
        )
        self.page.show_dialog(self.dialog)
    # 画面作成
    async def create(self):
        def buildPage(page):
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
            if totalItems == 0:
                #table.controls.append(ft.Text("データがありません"))
                return
            start = (page - 1) * PAGE_PER_CARDS
            end = min(start + PAGE_PER_CARDS, totalItems)
            for idx in range(start, end):
                row_data = filteredData[idx]
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
                numText = str(row_data[0]).ljust(8, " ")
                pageidText = str(row_data[1]).ljust(8, " ")
                rankText = str(rank).ljust(4, " ")
                nameText = row_data[2] if row_data[2] is not None else ""
                if row_data[9] == "-1":
                    hpText = "-".ljust(5, " ") if row_data[9] is not None else "".ljust(5, " ")
                else:
                    hpText = str(row_data[9]).ljust(5, " ") if row_data[9] is not None else "".ljust(5, " ")
                if row_data[10] == "-1":
                    atkText = "-".ljust(5, " ") if row_data[10] is not None else "".ljust(5, " ")
                else:
                    atkText = str(row_data[10]).ljust(5, " ") if row_data[10] is not None else "".ljust(5, " ")
                if row_data[11] == "-1":
                    defText = "-".ljust(5, " ") if row_data[11] is not None else "".ljust(5, " ")
                else:
                    defText = str(row_data[11]).ljust(5, " ") if row_data[11] is not None else "".ljust(5, " ")
                table.controls.append(
                    ft.Row(
                        spacing=12,
                        controls=[
                            ft.Text(numText, font_family="Consolas"),
                            ft.Text(pageidText, font_family="Consolas"),
                            ft.Text(rankText, font_family="Consolas"),
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
                            ft.Text(hpText, font_family="Consolas"),
                            ft.Text(atkText, font_family="Consolas"),
                            ft.Text(defText, font_family="Consolas"),
                        ],
                    )
                )
        def refreshPageLabel():
            # pageInput を現在ページに合わせて更新
            try:
                pageInput.value = str(currentPage)
                pageInput.update()
                pageInfo.value = f"/ {totalPages} ({totalItems})"
                pageInfo.update()
            except Exception:
                pass
        # ページ操作
        def onPrev(e):
            nonlocal currentPage
            if currentPage > 1:
                currentPage -= 1
                buildPage(currentPage)
                refreshPageLabel()
                self.page.update()
        def onNext(e):
            nonlocal currentPage
            if currentPage < totalPages:
                currentPage += 1
                buildPage(currentPage)
                refreshPageLabel()
                self.page.update()
        def jumpToPage(e):
            nonlocal currentPage
            # e.control は TextField
            v = str(e.control.value).strip()
            try:
                n = int(v)
            except Exception:
                e.control.value = str(currentPage)
                e.control.update()
                return
            if n < 1 or n > totalPages:
                e.control.value = str(currentPage)
                e.control.update()
                return
            currentPage = n
            buildPage(currentPage)
            refreshPageLabel()
            self.page.update()
        # ローディングオーバーレイを表示
        self.loadingOverlay.visible = True
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
            rankOrder = ["--", "C", "UC", "R", "SR", "SSR", "UR", "LR"]
            selectedRanks = set(rankOrder)
            def apply_filters():
                filtered = []
                for row in data:
                    r = rankIdToRank(row[5], row[7])
                    if r in selectedRanks:
                        filtered.append(row)
                return filtered
            filteredData = apply_filters()
            #for card in data:
            #    print(card)
            table = ft.ListView(
                expand=True,
                spacing=0,
                controls=[],
            )
            # ページネーション設定（filteredData に基づく）
            totalItems = len(filteredData)
            totalPages = (totalItems + PAGE_PER_CARDS - 1) // PAGE_PER_CARDS if totalItems > 0 else 1
            currentPage = 1
            # ページ入力（現在ページを入力してジャンプできる）
            pageInput = ft.TextField(
                value=str(currentPage), 
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
            pageInfo = ft.Text(f"/ {totalPages} ({totalItems})")
            # on_submit をセット（Enterでジャンプ）
            pageInput.on_submit = jumpToPage
            # 初期ページを構築
            buildPage(currentPage)
            # フィルタ用チェックボックスを作成（素材→C→... の順）
            def makeFilterCheckbox(rk):
                # 表示用のラベル（素材は見やすくする）
                displayLabel = "素材" if rk == "--" else rk
                cb = ft.Checkbox(label=displayLabel, label_position=ft.LabelPosition.LEFT, value=True)
                def _on_change(e):
                    nonlocal filteredData, totalItems, totalPages, currentPage
                    if e.control.value:
                        selectedRanks.add(rk)
                    else:
                        selectedRanks.discard(rk)
                    filteredData = apply_filters()
                    totalItems = len(filteredData)
                    totalPages = (totalItems + PAGE_PER_CARDS - 1) // PAGE_PER_CARDS if totalItems > 0 else 1
                    if currentPage > totalPages:
                        currentPage = 1
                    buildPage(currentPage)
                    refreshPageLabel()
                    self.page.update()
                cb.on_change = _on_change
                return cb
            filterControls = [makeFilterCheckbox(r) for r in rankOrder]
            # フィルタを2段の丸角ボックスにまとめる
            filterBox = ft.Container(
                bgcolor=ft.Colors.GREY_200,
                border_radius=8,
                padding=ft.Padding.all(8),
                content=ft.Column(
                    controls=[
                        ft.Row(controls=filterControls[0:6], spacing=1),
                        ft.Row(controls=filterControls[6:8], spacing=1),
                    ],
                ),
            )
            zukanTab = ft.Column(
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[ft.Text(f"Wikipedia 日本語版 取得対象総記事数：{count}")],
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=0,
                        controls=[
                            ft.Row(
                                spacing=4,
                                controls=[
                                    ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=onPrev),
                                    pageInput,
                                    pageInfo,
                                    ft.IconButton(icon=ft.Icons.ARROW_FORWARD, on_click=onNext),
                                    ft.Container(width=20),
                                ],
                            ),
                            filterBox,
                        ],
                    ),
                    table,
                ]
            )
        finally:
            # ローディングオーバーレイを非表示（例外が起きても必ず閉じる）
            try:
                self.loadingOverlay.visible = False
                self.page.update()
            except Exception:
                pass
        return zukanTab