import flet as ft
from bs4 import BeautifulSoup

from utils.utils import doApi, rankIdToRank
from utils.db import get_all_cards

PAGE_PER_CARDS = 30

class Zukan:
    # 初期化
    def __init__(self, page):
        self.page = page
        # ローディングオーバーレイの参照を保持
        self.loading_overlay = page.overlay[0]
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
    # 画面作成
    async def create(self):
        def build_page(page):
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
                        content=ft.Text(
                            "カード名",
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
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
                row_data = data[idx]
                #print(row_data[7])
                rank = rankIdToRank(row_data[5], row_data[7])
                num_text = str(row_data[0]).ljust(8, " ")
                pageid_text = str(row_data[1]).ljust(8, " ")
                rank_text = str(rank).ljust(4, " ")
                name_text = row_data[2] if row_data[2] is not None else ""
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
                                content=ft.Text(
                                    name_text,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                            ),
                            ft.Text(hp_text, font_family="Consolas"),
                            ft.Text(atk_text, font_family="Consolas"),
                            ft.Text(def_text, font_family="Consolas"),
                        ],
                    )
                )
        def refresh_page_label():
            page_label.value = f"{current_page} / {total_pages} ({total_items})"
        # ページ操作
        def on_prev(e):
            nonlocal current_page
            if current_page > 1:
                current_page -= 1
                build_page(current_page)
                self.page.update()
        def on_next(e):
            nonlocal current_page
            if current_page < total_pages:
                current_page += 1
                build_page(current_page)
                self.page.update()
        # ローディングオーバーレイを表示
        self.loading_overlay.visible = True
        self.page.update()
        # 総記事数はブロッキングなのでバックグラウンドで取得
        try:
            count = await __import__("asyncio").to_thread(self.getAllTargetCount)
        except Exception:
            count = -1
        #DBからデータを持ってくる
        data = get_all_cards()
        #for card in data:
        #    print(card)
        table = ft.ListView(
            expand=True,
            spacing=0,
            controls=[],
        )
        # ページネーション設定
        total_items = len(data)
        total_pages = (total_items + PAGE_PER_CARDS - 1) // PAGE_PER_CARDS if total_items > 0 else 1
        current_page = 1
        # ページ表示ラベル（更新は build_page 後に page.update で）
        page_label = ft.Text(f"{current_page} / {total_pages} ({total_items})")
        # 初期ページを構築
        build_page(current_page)
        zukan_tab = ft.Column(
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[ft.Text(f"Wikipedia 日本語版 取得対象総記事数：{count}")],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: (on_prev(e), refresh_page_label())),
                        page_label,
                        ft.IconButton(icon=ft.Icons.ARROW_FORWARD, on_click=lambda e: (on_next(e), refresh_page_label())),
                    ],
                ),
                table,
            ]
        )
        # ローディングオーバーレイを非表示
        self.loading_overlay.visible = False
        self.page.update()
        return zukan_tab