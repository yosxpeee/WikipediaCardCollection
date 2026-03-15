import flet as ft
from bs4 import BeautifulSoup

from utils.utils import doApi

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
        # ローディングオーバーレイを表示
        self.loading_overlay.visible = True
        self.page.update()
        #要素数決めたいので中身空でstaticに作ってみる
        table = ft.ListView(
            expand=True,
            spacing=0,
            controls=[],
        )
        #あとはどうやってページ送りを実装するか
        for n in range(40): #40ぐらいでちょうどよさげ
            table.controls.append(
                ft.Row(
                    controls=[
                        ft.Text(str(n)),
                        ft.Text("PageId"),
                        ft.Text("RANK"),
                        ft.Text("HP"),
                        ft.Text("ATK"),
                        ft.Text("DEF"),
                    ],
                ),
            )
        # 総記事数はブロッキングなのでバックグラウンドで取得
        try:
            count = await __import__("asyncio").to_thread(self.getAllTargetCount)
        except Exception:
            count = -1

        zukan_tab = ft.Column(
            controls=[
                ft.Text(f"総記事数：{count}"),
                table,
            ]
        )
        # ローディングオーバーレイを非表示
        self.loading_overlay.visible = False
        self.page.update()
        return zukan_tab