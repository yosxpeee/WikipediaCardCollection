import flet as ft
import asyncio
from utils.db import get_card_from_id, rankup_card, get_cards_by_rankid, get_cards_by_sozai
from utils.utils import RANK_TABLE, rankid_to_rank, rank_to_rankid, calc_status
from utils.ui import get_card_color, create_card_image

class PowerUp:
    def __init__(self, page):
        """初期化"""
        self.page = page
        # ローディングオーバーレイの参照を保持(図鑑のものを使いまわし)
        self.loading_overlay = page.overlay[1]
    async def do_powerup(self, target_id, next_rankid, atk, defence, hp, sozai_id):
        """強化実施処理"""
        # 強化タブ自身を再読み込みして差し替える
        async def _reload_powerup_tab():
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
        rank = rankid_to_rank(row_data[0][5], 0)
        rank_origin = rankid_to_rank(row_data[0][15], 0)
        row_data_for_image = {
            "id": row_data[0][0],
            "pageId": row_data[0][1],
            "title": row_data[0][2],
            "pageUrl": row_data[0][3],
            "imageUrl": row_data[0][4],
            "rank": rank,
            "quality": row_data[0][6],
            "isSozai": row_data[0][7],
            "extract": row_data[0][8],
            "HP": row_data[0][9],
            "ATK": row_data[0][10],
            "DEF": row_data[0][11],
            "favorite": row_data[0][12],
            "resourceATK": row_data[0][13],
            "resourceDEF": row_data[0][14],
            "resourceRANK": rank_origin,
        }
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
        # Note:
        # タブ切替は再読み込みタスク内で元に戻すためここでは戻さない
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
        sozai_data = get_card_from_id(sozai_id)
        sozai_title = sozai_data[0][2]
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
                            f"{rankid_to_rank(r, 0).ljust(3, ' ')} | HP:{str(hp).ljust(5, ' ')} ATK:{str(atk).ljust(5, ' ')} DEF:{str(defence).ljust(5, ' ')}", 
                            font_family="Consolas",
                            color=ft.Colors.RED
                        )
                    )
                else:
                    simulate_data.append(
                        ft.Text(
                            f"{rankid_to_rank(r, 0).ljust(3, ' ')} | HP:{str(hp).ljust(5, ' ')} ATK:{str(atk).ljust(5, ' ')} DEF:{str(defence).ljust(5, ' ')}",
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
            ranks = ["UR", "SSR", "SR", "R", "UC", "C"]
            # ランクごとにDBから必要な行だけ取得してメモリを分割する
            all_cards_by_rank = {}
            for rk in ranks:
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
            # 左側：ランク別タブの ListView を作成
            tab_views = []
            for rk in ranks:
                lv = ft.ListView(
                    expand=True, 
                    spacing=0, 
                    auto_scroll=False, 
                    controls=[]
                )
                # フィルタ/ソート/検索UIを個別に生成してから表示データを構築する
                sort_dd = ft.Dropdown(
                    margin=ft.Margin.all(0),
                    border_color=ft.Colors.GREY,
                    value="id",
                    options=[
                        ft.DropdownOption(key="id",   text="ID順"),
                        ft.DropdownOption(key="name", text="名前順"),
                        ft.DropdownOption(key="HP",   text="HP順"),
                        ft.DropdownOption(key="ATK",  text="ATK順"),
                        ft.DropdownOption(key="DEF",  text="DEF順"),
                    ],
                    editable=False,
                )
                sort_rg = ft.RadioGroup(
                    content=ft.Column(
                        spacing=0,
                        scale=ft.Scale(scale=0.75),
                        controls=[
                            ft.Radio(label="昇順", value="asc"), 
                            ft.Radio(label="降順", value="desc")
                        ]
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
                    suffix_icon=ft.IconButton(
                        icon=ft.Icons.BACKSPACE, 
                        scale=ft.Scale(scale=0.75), 
                        opacity=0.5,
                    ),
                    expand=True,
                    
                )
                def build_row_cont(row):
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
                            ],
                        ),
                    )
                    def _on_target_click(e, cid=cid, name=name, rk=rk, cont=cont):
                        nonlocal selected_target_id
                        selected_target_id = cid
                        selected_target_text.value = f"{cid} [{rk}] {name}"
                        selected_target_text.update()
                        for c in target_containers:
                            c.bgcolor = None
                            try:
                                c.content.controls[0].color = None
                                c.content.controls[2].color = None
                                c.content.controls[4].color = None
                                c.content.controls[5].color = None
                                c.content.controls[6].color = None
                            except Exception:
                                pass
                            c.update()
                        cont.bgcolor = ft.Colors.YELLOW_100
                        try:
                            cont.content.controls[0].color = ft.Colors.BLACK
                            cont.content.controls[2].color = ft.Colors.BLACK
                            cont.content.controls[4].color = ft.Colors.BLACK
                            cont.content.controls[5].color = ft.Colors.BLACK
                            cont.content.controls[6].color = ft.Colors.BLACK
                        except Exception:
                            pass
                        cont.update()
                    cont.on_click = _on_target_click
                    return cont
                def refresh_lv(e=None, rk=rk, lv=lv, sort_dd=sort_dd, sort_rg=sort_rg, search_tf=search_tf):
                    rows = all_cards_by_rank.get(rk, [])
                    q = (search_tf.value or "").strip().lower()
                    key = sort_dd.value or "id"
                    order_desc = (sort_rg.value == "desc")
                    # フィルタ
                    filtered = []
                    for row in rows:
                        name = (row[2] or "").lower()
                        if q == "" or q in name:
                            filtered.append(row)
                    # ソート
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
                    # 再構築
                    lv.controls.clear()
                    for row in filtered:
                        cont = build_row_cont(row)
                        lv.controls.append(cont)
                        target_containers.append(cont)
                    if len(lv.controls) == 0:
                        lv.controls.append(ft.Container(padding=ft.Padding.all(8), content=ft.Text("対象が見つかりません")))
                # sort_ui に実際のコントロールを渡す
                sort_ui = ft.Row(
                    spacing=4,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[sort_dd, sort_rg, search_tf],
                )
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
                            spacing=1,
                            controls=[
                                sort_ui, 
                                ft.Divider(height=1), 
                                header, 
                                ft.Divider(height=1), 
                                lv
                            ],
                        ), 
                    ),
                )
                # 初期表示を構築
                # イベントに bind
                sort_dd.on_select = refresh_lv      #選んだ時
                sort_rg.on_change = refresh_lv      #切り替わったとき
                search_tf.on_submit = refresh_lv    #入力後にEnterを押したとき
                # クリアボタンの挙動を設定（クリックで入力を消して即時リフレッシュ）
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
