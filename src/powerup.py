import flet as ft
import asyncio
from utils.db import get_all_cards, get_card_from_id, rankup_card
from utils.utils import RANK_TABLE, rankid_to_rank, calc_status
from utils.ui import get_card_color

class PowerUp:
    # 初期化
    def __init__(self, page):
        self.page = page
        # ローディングオーバーレイの参照を保持(図鑑のものを使いまわし)
        self.loading_overlay = page.overlay[1]
    # 強化実施処理
    async def do_powerup(self, target_id, next_rankid, atk, defence, hp, sozai_id):
        # 強化タブ自身を再読み込みして差し替える
        async def _reload_powerup_tab():
            try:
                # create() は自身でオーバーレイを表示/非表示するのでそのまま await する
                content = await self.create()
                try:
                    tabs_widget = self.page.controls[0]
                    tab_bar_view = tabs_widget.content.controls[1]
                    tab_bar_view.controls[2] = ft.Container(
                        content=content,
                        alignment=ft.Alignment.CENTER,
                    )
                    tab_bar_view.update()
                    # タブ切替を元に戻す
                    try:
                        tabs_widget.disabled = False
                        tabs_widget.update()
                    except Exception:
                        pass
                except Exception:
                    pass
            except Exception:
                try:
                    tabs_widget = self.page.controls[0]
                    tab_bar_view = tabs_widget.content.controls[1]
                    tab_bar_view.controls[2] = ft.Column([ft.Text("読み込みに失敗しました。")])
                    tab_bar_view.update()
                    try:
                        tabs_widget.disabled = False
                        tabs_widget.update()
                    except Exception:
                        pass
                except Exception:
                    pass
        # 強化演出
        async def _powerup_effect():
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
                        top=0,
                        left=0,
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
                    # カード素材
                    ft.Container(
                        width=120,
                        height=140,
                        top=1024-140,
                        left=768-120,
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
            #今作ったものに差し替える
            self.page.overlay[2] = powerup_overlay
            #オーバーレイの切り替え
            self.loading_overlay = self.page.overlay[2]
            self.page.update()
            await asyncio.sleep(0.1)
            #アニメーション
            powerup_overlay.controls[1].top = 512-60
            powerup_overlay.controls[1].left = 384-80
            powerup_overlay.controls[2].top = 512-60
            powerup_overlay.controls[2].left = 384-80
            self.page.update()
            await asyncio.sleep(1) #アニメーションと同じ時間待機する
        # タブ切替を一時無効化
        try:
            tabs_widget.disabled = True
            tabs_widget.update()
        except Exception:
            pass
        # 強化演出を行う
        await _powerup_effect()
        # DB を更新
        rankup_card(target_id, next_rankid, atk, defence, hp, sozai_id)
        self.loading_overlay.visible = False
        # オーバーレイをローディングのものに戻す
        self.loading_overlay = self.page.overlay[1]
        self.page.update()
        # 完了通知POP
        self.page.show_dialog(ft.SnackBar(ft.Text("アップグレード完了"), bgcolor=ft.Colors.LIGHT_GREEN, duration=1500))
        # 表示用のプレースホルダを即時反映してから再読み込みを開始する
        try:
            tabs_widget = self.page.controls[0]
            tab_bar_view = tabs_widget.content.controls[1]
            tab_bar_view.controls[2] = ft.Container(content=ft.Text("読み込み中...", size=18), alignment=ft.Alignment.CENTER)
            tab_bar_view.update()
        except Exception:
            pass
        # 非同期で再読み込みを実行（UI スレッドをブロックしない）
        try:
            asyncio.create_task(_reload_powerup_tab())
        finally:
            # タブ切替は再読み込みタスク内で元に戻すためここでは戻さない
            # （create() の完了後に表示更新される想定）
            pass
    # 強化の確認画面表示
    def popup_powerup_dialog(self, target_id, sozai_id):
        if target_id == -1:
            self.page.show_dialog(ft.SnackBar(ft.Text("対象が選択されていません。"), duration=1500))
            return
        if sozai_id == -1:
            self.page.show_dialog(ft.SnackBar(ft.Text("素材が選択されていません。"), duration=1500))
            return
        #idからパラメータをとってくる
        data = get_card_from_id(target_id)
        title = data[0][2]
        a_resource = int(data[0][13])
        d_resource = int(data[0][14])
        rankid = int(data[0][5])
        next_rankid = int(data[0][5])+1
        # 強化シミュレート
        print(f"#################### {data[0][2]} 強化シミュレート")
        simulate_data = []
        defence = 0
        atk     = 0
        hp      = 0
        for r in RANK_TABLE:
            if r >= next_rankid:
                defence, atk, hp = calc_status(d_resource, a_resource, rankid_to_rank(r, 0))
                print(f"{rankid_to_rank(r, 0)} | ATK:{atk} DEF:{defence} HP:{hp}")
                if r == next_rankid:
                    simulate_data.append(
                        ft.Text(
                            f"{rankid_to_rank(r, 0).ljust(3, " ")} | ATK:{str(atk).ljust(5, " ")} DEF:{str(defence).ljust(5, " ")} HP:{str(hp).ljust(5, " ")}", 
                            font_family="Consolas",
                            color=ft.Colors.RED
                        )
                    )
                else:
                    simulate_data.append(
                        ft.Text(
                            f"{rankid_to_rank(r, 0).ljust(3, " ")} | ATK:{str(atk).ljust(5, " ")} DEF:{str(defence).ljust(5, " ")} HP:{str(hp).ljust(5, " ")}",
                            font_family="Consolas",
                        )
                    )
        simulate = ft.Column(
            controls=simulate_data,
            spacing=0
        )
        # ダイアログ作成
        self.cancel_button = ft.TextButton("Cancel", on_click=lambda e: self.page.pop_dialog())
        def _on_ok(e, tid=target_id, nr=next_rankid, a=atk, d=defence, h=hp, sid=sozai_id):
            try:
                self.page.pop_dialog()
            except Exception:
                pass
            try:
                asyncio.create_task(self.do_powerup(tid, nr, a, d, h, sid))
            except Exception:
                pass
        self.OK_button = ft.TextButton("OK", on_click=_on_ok)
        powerup_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("カード強化"),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
                expand=True,
                spacing=0,
                controls=[
                    ft.Text(f"対象: {title}",no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Divider(height=1),
                    simulate,
                    ft.Divider(height=1),
                    ft.Container(width=20, height=20),
                    ft.Text(f"現在の{rankid_to_rank(rankid, 0)}ランクから{rankid_to_rank(next_rankid, 0)}への強化を行いますか？")
                ],
            ),
            actions=[self.cancel_button, self.OK_button],
            actions_alignment=ft.MainAxisAlignment.END,
            title_padding=ft.Padding.all(10),
        )
        self.page.show_dialog(powerup_dialog)
    # 画面作成
    async def create(self):
        ####################
        # 処理開始
        ####################
        # ローディングオーバーレイを表示
        self.loading_overlay.visible = True
        self.page.update()
        selected_target_id = -1
        selected_sozai_id = -1
        try:
            # DB からカードを非同期で取得（ブロッキング回避）
            try:
                all_cards = await asyncio.to_thread(get_all_cards)
            except Exception:
                all_cards = []
            ranks = ["UR", "SSR", "SR", "R", "UC", "C"]
            # 表示用テキスト
            selected_target_text = ft.Text("",no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS, bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.GREY_500))
            selected_sozai_text = ft.Text("",no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS, bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.ORANGE))
            # コンテナ参照リスト（ハイライト更新用）
            target_containers = []
            sozai_containers = []
            # 左側：ランク別タブの ListView を作成
            tab_views = []
            for rk in ranks:
                lv = ft.ListView(
                    expand=True, 
                    spacing=0, 
                    auto_scroll=False, 
                    controls=[]
                )
                for row in all_cards:
                    # row: (id, pageId, title, pageUrl, imageUrl, rank, quality, isSozai, extract, HP, ATK, DEF, ...)
                    try:
                        row_rank = rankid_to_rank(row[5], row[7])
                    except Exception:
                        row_rank = ""
                    if row_rank == rk and int(row[7]) == 0:
                        cid = row[0]
                        name = row[2] or ""
                        hp = row[9] if row[9] is not None else "-"
                        atk = row[10] if row[10] is not None else "-"
                        deff = row[11] if row[11] is not None else "-"
                        cont = ft.Container(
                            padding=ft.Padding(top=0, left=6, right=6, bottom=0),
                            bgcolor=None,
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(str(cid).ljust(8, " "), font_family="Consolas"),
                                    ft.Container(width=10),
                                    ft.Text(name, expand=True, tooltip=name, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Container(width=10),
                                    ft.Text(str(hp).ljust(5, " "), font_family="Consolas"),
                                    ft.Text(str(atk).ljust(5, " "), font_family="Consolas"),
                                    ft.Text(str(deff).ljust(5, " "), font_family="Consolas"),
                                    ft.Text(rk, disabled=True)
                                ],
                            ),
                        )
                        def _on_target_click(e, cid=cid, name=name, rk=rk, cont=cont):
                            nonlocal selected_target_id
                            selected_target_id = cid
                            try:
                                selected_target_text.value = f"{cid} [{rk}] {name}"
                                selected_target_text.update()
                            except Exception:
                                pass
                            # ハイライト更新
                            for c in target_containers:
                                try:
                                    c.bgcolor = None
                                    c.update()
                                except Exception:
                                    pass
                            try:
                                cont.bgcolor = ft.Colors.YELLOW_100
                                cont.update()
                            except Exception:
                                pass
                        cont.on_click = _on_target_click
                        lv.controls.append(cont)
                        target_containers.append(cont)
                # ヘッダ（ListView の外に置くことでスクロール時に固定される）
                header = ft.Container(
                    padding=ft.Padding.all(6),
                    bgcolor=None,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("ID".ljust(8, " "), font_family="Consolas", bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.WHITE)),
                            ft.Container(width=10),
                            ft.Text("カード名",expand=True, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS, bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.WHITE)),
                            ft.Container(width=10),
                            ft.Text("HP".ljust(5, " "), font_family="Consolas", bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.WHITE)),
                            ft.Text("ATK".ljust(5, " "), font_family="Consolas", bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.WHITE)),
                            ft.Text("DEF".ljust(5, " "), font_family="Consolas", bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.WHITE)),
                        ],
                    )
                )
                tab_views.append(
                    ft.Container(
                        alignment=ft.Alignment.CENTER,
                        content=ft.Column(
                            controls=[header, lv]
                        ), 
                    )
                )
                # 素材一覧が空ならプレースホルダを表示
                if len(lv.controls) == 0:
                    lv.controls.append(ft.Container(padding=ft.Padding.all(8), content=ft.Text("対象が見つかりません")))
            target_tab = ft.Tabs(
                selected_index=0,
                length=len(ranks),
                expand=True,
                content=ft.Column(
                    expand=True,
                    controls=[
                        ft.TabBar(tab_alignment=ft.TabAlignment.CENTER, tabs=[ft.Tab(label=r) for r in ranks]),
                        ft.TabBarView(expand=True, controls=tab_views),
                    ],
                ),
            )
            # 右側：素材一覧（isSozai == 1）
            sozai_lv = ft.ListView(
                expand=True, 
                spacing=0, 
                controls=[]
            )
            for row in all_cards:
                try:
                    if int(row[7]) == 1:
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
                            nonlocal selected_sozai_id
                            selected_sozai_id = cid
                            try:
                                selected_sozai_text.value = f"{cid} : {name}"
                                selected_sozai_text.update()
                            except Exception:
                                pass
                            for c in sozai_containers:
                                try:
                                    c.bgcolor = None
                                    c.update()
                                except Exception:
                                    pass
                            try:
                                cont.bgcolor = ft.Colors.YELLOW_100
                                cont.update()
                            except Exception:
                                pass
                        cont.on_click = _on_sozai_click
                        sozai_lv.controls.append(cont)
                        sozai_containers.append(cont)
                except Exception:
                    pass
            # 素材一覧が空ならプレースホルダを表示
            if len(sozai_lv.controls) == 0:
                sozai_lv.controls.append(ft.Container(padding=ft.Padding.all(8), content=ft.Text("素材が見つかりません")))
            # 強化タブ本体
            powerup_tab = ft.Column(
                controls=[
                    ft.Stack(
                        controls=[
                            ft.ShaderMask(
                                content=ft.Container(
                                    border=ft.Border.all(0),
                                    width=728,
                                    height=776,
                                    alignment=ft.Alignment.CENTER,
                                    bgcolor=ft.Colors.ON_PRIMARY,
                                    content=None,
                                ),
                                blend_mode=ft.BlendMode.SRC_IN,
                                shader=ft.RadialGradient(center=ft.Alignment.CENTER, radius=0.22, colors=[ft.Colors.ON_PRIMARY, ft.Colors.PRIMARY_CONTAINER, ft.Colors.ON_PRIMARY], stops=[0.2, 0.8, 1.0], tile_mode=ft.GradientTileMode.REPEATED),
                            ),
                            ft.Row(
                                width=728,
                                height=776,
                                alignment=ft.MainAxisAlignment.CENTER,
                                vertical_alignment=ft.CrossAxisAlignment.START,
                                controls=[
                                    ft.Container(
                                        width=450,
                                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREY_900),
                                        alignment=ft.Alignment.TOP_CENTER,
                                        content=ft.Column(
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                            controls=[
                                                ft.Text("対象",weight=ft.FontWeight.BOLD), 
                                                ft.Divider(color=ft.Colors.GREY, height=1), 
                                                target_tab
                                            ],
                                        ),
                                    ),
                                    ft.Container(
                                        width=250,
                                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREY_900),
                                        alignment=ft.Alignment.TOP_CENTER,
                                        content=ft.Column(
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                            controls=[
                                                ft.Text(f"素材"),
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
                                                sozai_lv,
                                            ],
                                        ),
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.Column(
                        spacing=0, 
                        controls=[
                            ft.Row(controls=[ft.Text("対象: "), selected_target_text]),
                            ft.Row(controls=[ft.Text("素材: "), selected_sozai_text]),
                        ]
                    ),
                    ft.Container(
                        width=728, 
                        height=100, 
                        expand=True, 
                        content=ft.Button("強化する", on_click=lambda x:self.popup_powerup_dialog(selected_target_id, selected_sozai_id))
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