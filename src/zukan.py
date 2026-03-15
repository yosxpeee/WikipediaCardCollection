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
        for card in data:
            print(card)

        table = ft.ListView(
            expand=True,
            spacing=0,
            controls=[],
        )
        #総カウント数÷1ページの分の枚数
        #(余りがあれば+1)

        #データが少ない時の特別措置
        if len(data) < 30:
            dataNum = len(data)
        else:
            dataNum = PAGE_PER_CARDS
        #30ぐらいでちょうどよさげ。これをスタックで積む・・・と多分数万単位になったら困るので
        #nextとかprevで送ったときのそのページを都度都度作って更新しないといけないんだろうな
        for n in range(dataNum):
            rank = rankIdToRank(data[n][5])
            table.controls.append(
                ft.Row(
                    controls=[
                        ft.Text(data[n][0]),  #通し番号
                        ft.Text(data[n][1]),  #pageId
                        ft.Text(rank),  #RANK
                        ft.Text(data[n][2]),  #カード名
                        ft.Text(data[n][9]),  #HP
                        ft.Text(data[n][10]), #ATK
                        ft.Text(data[n][11]), #DEF
                    ],
                ),
            )

        #ページ送り、検索UI
        #<- 現在/総 ->
        #検索[キーワード]
        #フィルタ[C～LR]

        #現在をテキストぼっくスにして
        #あとはどうやってページ送りを実装するか

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