import flet as ft
import asyncio
import random
import json

from utils.utils import RANK_TABLE, debug_print, rankid_to_rank, rank_to_rankid, calc_status, create_card_image_data, calc_damage
from utils.db import get_card_from_id, rankup_card, get_cards_by_rankid, get_cards_by_sozai, get_cards_by_favorite
from utils.ui import create_ranked_tabs, create_sortie_formation_image

class Sortie:
    def __init__(self, page):
        """初期化"""
        self.page = page
        # ローディングオーバーレイの参照を保持(図鑑のものを使いまわし)
        self.loading_overlay = page.overlay[1]
        self.current_select_card = {}
        self.current_formation_no = -1
        self.current_formation_dialog = None
        self.current_formation = [{},{},{},{},{},{}]
        self.current_enemies_formation = [{},{},{},{},{},{}]
        self.accordion_opened = "NORMAL"
    async def create(self):
        """画面作成"""
        def _set_current_formation(no):
            """編成しようとしている編隊番号を記憶"""
            self.current_formation_no = no
        def _load_sortie_formation_image(data, num):
            """編成用カードイメージをロードする"""
            sortie_tab.controls[3].controls[0].controls[0].controls[num].content = create_sortie_formation_image(data, False)
            self.page.update()
        def _load_sortie_formation_blank(num):
            """編成用カード(未配属)をロードする"""
            sortie_tab.controls[3].controls[0].controls[0].controls[num].content = ft.Text("未配属")
            self.page.update()
        def _create_formation_dialog():
            """編成用画面のダイアログ作成"""
            formation_dialog = ft.AlertDialog(
                modal=True,
                title=f"編成：{self.current_formation_no+1}",
                content=ft.Container(
                    width=700,
                    expand=True,
                    content=create_ranked_tabs(ranks, all_cards_by_rank, on_select_callback=_on_target_selected),
                ),
                actions=[
                    self.formation_close_button,
                    self.formation_clear_button,
                    self.formation_ok_button,
                ],
            )
            self.current_formation_dialog = formation_dialog
        def _create_blank_panel(no):
            """編成の空パネル作成"""
            return ft.Container(
                width=300,
                height=100,
                bgcolor=ft.Colors.ON_PRIMARY,
                content=ft.Text("未配置"),
                border_radius=8,
                border=ft.Border.all(1, color=ft.Colors.GREY),
                on_click=lambda x:{
                    _set_current_formation(no),
                    _create_formation_dialog(),
                    self.page.show_dialog(self.current_formation_dialog),
                },
            )
        def _expansion_tile_control(level, toggle):
            """"アコーディオンメニュー制御"""
            if toggle:
                for item in sortie_tab.controls[3].controls[1].controls:
                    if item.title != level:
                        item.expanded = False
                    else:
                        self.accordion_opened = level
            else:
                if level == self.accordion_opened:
                    for item in sortie_tab.controls[3].controls[1].controls:
                        if item.title == level:
                            item.expanded = True
        def _create_formation_grid(formation_data, isEnemy):
            """戦闘画面用の編成表示"""
            data_images = []
            for info in formation_data:
                image = create_sortie_formation_image(info, isEnemy)
                data_images.append(image)
            data = []
            for image in data_images:
                if isEnemy:
                    data.append(
                        ft.Row(
                            expand=True,
                            spacing=1,
                            controls=[
                                ft.RotatedBox(
                                    quarter_turns=3,
                                    content=ft.ProgressBar(
                                        width=100,
                                        height=5,
                                        bar_height=5,
                                        value=1.0,
                                        color=ft.Colors.BLUE,
                                    ),
                                ),
                                ft.Container(
                                    width=16,
                                    height=20,
                                ),
                                image,
                            ],
                        ),
                    )
                else:
                    data.append(
                        ft.Row(
                            expand=True,
                            spacing=1,
                            controls=[
                                image,
                                ft.RotatedBox(
                                    quarter_turns=3,
                                    content=ft.ProgressBar(
                                        width=100,
                                        height=5,
                                        bar_height=5,
                                        value=1.0,
                                        color=ft.Colors.BLUE,
                                    ),
                                ),
                            ],
                        ),
                    )
            return ft.GridView(
                width=200,
                height=606,
                child_aspect_ratio=2,
                runs_count=1,
                run_spacing=0,
                spacing=1,
                controls=[
                    data[0],
                    data[1],
                    data[2],
                    data[3],
                    data[4],
                    data[5],
                ],
            )
        def _start_battle(data, title):
            """戦闘ダイアログを表示する"""
            async def _sortie(player_data, enemy_data):
                """戦闘処理"""
                def append_log(s):
                    """戦闘ログ書き込み"""
                    log_list.controls.append(ft.Text(s))
                    self.page.update()
                def get_player_pb(idx):
                    """進行中のプログレスバー参照取得(プレイヤー側)"""
                    try:
                        return grid_player.controls[idx].controls[1].content
                    except Exception:
                        return None
                def get_enemy_pb(idx):
                    """進行中のプログレスバー参照取得(敵側)"""
                    try:
                        return grid_enemy.controls[idx].controls[0].content
                    except Exception:
                        return None
                def mark_dead_image(isEnemy, idx):
                    """指定スロットのカード画像を半透明オーバーレイと赤×印を重ねたものに差し替える"""
                    try:
                        if isEnemy:
                            row = grid_enemy.controls[idx]
                            img_index = 2
                            left = 0
                            top = 0
                        else:
                            row = grid_player.controls[idx]
                            img_index = 0
                            left = -12
                            top = 0
                        if img_index >= len(row.controls):
                            return
                        img = row.controls[img_index]
                        if getattr(img, '_dead_overlay', False):
                            return
                        overlay = ft.Container(
                            width=200,
                            height=100,
                            left=left,
                            top=top,
                            bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.GREY)
                        )
                        x_icon = ft.Container(
                            width=200,
                            height=100,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(ft.CupertinoIcons.CLEAR_THICK, color=ft.Colors.RED, size=100),
                        )
                        stack = ft.Stack(
                            alignment=ft.Alignment.CENTER,
                            controls=[img, overlay, x_icon],
                        )
                        stack._dead_overlay = True
                        row.controls[img_index] = stack
                        try:
                            self.page.update()
                        except Exception:
                            pass
                    except Exception:
                        pass
                def update_pb_color(pb, pct):
                    """プログレスバーの色更新"""
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
                # 初期化
                await asyncio.sleep(0.2)
                log_list = battle_dialog.content.controls[1].content.controls[2]
                # 準備：最大HPと現在HPを収集
                p_max = [0]*6
                p_cur = [0]*6
                e_max = [0]*6
                e_cur = [0]*6
                for i in range(6):
                    pd = player_data[i] if i < len(player_data) else {}
                    ed = enemy_data[i] if i < len(enemy_data) else {}
                    p_max[i] = int(pd.get("HP", 0)) if pd != {} else 0
                    p_cur[i] = float(p_max[i])
                    e_max[i] = int(ed.get("HP", 0)) if ed != {} else 0
                    e_cur[i] = float(e_max[i])
                # 戦闘ループ（最大5ターン） -- 各位置ごとにプレイヤーi → 敵i の順で交互に行動
                winner = None
                for turn in range(1, 6):
                    append_log(f"--- ターン {turn} 開始 ---")
                    for i in range(6):
                        # プレイヤー i の行動
                        if p_cur[i] > 0 and p_max[i] > 0:
                            alive = [j for j in range(6) if e_cur[j] > 0 and e_max[j] > 0]
                            if not alive:
                                winner = "PLAYER"
                                break
                            tgt = random.choice(alive)
                            dmg, d_type = calc_damage(self.page.debug, player_data[i], enemy_data[tgt], e_cur[tgt])
                            e_cur[tgt] = max(0.0, e_cur[tgt] - dmg)
                            append_log(f"プレイヤー[{player_data[i].get('title','?')}] -> 敵[{enemy_data[tgt].get('title','?')}] : {dmg} ({d_type})")
                            pb = get_enemy_pb(tgt)
                            if pb is not None and e_max[tgt] > 0:
                                try:
                                    val = max(0.0, e_cur[tgt] / e_max[tgt])
                                    pb.value = val
                                    update_pb_color(pb, val)
                                except Exception:
                                    pass
                            # HP が 0 になったら画像にオーバーレイを付ける
                            if e_cur[tgt] == 0:
                                mark_dead_image(True, tgt)
                            self.page.update()
                            await asyncio.sleep(0.20)
                        # 敵 i の行動（プレイヤー i の行動後に行う）
                        if e_cur[i] > 0 and e_max[i] > 0:
                            alive_p = [j for j in range(6) if p_cur[j] > 0 and p_max[j] > 0]
                            if not alive_p:
                                winner = "ENEMY"
                                break
                            tgt_p = random.choice(alive_p)
                            dmg, d_type = calc_damage(self.page.debug, enemy_data[i], player_data[tgt_p], p_cur[tgt_p])
                            p_cur[tgt_p] = max(0.0, p_cur[tgt_p] - dmg)
                            append_log(f"敵[{enemy_data[i].get('title','?')}] -> プレイヤー[{player_data[tgt_p].get('title','?')}] : {dmg} ({d_type})")
                            pbp = get_player_pb(tgt_p)
                            if pbp is not None and p_max[tgt_p] > 0:
                                try:
                                    valp = max(0.0, p_cur[tgt_p] / p_max[tgt_p])
                                    pbp.value = valp
                                    update_pb_color(pbp, valp)
                                except Exception:
                                    pass
                            # HP が 0 になったら画像にオーバーレイを付ける
                            if p_cur[tgt_p] == 0:
                                mark_dead_image(False, tgt_p)
                            self.page.update()
                            await asyncio.sleep(0.20)
                    if winner == "PLAYER":
                        append_log("敵を全滅させました。プレイヤー勝利！")
                        break
                    if winner == "ENEMY":
                        append_log("編成が全滅しました。プレイヤー敗北…")
                        break
                # 判定（5ターン終了または早期終了）
                if winner is None:
                    p_alive = sum(1 for v in p_cur if v > 0)
                    e_alive = sum(1 for v in e_cur if v > 0)
                    if p_alive > e_alive:
                        winner = "PLAYER"
                    elif e_alive > p_alive:
                        winner = "ENEMY"
                    else:
                        p_hp_sum = sum(p_cur)
                        e_hp_sum = sum(e_cur)
                        if p_hp_sum > e_hp_sum:
                            winner = "PLAYER"
                        elif e_hp_sum > p_hp_sum:
                            winner = "ENEMY"
                        else:
                            winner = "ENEMY"
                append_log(f"--- 結果: { 'プレイヤー勝利' if winner== 'PLAYER' else 'プレイヤー敗北' } ---")
                battle_close_button.disabled = False
                self.page.update()
            #戦闘開始条件を満たしているかチェックする
            for chk_data in self.current_formation:
                if chk_data == {}:
                    self.page.show_dialog(ft.SnackBar(ft.Text(f"必ず6枚のカードすべてを編成してください。"), duration=1500))
                    return
            num = 0
            for enemy_id in data["enemies"]:
                for enemy in master_data:
                    if enemy_id == enemy["pageid"]:
                        image_data = {
                            "id"   :enemy["pageid"],
                            "title":enemy["title"],
                            "rank" :rankid_to_rank(enemy["rank"], 0),
                            "image":enemy["imageUrl"],
                            "HP"   :enemy["HP"],
                            "ATK"  :enemy["ATK"],
                            "DEF"  :enemy["DEF"],
                        }
                        self.current_enemies_formation[num] = image_data
                        num = num + 1
                        break
            grid_player = _create_formation_grid(self.current_formation,         False)
            grid_enemy  = _create_formation_grid(self.current_enemies_formation, True )
            battle_close_button = ft.TextButton("close", disabled=True, on_click=lambda x:self.page.pop_dialog())
            battle_dialog = ft.AlertDialog(
                modal=True,
                title=f"出撃：{title}",
                content=ft.Column(
                    controls=[
                        ft.Row(
                            spacing=0,
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                grid_player,
                                ft.Container(
                                    width=11,
                                    height=10,
                                ),
                                ft.Container(
                                    width=70,
                                    alignment=ft.Alignment.CENTER,
                                    content=ft.Text("vs", size=60),
                                ),
                                grid_enemy,
                            ],
                        ),
                        ft.Container(
                            alignment=ft.Alignment.CENTER,
                            width=640,
                            height=180,
                            bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.GREY_100),
                            content=ft.Column(
                                spacing=0,
                                controls=[
                                    ft.Text("＜＜＜戦闘ログ＞＞＞"),
                                    ft.Divider(color=ft.Colors.GREY, height=1),
                                    ft.ListView(
                                        width=640,
                                        height=160,
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
                    battle_close_button
                ]
            )
            self.page.show_dialog(battle_dialog)
            asyncio.create_task(_sortie(self.current_formation, self.current_enemies_formation))
        def _create_level_ui(level, opened):
            """レベルデザイン"""
            return ft.ExpansionTile(
                width=320,
                title=level,
                expanded=opened,
                dense=True,
                expanded_alignment=ft.Alignment.TOP_LEFT,
                shape=ft.BeveledRectangleBorder(side=ft.BorderSide(width=2, color=ft.Colors.ON_SURFACE)),
                collapsed_shape=ft.BeveledRectangleBorder(side=ft.BorderSide(width=2, color=ft.Colors.ON_SURFACE)),
                controls=[
                    ft.Row(
                        controls=[
                            ft.FilledButton("Stage 1", on_click=lambda x:_start_battle(stage_data[level]["Stage 1"], f"{level} (Stage 1)")),
                            ft.Text(stage_data[level]["Stage 1"]["description"]),
                        ]
                    ),
                    ft.Row(
                        controls=[
                            ft.FilledButton("Stage 2", on_click=lambda x:_start_battle(stage_data[level]["Stage 2"], f"{level} (Stage 2)")),
                            ft.Text(stage_data[level]["Stage 2"]["description"]),
                        ]
                    ),
                    ft.Row(
                        controls=[
                            ft.FilledButton("Stage 3", on_click=lambda x:_start_battle(stage_data[level]["Stage 3"], f"{level} (Stage 3)")),
                            ft.Text(stage_data[level]["Stage 3"]["description"]),
                        ]
                    ),
                ],
                on_change=lambda x:_expansion_tile_control(level, x.data),
            )
        def _on_target_selected(id, name, rk, hp, atk, deff, img):
            """選んだカード"""
            #print(f"編成対象：{self.current_formation_no+1}")
            #print(f"{id}, {name}, {rk}, {hp}, {atk}, {deff}, {img}")
            self.current_select_card = {
                "id"   :id,
                "title":name,
                "rank" :rk,
                "image":img,
                "HP"   :hp,
                "ATK"  :atk,
                "DEF"  :deff,
            }
            return
        def _formation_dialog_common_update():
            """編成ダイアログの共通更新処理"""
            _set_current_formation(-1)
            self.current_select_card = {}
            with open('formation.json', 'w', encoding='utf-8') as f:
                json.dump(self.current_formation, f, indent=4, ensure_ascii=False)
            self.page.pop_dialog()
            self.page.update()
        def _cancel_load_formation():
            """編成ダイアログのキャンセルボタン"""
            _set_current_formation(-1)
            self.current_select_card = {}
            self.page.pop_dialog()
            self.page.update()
        def _clear_formation():
            """編成ダイアログのクリアボタン(編成から外す)"""
            self.current_formation[self.current_formation_no] = {}
            _load_sortie_formation_blank(self.current_formation_no)
            _formation_dialog_common_update()
        def _apply_load_formation():
            """編成ダイアログのOKボタン"""
            hit = False
            for num in range(len(self.current_formation)):
                #print(num)
                organized = self.current_formation[num]
                if organized == {}:
                    continue
                if organized["id"] == self.current_select_card["id"]:
                    if num != self.current_formation_no:
                        #現在の選択とは違うところに同じカードがある＝スワップ
                        if self.current_formation[self.current_formation_no] == {}:
                            #未配属と入れ替え
                            self.current_formation[num] = {}
                            _load_sortie_formation_blank(num)
                            self.current_formation[self.current_formation_no] = self.current_select_card
                            _load_sortie_formation_image(self.current_select_card, self.current_formation_no)
                        else:
                            #編成済みと入れ替え
                            tmp = self.current_formation[self.current_formation_no]
                            self.current_formation[self.current_formation_no] = self.current_select_card
                            _load_sortie_formation_image(self.current_select_card, self.current_formation_no)
                            self.current_formation[num] = tmp
                            _load_sortie_formation_image(tmp, num)
                    _formation_dialog_common_update()
                    hit = True
                    break
            #当てはまらなければ追加
            if hit == False:
                self.current_formation[self.current_formation_no] = self.current_select_card
                _load_sortie_formation_image(self.current_select_card, self.current_formation_no)
                _formation_dialog_common_update()
        ####################
        # 処理開始
        ####################
        # ローディングオーバーレイを表示
        self.loading_overlay.visible = True
        self.page.update()
        # ステージデータ読み出し
        with open('src/stage_data.json', 'r', encoding='utf-8') as f:
            stage_data = json.load(f)
        # 対戦相手のマスターデータ読み出し
        with open('src/enemy_master_data.json', 'r', encoding='utf-8') as f:
            master_data = json.load(f)
        # ダイアログのボタン作成
        self.formation_close_button = ft.TextButton(
            "キャンセル", 
            on_click=lambda e:{
                _cancel_load_formation()
            }
        )
        self.formation_clear_button = ft.TextButton(
            "外す", 
            on_click=lambda e:{
                _clear_formation()
            }
        )
        self.formation_ok_button = ft.TextButton(
            "編成する", 
            on_click=lambda e: {
                _apply_load_formation()
            }
        )
        # ランクごとにDBからカード一覧を取得
        ranks = ["LR", "UR", "SSR", "SR", "R", "UC", "C", "★"]
        all_cards_by_rank = {}
        for rk in ranks:
            if rk == "★":
                rows = await asyncio.to_thread(get_cards_by_favorite)
            else:
                rid = rank_to_rankid(rk)
                rows = await asyncio.to_thread(get_cards_by_rankid, rid, 0)
            all_cards_by_rank[rk] = rows
        try:
            await asyncio.sleep(1)
            sortie_tab = ft.Column(
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            ft.Container(
                                width=630,
                                border=ft.Border.all(width=2, color=ft.Colors.ON_SURFACE),
                                border_radius=8,
                                content=ft.Column(
                                    alignment=ft.MainAxisAlignment.START,
                                    horizontal_alignment=ft.CrossAxisAlignment.START,
                                    spacing=0,
                                    width=620,
                                    margin=ft.Margin.all(5),
                                    controls=[
                                        ft.Text("<<< 注意事項 >>>"),
                                        ft.Text("出撃には6枚のカードを編成すること（必須条件）。")
                                    ],
                                ),
                            ),
                        ],
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                alignment=ft.Alignment.CENTER,
                                width=300,
                                content=ft.Text("編成"),
                            ),
                            ft.Container(
                                alignment=ft.Alignment.CENTER,
                                width=320,
                                content=ft.Text("出撃先"),
                            ),
                        ],
                    ),
                    ft.Divider(height=1,),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Column(
                                alignment=ft.MainAxisAlignment.START,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.GridView(
                                        width=200,
                                        height=600,
                                        child_aspect_ratio=2,
                                        runs_count=1,
                                        run_spacing=0,
                                        spacing=0,
                                        controls=[
                                            # 編成変更用のトリガー付きコンテナをロードする
                                            _create_blank_panel(0),
                                            _create_blank_panel(1),
                                            _create_blank_panel(2),
                                            _create_blank_panel(3),
                                            _create_blank_panel(4),
                                            _create_blank_panel(5),
                                        ],
                                    ),
                                ],
                            ),
                            ft.Column(
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                width=320,
                                height=600,
                                controls=[
                                    _create_level_ui("NORMAL",    True ), #C
                                    _create_level_ui("HARD",      False), #UC
                                    _create_level_ui("VERY HARD", False), #R
                                    _create_level_ui("HARD CORE", False), #SR
                                    _create_level_ui("EXTREME",   False), #SSR
                                    _create_level_ui("INSANE",    False), #UR
                                    _create_level_ui("TORMENT",   False), #LR
                                    _create_level_ui("LUNATIC",   False), #LR+ (まともにやったら勝てないだろうからどうするかね)
                                ],
                            ),
                        ],
                    ),
                ],
            )
            # 以前に編成したデータをそっくり読みだして編成を再現する
            try:
                with open('formation.json', 'r', encoding='utf-8') as f:
                    self.current_formation = json.load(f)
                    #print(self.current_formation)
                    self.current_formation_no = 0
                    for data in self.current_formation:
                        #print(data)
                        if data != {}:
                            _load_sortie_formation_image(data, self.current_formation_no)
                        self.current_formation_no += 1
                    self.current_formation_no = -1
            except Exception as e:
                pass
        finally:
            # ローディングオーバーレイを非表示（例外が起きても必ず閉じる）
            try:
                self.loading_overlay.visible = False
                self.page.update()
            except Exception:
                pass
        # 他タブと雰囲気を揃えた淡い背景グラデーションでラップして返す
        view = ft.Stack(
            controls=[
                ft.ShaderMask(
                    content=ft.Container(
                        border=ft.Border.all(0),
                        width=738,
                        height=910,
                        alignment=ft.Alignment.CENTER,
                        bgcolor=ft.Colors.ON_PRIMARY,
                        content=None,
                    ),
                    blend_mode=ft.BlendMode.SRC_IN,
                    shader=ft.RadialGradient(
                        center=ft.Alignment.CENTER,
                        radius=0.5,
                        colors=[
                            ft.Colors.with_opacity(0.5, ft.Colors.ON_PRIMARY),
                            ft.Colors.with_opacity(0.5, ft.Colors.PRIMARY_CONTAINER),
                            ft.Colors.with_opacity(0.5, ft.Colors.ON_PRIMARY),
                            ft.Colors.with_opacity(0.5, ft.Colors.PRIMARY_CONTAINER),
                            ft.Colors.with_opacity(0.5, ft.Colors.ON_PRIMARY),
                        ],
                        stops=[0.2, 0.4, 0.6, 0.8, 1.0],
                        tile_mode=ft.GradientTileMode.REPEATED,
                    ),
                ),
                ft.Container(
                    content=sortie_tab,
                ),
            ],
        )
        return view
