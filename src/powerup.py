import flet as ft
import asyncio
from utils.db import get_card_from_id, rankup_card, get_cards_by_rankid, get_cards_by_sozai, get_cards_by_favorite
from utils.utils import RANK_TABLE, debug_print, rankid_to_rank, rank_to_rankid, calc_status, create_card_image_data
from utils.ui import get_card_color, create_card_image

class PowerUp:
    def __init__(self, page):
        """初期化"""
        self.page = page
        # ローディングオーバーレイの参照を保持(図鑑のものを使いまわし)
        self.loading_overlay = page.overlay[1]
    async def do_powerup(self, target_id, next_rankid, atk, defence, hp, sozai_id):
        """強化実施処理"""
        async def _reload_powerup_tab():
            """画面リロード"""
            try:
                # タブを一時的に無効化する
                tabs_widget = self.page.controls[0]
                tabs_widget.disabled = True
                tabs_widget.update()
                # create() は自身でオーバーレイを表示/非表示するのでそのまま await する
                content = await self.create()
                tab_bar_view = tabs_widget.content.controls[1]
                tab_bar_view.controls[2] = ft.Container(
                    content=content,
                    alignment=ft.Alignment.CENTER,
                )
                tab_bar_view.update()
                # タブを再有効化する
                tabs_widget.disabled = False
                tabs_widget.update()
            except Exception:
                tabs_widget = self.page.controls[0]
                tab_bar_view = tabs_widget.content.controls[1]
                tab_bar_view.controls[2] = ft.Column([ft.Text("読み込みに失敗しました。")])
                tab_bar_view.update()
                tabs_widget.disabled = False
                tabs_widget.update()
        async def _powerup_effect():
            """強化演出"""
            powerup_overlay = ft.Stack(
                expand=True,
                controls=[
                    # 下地
                    ft.Container(
                        expand=True,
                        bgcolor=ft.Colors.with_opacity(0.88, ft.Colors.GREY),
                    ),
                    # カード(対象)
                    ft.Container(
                        width=120,
                        height=140,
                        left=0,
                        top=0,
                        border_radius=8,
                        alignment=ft.Alignment.CENTER,
                        bgcolor=get_card_color(rankid_to_rank(next_rankid-1, 0) ,0),
                        content=ft.Text("✡",size=50, color=ft.Colors.with_opacity(0.5, ft.Colors.BLACK)),
                        shadow=ft.BoxShadow(
                                        blur_style=ft.BlurStyle.NORMAL,
                                        spread_radius=1,
                                        blur_radius=10,
                                        color=ft.Colors.BLACK_45,
                                        offset=ft.Offset(0, 0),
                                    ),
                        animate_position=ft.Animation(1000, ft.AnimationCurve.EASE_IN_OUT_CUBIC_EMPHASIZED)
                    ),
                    # カード(素材)
                    ft.Container(
                        width=120,
                        height=140,
                        left=768-134,
                        top=1024-180,
                        border_radius=8,
                        alignment=ft.Alignment.CENTER,
                        bgcolor=ft.Colors.ORANGE,
                        content=ft.Text("✡",size=50, color=ft.Colors.with_opacity(0.5, ft.Colors.BLACK)),
                        shadow=ft.BoxShadow(
                            blur_style=ft.BlurStyle.NORMAL,
                            spread_radius=1,
                            blur_radius=10,
                            color=ft.Colors.BLACK_45,
                            offset=ft.Offset(0, 0),
                        ),
                        animate_position=ft.Animation(1000, ft.AnimationCurve.EASE_IN_OUT_CUBIC_EMPHASIZED)
                    ),
                ]
            )
            # 今作ったものに差し替える
            self.page.overlay[2] = powerup_overlay
            # オーバーレイの切り替え
            self.loading_overlay = self.page.overlay[2]
            self.page.update()
            await asyncio.sleep(0.1)
            # アニメーション
            powerup_overlay.controls[1].top = 512-60
            powerup_overlay.controls[1].left = 384-80
            powerup_overlay.controls[2].top = 512-60
            powerup_overlay.controls[2].left = 384-80
            self.page.update()
            # アニメーションと同じ時間待機する
            await asyncio.sleep(1)
        # 強化演出を行う
        await _powerup_effect()
        # DBを更新
        rankup_card(target_id, next_rankid, atk, defence, hp, sozai_id)
        # オーバーレイを解いてローディングのものに戻しておく
        self.loading_overlay.visible = False
        self.loading_overlay = self.page.overlay[1]
        self.page.update()
        # 完了通知POP(完了後のカードイメージを出力する)
        row_data = get_card_from_id(target_id)
        row_data_for_image = create_card_image_data(row_data[0])
        self.close_button = ft.TextButton("Close", on_click=lambda e: self.page.pop_dialog())
        complete_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("強化完了"),
            content=ft.Container(
                width=320,
                height=480,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True,
                    controls=[
                        create_card_image(row_data_for_image, True, False),
                    ],
                ),
                bgcolor=ft.Colors.GREY_100, border_radius=5,
                padding=ft.Padding.all(5),
            ),
            actions=[self.close_button],
            actions_alignment=ft.MainAxisAlignment.END,
            title_padding=ft.Padding.all(10),
        )
        self.page.show_dialog(complete_dialog)
        # カードイメージ出力の裏で強化画面の再読み込みを開始する
        tabs_widget = self.page.controls[0]
        tab_bar_view = tabs_widget.content.controls[1]
        tab_bar_view.controls[2] = ft.Container(content=ft.Text("読み込み中...", size=18), alignment=ft.Alignment.CENTER)
        tab_bar_view.update()
        # 非同期で再読み込みを実行（UI スレッドをブロックしない）
        asyncio.create_task(_reload_powerup_tab())
        # Note:タブ切替は再読み込みタスク内で元に戻すためここでは戻さない
        # （create() の完了後に表示更新される想定）
    def popup_powerup_dialog(self, target_id, sozai_id):
        """強化の確認画面表示"""
        def _on_ok(target_id, next_rankid, atk, defence, hp, sozai_id):
            """ダイアログのOKボタンイベント"""
            self.page.pop_dialog()
            asyncio.create_task(self.do_powerup(target_id, next_rankid, atk, defence, hp, sozai_id))
        # 状態チェック
        if target_id == -1:
            self.page.show_dialog(ft.SnackBar(ft.Text("対象が選択されていません。"), duration=1500))
            return
        if sozai_id == -1:
            self.page.show_dialog(ft.SnackBar(ft.Text("素材が選択されていません。"), duration=1500))
            return
        # idからパラメータをとってくる
        data = get_card_from_id(target_id)
        title = data[0][2]
        a_resource = int(data[0][13])
        d_resource = int(data[0][14])
        rankid = int(data[0][5])
        next_rankid = int(data[0][5])+1
        if next_rankid > 6:
            self.page.show_dialog(ft.SnackBar(ft.Text("LR以上にはランクアップできません。"), duration=1500))
            return
        sozai_data = get_card_from_id(sozai_id)
        sozai_title = sozai_data[0][2]
        # 強化シミュレート
        debug_print(self.page.debug, f"#################### {data[0][2]} 強化シミュレート")
        simulate_data = []
        defence = 0
        atk     = 0
        hp      = 0
        for r in RANK_TABLE:
            if r >= next_rankid:
                tmp_defence, tmp_atk, tmp_hp = calc_status(d_resource, a_resource, rankid_to_rank(r, 0))
                if self.page.debug:
                    debug_print(self.page.debug, f"{rankid_to_rank(r, 0)} | ATK:{tmp_atk} DEF:{tmp_defence} HP:{tmp_hp}")
                if r == next_rankid:
                    defence = tmp_defence
                    atk     = tmp_atk
                    hp      = tmp_hp
                    simulate_data.append(
                        ft.Text(
                            f"{rankid_to_rank(r, 0).ljust(3, ' ')} | HP:{str(hp).ljust(5, ' ')} ATK:{str(atk).ljust(5, ' ')} DEF:{str(defence).ljust(5, ' ')}", 
                            font_family="Consolas",
                            color=ft.Colors.RED
                        )
                    )
                else:
                    simulate_data.append(
                        ft.Text(
                            f"{rankid_to_rank(r, 0).ljust(3, ' ')} | HP:{str(tmp_hp).ljust(5, ' ')} ATK:{str(tmp_atk).ljust(5, ' ')} DEF:{str(tmp_defence).ljust(5, ' ')}",
                            font_family="Consolas",
                        )
                    )
        simulate = ft.Column(
            controls=simulate_data,
            spacing=0
        )
        # ダイアログ作成
        self.cancel_button = ft.TextButton("Cancel", on_click=lambda e: self.page.pop_dialog())
        self.OK_button = ft.TextButton("OK", on_click=lambda x:_on_ok(target_id, next_rankid, atk, defence, hp, sozai_id))
        powerup_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("カード強化"),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
                expand=True,
                spacing=0,
                controls=[
                    ft.Text(f"強化対象: {title}",no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(f"使用素材: {sozai_title}",no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Divider(height=1),
                    simulate,
                    ft.Divider(height=1),
                    ft.Container(width=20, height=10),
                    ft.Text(f"現在の{rankid_to_rank(rankid, 0)}ランクから{rankid_to_rank(next_rankid, 0)}への強化を行いますか？")
                ],
            ),
            actions=[self.cancel_button, self.OK_button],
            actions_alignment=ft.MainAxisAlignment.END,
            title_padding=ft.Padding.all(10),
        )
        self.page.show_dialog(powerup_dialog)
    async def create(self):
        """画面作成"""
        ####################
        # 処理開始
        ####################
        # ローディングオーバーレイを表示
        self.loading_overlay.visible = True
        self.page.update()
        selected_target_id = -1
        selected_sozai_id = -1
        try:
            # DB からカードを非同期で取得（ランクごとに分割して取得）
            ranks = ["UR", "SSR", "SR", "R", "UC", "C", "★"]
            # ランクごとにDBから必要な行だけ取得してメモリを分割する
            all_cards_by_rank = {}
            for rk in ranks:
                if rk == "★":
                    rows = await asyncio.to_thread(get_cards_by_favorite)
                else:
                    rid = rank_to_rankid(rk)
                    rows = await asyncio.to_thread(get_cards_by_rankid, rid, 0)
                all_cards_by_rank[rk] = rows
            # 素材一覧は別途取得しておく
            sozai_all = await asyncio.to_thread(get_cards_by_sozai, 1)
            # 表示用テキスト
            selected_target_text = ft.Text("",no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS, bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.GREY_500))
            selected_sozai_text = ft.Text("",no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS, bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.ORANGE))
            # コンテナ参照リスト（ハイライト更新用）
            target_containers = []
            sozai_containers = []
            # 左側：ランク別タブの ListView を作成（共通化）
            from utils.ui import create_ranked_tabs
            def _on_target_selected(cid, name, rk, hp, atk, deff, img):
                nonlocal selected_target_id
                selected_target_id = cid
                selected_target_text.value = f"{cid} [{rk}] {name}"
                selected_target_text.update()
            target_tab = create_ranked_tabs(ranks, all_cards_by_rank, on_select_callback=_on_target_selected)
            # 右側：素材一覧（isSozai == 1）
            sozai_lv = ft.ListView(
                expand=True, 
                spacing=0, 
                controls=[]
            )
            for row in sozai_all:
                # sozai_all は isSozai==1 の行のみ
                cid = row[0]
                name = row[2] or ""
                cont = ft.Container(
                    padding=ft.Padding(top=0, left=6, right=6, bottom=0),
                    bgcolor=None,
                    content=ft.Row(
                        controls=[
                            ft.Text(str(cid).ljust(8, " "), font_family="Consolas"), 
                            ft.Text(name, expand=True, tooltip=name, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS)
                        ],
                    ),
                )
                def _on_sozai_click(e, cid=cid, name=name, cont=cont):
                    """素材リストをクリックしたときの処理"""
                    nonlocal selected_sozai_id
                    selected_sozai_id = cid
                    selected_sozai_text.value = f"{cid} : {name}"
                    selected_sozai_text.update()
                    for c in sozai_containers:
                        c.bgcolor = None
                        c.content.controls[0].color = None
                        c.content.controls[1].color = None
                        c.update()
                    cont.bgcolor = ft.Colors.YELLOW_100
                    cont.content.controls[0].color = ft.Colors.BLACK
                    cont.content.controls[1].color = ft.Colors.BLACK
                    cont.update()
                cont.on_click = _on_sozai_click
                sozai_lv.controls.append(cont)
                sozai_containers.append(cont)
            # 素材一覧が空ならプレースホルダを表示
            if len(sozai_lv.controls) == 0:
                sozai_lv.controls.append(ft.Container(padding=ft.Padding.all(8), content=ft.Text("素材が見つかりません")))
            # 強化タブ本体
            powerup_tab = ft.Column(
                controls=[
                    ft.Stack(
                        controls=[
                            ft.ShaderMask(      #バックグラウンド
                                width=738,
                                height=784,
                                content=ft.Container(
                                    border=ft.Border.all(0),
                                    width=738,
                                    height=784,
                                    alignment=ft.Alignment.CENTER,
                                    bgcolor=ft.Colors.ON_PRIMARY,
                                    content=None,
                                ),
                                blend_mode=ft.BlendMode.SRC_IN,
                                shader=ft.RadialGradient(
                                    center=ft.Alignment.CENTER, 
                                    radius=0.22, 
                                    colors=[ft.Colors.ON_PRIMARY, ft.Colors.PRIMARY_CONTAINER, ft.Colors.ON_PRIMARY], 
                                    stops=[0.2, 0.8, 1.0], 
                                    tile_mode=ft.GradientTileMode.REPEATED
                                ),
                            ),
                            ft.Row(
                                width=738,
                                height=784,
                                alignment=ft.MainAxisAlignment.CENTER,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Container(       #左(対象)
                                        width=460,
                                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREY_900),
                                        alignment=ft.Alignment.TOP_CENTER,
                                        content=ft.Column(
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                            spacing=0,
                                            controls=[
                                                ft.Text("対象",weight=ft.FontWeight.BOLD), 
                                                ft.Divider(color=ft.Colors.GREY, height=1), 
                                                target_tab
                                            ],
                                        ),
                                    ),
                                    ft.Container(       #右(素材)
                                        width=268,
                                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREY_900),
                                        alignment=ft.Alignment.TOP_CENTER,
                                        content=ft.Column(
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                            spacing=0,
                                            controls=[
                                                ft.Text(f"素材",weight=ft.FontWeight.BOLD),
                                                ft.Divider(color=ft.Colors.GREY, height=1),
                                                ft.Container(
                                                    padding=ft.Padding.all(6),
                                                    bgcolor=None,
                                                    content=ft.Row(
                                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                                        controls=[
                                                            ft.Text("ID".ljust(8," "), font_family="Consolas", bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.ORANGE)),
                                                            ft.Text("カード名", expand=True, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS, bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.ORANGE)),
                                                        ],
                                                    ),
                                                ),
                                                ft.Divider(color=ft.Colors.GREY, height=1),
                                                sozai_lv,
                                            ],
                                        ),
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.Column(      #選択したアイテムの表示
                        spacing=0, 
                        controls=[
                            ft.Row(controls=[ft.Text("対象: "), selected_target_text]),
                            ft.Row(controls=[ft.Text("素材: "), selected_sozai_text]),
                        ]
                    ),
                    ft.Container(   #強化実行ボタン
                        width=738,
                        height=34,
                        padding=ft.Padding.all(0),
                        content=ft.Button(
                            "強化する", 
                            on_click=lambda x:self.popup_powerup_dialog(selected_target_id, selected_sozai_id)
                        )
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
        return powerup_tab
