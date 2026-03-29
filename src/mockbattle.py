import flet as ft
import asyncio
from utils.db import get_cards_by_rankid, get_random_card_by_rank, get_card_from_id, get_cards_by_favorite
from utils.ui import create_card_image
from utils.utils import rank_to_rankid, rankid_to_rank, calc_damage

class MockBattle:
    def __init__(self, page):
        """初期化"""
        self.page = page
        # ローディングオーバーレイの参照を保持(図鑑のものを使いまわし)
        self.loading_overlay = page.overlay[1]
    def popup_mock_battle_dialog(self, player_id, npc_id):
        """模擬戦のダイアログ表示"""
        def create_card_image_from_id(data):
            rank = rankid_to_rank(data[0][5], 0)
            rank_origin = rankid_to_rank(data[0][15], 0)
            data_for_image = {
                "id": data[0][0],
                "pageId": data[0][1],
                "title": data[0][2],
                "pageUrl": data[0][3],
                "imageUrl": data[0][4],
                "rank": rank,
                "quality": data[0][6],
                "isSozai": data[0][7],
                "extract": data[0][8],
                "HP": data[0][9],
                "ATK": data[0][10],
                "DEF": data[0][11],
                "favorite": data[0][12],
                "resourceATK": data[0][13],
                "resourceDEF": data[0][14],
                "resourceRANK": rank_origin,
            }
            return create_card_image(data_for_image, True, False), data_for_image
        async def mock_battle(player_data, npc_data):
            """模擬戦（非同期でUI更新しながら進行）"""
            player_hp = int(player_data["HP"])
            npc_hp = int(npc_data["HP"])
            # 参照しやすいようにバーオブジェクトを取得
            row = mock_battle_dialog.content.controls[0]
            player_bar = row.controls[0].controls[1]
            npc_bar = row.controls[2].controls[1]
            log_col = mock_battle_dialog.content.controls[1].content.controls[2]
            player_bar._max_hp = int(player_data["HP"]) if str(player_data["HP"]).isdigit() else int(player_data["HP"])
            npc_bar._max_hp = int(npc_data["HP"]) if str(npc_data["HP"]).isdigit() else int(npc_data["HP"])
            for turn in range(30):
                npc_dmg = calc_damage(player_data, npc_data, npc_hp)
                npc_hp -= int(npc_dmg)
                if npc_hp <= 0:
                    npc_hp = 0
                    npc_bar.value = 0.0
                    msg = f"Turn {turn+1}: プレイヤーの攻撃、NPCへ{int(npc_dmg)}ダメージを与えた。(NPCの残HP: 0)"
                    log_col.controls.append(ft.Text(msg))
                    msg = f"Turn {turn+1}: プレイヤーの勝利！！"
                    log_col.controls.append(ft.Text(msg))
                    self.page.update()
                    break
                else:
                    max_hp = getattr(npc_bar, '_max_hp', None) or int(npc_data["HP"])
                    npc_bar.value = max(0.0, float(npc_hp) / float(max_hp))
                    msg = f"Turn {turn+1}: プレイヤーの攻撃、NPCへ{int(npc_dmg)}ダメージを与えた。(NPCの残HP: {npc_hp})"
                    log_col.controls.append(ft.Text(msg))
                    self.page.update()
                await asyncio.sleep(0.15)
                player_dmg = calc_damage(npc_data, player_data, player_hp)
                player_hp -= int(player_dmg)
                if player_hp <= 0:
                    player_hp = 0
                    player_bar.value = 0.0
                    msg = f"Turn {turn+1}: NPCの攻撃、プレイヤーへ{int(player_dmg)}のダメージを与えた。(プレイヤーの残HP: 0)"
                    log_col.controls.append(ft.Text(msg))
                    msg = f"Turn {turn+1}: NPCの勝利！！"
                    log_col.controls.append(ft.Text(msg))
                    self.page.update()
                    break
                else:
                    max_hp = getattr(player_bar, '_max_hp', None) or int(player_data["HP"])
                    player_bar.value = max(0.0, float(player_hp) / float(max_hp))
                    msg = f"Turn {turn+1}: NPCの攻撃、プレイヤーへ{int(player_dmg)}のダメージを与えた。(Playerの残HP: {player_hp})"
                    log_col.controls.append(ft.Text(msg))
                    self.page.update()
                await asyncio.sleep(0.15)
        if player_id == -1:
            return
        if npc_id == -1:
            return
        #プレイヤーカードの取得
        player_card, player_data = create_card_image_from_id(get_card_from_id(player_id))
        npc_card, npc_data = create_card_image_from_id(get_card_from_id(npc_id))
        mock_battle_dialog = ft.AlertDialog(
            modal=True,
            expand=True,
            content_padding=ft.Padding.all(10),
            title=ft.Text("模擬戦"),
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=0,
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Container(
                                        width=320,
                                        height=480,
                                        content=ft.Column(
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                            expand=True,
                                            controls=[
                                                player_card,
                                            ],
                                        ),
                                        bgcolor=ft.Colors.GREY_100, border_radius=5,
                                        padding=ft.Padding.all(5),
                                    ),
                                    ft.ProgressBar(width=320, value=1.0),
                                ],
                            ),
                            ft.Text("vs"),
                            ft.Column(
                                controls=[
                                    ft.Container(
                                        width=320,
                                        height=480,
                                        content=ft.Column(
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                            expand=True,
                                            controls=[
                                                npc_card,
                                            ],
                                        ),
                                        bgcolor=ft.Colors.GREY_100, border_radius=5,
                                        padding=ft.Padding.all(5),
                                    ),
                                    ft.ProgressBar(width=320, value=1.0),
                                ],
                            ),
                        ],
                    ),
                    ft.Container(
                        width=640,
                        height=300,
                        bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.GREY),
                        content=ft.Column(
                            spacing=0,
                            controls=[
                                ft.Text("＜＜＜戦闘ログ＞＞＞"),
                                ft.Divider(height=1),
                                ft.ListView(
                                    width=640,
                                    height=280,
                                    spacing=0,
                                    auto_scroll=True,
                                    controls=[],
                                ),
                            ],
                        ),
                    ),
                ],
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self.page.pop_dialog())
            ]
        )
        self.page.show_dialog(mock_battle_dialog)
        # バトルを非同期タスクとして開始（UI スレッドをブロックしない）
        try:
            asyncio.create_task(mock_battle(player_data, npc_data))
        except Exception:
            # フォールバック（同期呼び出し）
            import threading
            threading.Thread(target=lambda: asyncio.run(mock_battle(player_data, npc_data))).start()
    async def create(self):
        """画面作成"""
        def select_npc_by_rank(rank):
            """対戦相手選択処理"""
            nonlocal selected_single_mock_npc_card_id
            random = get_random_card_by_rank(rank_to_rankid(rank))
            if len(random) == 0:
                self.page.show_dialog(ft.SnackBar(ft.Text(f"{rank}ランクのカードを所有していません。"), duration=1500))
            else:
                selected_single_mock_npc_card_id = random[0][0]
                selected_single_mock_npc_text.value = f"{random[0][0]} [{rank}] {random[0][2]}"
                selected_single_mock_npc_text.update()
        ####################
        # 処理開始
        ####################
        # ローディングオーバーレイを表示
        self.loading_overlay.visible = True
        self.page.update()
        #各ページの選択カード格納場所
        selected_single_mock_player_card_id = -1
        selected_single_mock_npc_card_id    = -1
        try:
            ########################################
            # 模擬戦（シングル）のページ作成
            ########################################
            # DB からカードを非同期で取得（ランクごとに分割して取得）
            ranks = ["LR", "UR", "SSR", "SR", "R", "UC", "C", "★"]
            # ランクごとにDBから必要な行だけ取得してメモリを分割する
            all_cards_by_rank = {}
            for rk in ranks:
                if rk == "★":
                    rows = await asyncio.to_thread(get_cards_by_favorite)
                else:
                    rid = rank_to_rankid(rk)
                    rows = await asyncio.to_thread(get_cards_by_rankid, rid, 0)
                all_cards_by_rank[rk] = rows
            # 表示用テキスト
            selected_single_mock_player_text = ft.Text("",no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS, bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.GREY_500))
            selected_single_mock_npc_text = ft.Text("",no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS, bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.ORANGE))
            # コンテナ参照リスト（ハイライト更新用）
            target_containers = []
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
                    rank = rankid_to_rank(row[5], row[7])
                    cont = ft.Container(
                        padding=ft.Padding(top=0, left=6, right=6, bottom=0),
                        bgcolor=None,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(str(cid).ljust(8, " "), font_family="Consolas"),
                                ft.Container(width=10),
                                ft.Text(name, expand=True, tooltip=f"[{rank}] {name}", no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Container(width=10),
                                ft.Text(str(hp).ljust(5, " "), font_family="Consolas"),
                                ft.Text(str(atk).ljust(5, " "), font_family="Consolas"),
                                ft.Text(str(deff).ljust(5, " "), font_family="Consolas"),
                            ],
                        ),
                    )
                    def _on_target_click(e, cid=cid, name=name, rk=rk, cont=cont):
                        nonlocal selected_single_mock_player_card_id
                        selected_single_mock_player_card_id = cid
                        selected_single_mock_player_text.value = f"{cid} [{rk}] {name}"
                        selected_single_mock_player_text.update()
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
            # 模擬戦のページ本体
            single_mock = ft.Column(
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
                                    colors=[ft.Colors.PRIMARY_CONTAINER, ft.Colors.ON_PRIMARY, ft.Colors.PRIMARY_CONTAINER], 
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
                                                ft.Text("プレイヤー",weight=ft.FontWeight.BOLD), 
                                                ft.Divider(color=ft.Colors.GREY, height=1), 
                                                target_tab
                                            ],
                                        ),
                                    ),
                                    ft.Container(       #右(対戦相手の選択ボタン群)
                                        width=268,
                                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREY_900),
                                        alignment=ft.Alignment.TOP_CENTER,
                                        content=ft.Column(
                                            width=268,
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                            controls=[
                                                ft.Text("対戦相手",weight=ft.FontWeight.BOLD), 
                                                ft.Divider(color=ft.Colors.GREY, height=1), 
                                                ft.Button(ft.Text("  C級からランダムに選ぶ",font_family="Consolas"),on_click=lambda x:select_npc_by_rank("C")),
                                                ft.Button(ft.Text(" UC級からランダムに選ぶ",font_family="Consolas"),on_click=lambda x:select_npc_by_rank("UC")),
                                                ft.Button(ft.Text("  R級からランダムに選ぶ",font_family="Consolas"),on_click=lambda x:select_npc_by_rank("R")),
                                                ft.Button(ft.Text(" SR級からランダムに選ぶ",font_family="Consolas"),on_click=lambda x:select_npc_by_rank("SR")),
                                                ft.Button(ft.Text("SSR級からランダムに選ぶ",font_family="Consolas"),on_click=lambda x:select_npc_by_rank("SSR")),
                                                ft.Button(ft.Text(" UR級からランダムに選ぶ",font_family="Consolas"),on_click=lambda x:select_npc_by_rank("UR")),
                                                ft.Button(ft.Text(" LR級からランダムに選ぶ",font_family="Consolas"),on_click=lambda x:select_npc_by_rank("LR")),
                                            ]
                                        ),
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.Column(      #選択したアイテムの表示
                        spacing=0, 
                        controls=[
                            ft.Row(controls=[ft.Text("プレイヤー: "), selected_single_mock_player_text]),
                            ft.Row(controls=[ft.Text("対戦相手: "), selected_single_mock_npc_text]),
                        ]
                    ),
                    ft.Container(   #開始ボタン
                        width=738,
                        height=34,
                        padding=ft.Padding.all(0),
                        content=ft.Button(
                            "模擬戦開始", 
                            on_click=lambda x:self.popup_mock_battle_dialog(selected_single_mock_player_card_id, selected_single_mock_npc_card_id)
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
        return single_mock
