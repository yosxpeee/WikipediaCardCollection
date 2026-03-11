import flet as ft
from bs4 import BeautifulSoup
from utils.utils import doApi

class Zukan:
    # 初期化
    def __init__(self):
        pass
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
    def create(self):
        zukan_tab = ft.Column(
            alignment=ft.Alignment.CENTER,
            controls=[
                ft.Text(f"総記事数：{self.getAllTargetCount()}")
            ]
        )
        return zukan_tab