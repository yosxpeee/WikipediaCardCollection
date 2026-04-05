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
            """カードイメージ作成"""
            #Note:データ自体も欲しいので、utilsにある関数は呼ばず個別実装
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
            def update_pb_color(pb, pct):
                try:
                    if pct > 0.5:
                        pb.color = ft.Colors.BLUE
                    elif pct > 0.3:
                        pb.color = ft.Colors.YELLOW
                    elif pct > 0.1:
                        pb.color = ft.Colors.ORANGE
                    else:
                        pb.color = ft.Colors.RED
                except Exception:
                    pass

            # 初期色設定
            try:
                update_pb_color(player_bar, 1.0)
                update_pb_color(npc_bar, 1.0)
            except Exception:
                pass
            for turn in range(10):
                npc_dmg, type = calc_damage(self.page.debug, player_data, npc_data, npc_hp)
                npc_hp -= int(npc_dmg)
                if npc_hp <= 0:
                    npc_hp = 0
                    npc_bar.value = 0.0
                    update_pb_color(npc_bar, 0.0)
                    if type == "critical":
                        msg = f"Turn {turn+1}: [Critical] プレイヤーの攻撃、対戦相手へ{int(npc_dmg)}ダメージを与えた。(対戦相手の残HP: 0)"
                    else:
                        msg = f"Turn {turn+1}: プレイヤーの攻撃、対戦相手へ{int(npc_dmg)}ダメージを与えた。(対戦相手の残HP: 0)"
                    log_col.controls.append(ft.Text(msg))
                    self.page.update()
                    await asyncio.sleep(0.30)
                    msg = f"Turn {turn+1}: プレイヤーの勝利！！"
                    log_col.controls.append(ft.Text(msg, color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE))
                    self.page.update()
                    await asyncio.sleep(0.30)
                    break
                else:
                    max_hp = getattr(npc_bar, '_max_hp', None) or int(npc_data["HP"])
                    val = max(0.0, float(npc_hp) / float(max_hp))
                    npc_bar.value = val
                    update_pb_color(npc_bar, val)
                    if type == "critical":
                        msg = f"Turn {turn+1}: [Critical] プレイヤーの攻撃、対戦相手へ{int(npc_dmg)}ダメージを与えた。(対戦相手の残HP: {npc_hp})"
                    elif type == "avoid":
                        msg = f"Turn {turn+1}: プレイヤーの攻撃、対戦相手は攻撃を回避した。(対戦相手の残HP: {npc_hp})"
                    else:
                        msg = f"Turn {turn+1}: プレイヤーの攻撃、対戦相手へ{int(npc_dmg)}ダメージを与えた。(対戦相手の残HP: {npc_hp})"
                    log_col.controls.append(ft.Text(msg))
                    self.page.update()
                await asyncio.sleep(0.30)
                player_dmg, type = calc_damage(self.page.debug, npc_data, player_data, player_hp)
                player_hp -= int(player_dmg)
                if player_hp <= 0:
                    player_hp = 0
                    player_bar.value = 0.0
                    update_pb_color(player_bar, 0.0)
                    if type == "critical":
                        msg = f"Turn {turn+1}: [Critical] 対戦相手の攻撃、プレイヤーへ{int(player_dmg)}のダメージを与えた。(プレイヤーの残HP: 0)"
                    else:
                        msg = f"Turn {turn+1}: 対戦相手の攻撃、プレイヤーへ{int(player_dmg)}のダメージを与えた。(プレイヤーの残HP: 0)"
                    log_col.controls.append(ft.Text(msg))
                    self.page.update()
                    await asyncio.sleep(0.30)
                    msg = f"Turn {turn+1}: 対戦相手の勝利！！"
                    log_col.controls.append(ft.Text(msg, color=ft.Colors.WHITE, bgcolor=ft.Colors.RED))
                    self.page.update()
                    await asyncio.sleep(0.30)
                    break
                else:
                    max_hp = getattr(player_bar, '_max_hp', None) or int(player_data["HP"])
                    valp = max(0.0, float(player_hp) / float(max_hp))
                    player_bar.value = valp
                    update_pb_color(player_bar, valp)
                    if type == "critical":
                        msg = f"Turn {turn+1}: [Critical] 対戦相手の攻撃、プレイヤーへ{int(player_dmg)}のダメージを与えた。(プレイヤーの残HP: {player_hp})"
                    elif type == "avoid":
                        msg = f"Turn {turn+1}: 対戦相手の攻撃、プレイヤーは攻撃を回避した。(プレイヤーの残HP: {player_hp})"
                    else:
                        msg = f"Turn {turn+1}: 対戦相手の攻撃、プレイヤーへ{int(player_dmg)}のダメージを与えた。(プレイヤーの残HP: {player_hp})"
                    log_col.controls.append(ft.Text(msg))
                    self.page.update()
                await asyncio.sleep(0.30)
            # 10ターンかけても両方HPが残った場合はHPの多いほうを勝ちとする。HPも同じなら引き分け
            if player_hp != 0 and npc_hp != 0:
                if player_hp > npc_hp:
                    msg = f"判定：プレイヤーの勝利"
                    log_col.controls.append(ft.Text(msg, color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE))
                    await asyncio.sleep(0.30)
                elif player_hp < npc_hp:
                    msg = f"判定：対戦相手の勝利"
                    log_col.controls.append(ft.Text(msg, color=ft.Colors.WHITE, bgcolor=ft.Colors.RED))
                    await asyncio.sleep(0.30)
                else:
                    msg = f"判定：引き分け"
                    log_col.controls.append(ft.Text(msg, color=ft.Colors.WHITE, bgcolor=ft.Colors.GREY))
                    await asyncio.sleep(0.30)
            mock_battle_dialog.actions[0].disabled = False
            self.page.update()
        if player_id == -1:
            return
        if npc_id == -1:
            return
        # プレイヤーカードの取得
        player_card, player_data = create_card_image_from_id(get_card_from_id(player_id))
        # 対戦相手カードの取得
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
                                    ft.ProgressBar(width=320, value=1.0, color=ft.Colors.BLUE),
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
                                    ft.ProgressBar(width=320, value=1.0, color=ft.Colors.BLUE),
                                ],
                            ),
                        ],
                    ),
                    ft.Container(
                        width=640,
                        height=300,
                        bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.GREY_100),
                        content=ft.Column(
                            spacing=0,
                            controls=[
                                ft.Text("＜＜＜戦闘ログ＞＞＞"),
                                ft.Divider(color=ft.Colors.GREY, height=1),
                                ft.ListView(
                                    width=640,
                                    height=280,
                                    spacing=0,
                                    auto_scroll=True,
                                    scroll=ft.ScrollMode.AUTO,
                                    controls=[],
                                ),
                            ],
                        ),
                    ),
                ],
            ),
            actions=[
                ft.TextButton(
                    content="Close", 
                    on_click=lambda e: self.page.pop_dialog(),
                    disabled=True,
                )
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
            # 左側：ランク別タブの ListView を作成（共通化）
            from utils.ui import create_ranked_tabs
            def _on_player_selected(cid, name, rk, hp, atk, deff, img):
                nonlocal selected_single_mock_player_card_id
                selected_single_mock_player_card_id = cid
                selected_single_mock_player_text.value = f"{cid} [{rk}] {name}"
                selected_single_mock_player_text.update()
            target_tab = create_ranked_tabs(ranks, all_cards_by_rank, on_select_callback=_on_player_selected)
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
                                            spacing=0,
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
                                            spacing=0,
                                            controls=[
                                                ft.Text("対戦相手",weight=ft.FontWeight.BOLD), 
                                                ft.Divider(color=ft.Colors.GREY, height=1), 
                                                ft.Column(
                                                    margin=ft.Margin.all(10),
                                                    controls=[
                                                        ft.Button(ft.Text("  C級からランダムに選ぶ",font_family="Consolas"),on_click=lambda x:select_npc_by_rank("C")),
                                                        ft.Button(ft.Text(" UC級からランダムに選ぶ",font_family="Consolas"),on_click=lambda x:select_npc_by_rank("UC")),
                                                        ft.Button(ft.Text("  R級からランダムに選ぶ",font_family="Consolas"),on_click=lambda x:select_npc_by_rank("R")),
                                                        ft.Button(ft.Text(" SR級からランダムに選ぶ",font_family="Consolas"),on_click=lambda x:select_npc_by_rank("SR")),
                                                        ft.Button(ft.Text("SSR級からランダムに選ぶ",font_family="Consolas"),on_click=lambda x:select_npc_by_rank("SSR")),
                                                        ft.Button(ft.Text(" UR級からランダムに選ぶ",font_family="Consolas"),on_click=lambda x:select_npc_by_rank("UR")),
                                                        ft.Button(ft.Text(" LR級からランダムに選ぶ",font_family="Consolas"),on_click=lambda x:select_npc_by_rank("LR")),
                                                    ],
                                                ),
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
