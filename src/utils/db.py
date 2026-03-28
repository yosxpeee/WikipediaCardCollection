import sqlite3
from utils.utils import rank_to_rankid

def initialize_db():
    """DB初期化"""
    conn = sqlite3.connect('cards.db')
    cursor = conn.cursor()
    # ファイルがない、ファイルがあってもテーブルがない場合は新規作成する
    # IDは数値、それ以外は全部文字列    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gacha_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pageId INTEGER NOT NULL,
            title TEXT NOT NULL,
            pageUrl TEXT NOT NULL,
            imageUrl TEXT NOT NULL,
            rank TEXT NOT NULL,
            quality TEXT NOT NULL,
            isSozai INTEGER NOT NULL,
            extract TEXT NOT NULL,
            HP TEXT NOT NULL,
            ATK TEXT NOT NULL,
            DEF TEXT NOT NULL,
            favorite INTEGER NOT NULL DEFAULT 0,
            resourceATK TEXT NOT NULL,
            resourceDEF TEXT NOT NULL,
            resourceRANK TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_cards(cards):
    """カード保存"""
    conn = sqlite3.connect('cards.db')
    cursor = conn.cursor()
    # カードがかぶっても関係なく新しく追加していく
    for card in cards:
        cursor.execute('''
            INSERT INTO gacha_cards (pageId, title, pageUrl, imageUrl, rank, quality, isSozai, extract, HP, ATK, DEF, favorite, resourceATK, resourceDEF, resourceRANK) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (card['pageId'], card['title'], card['pageUrl'], card['imageUrl'], rank_to_rankid(card['rank']), card['quality'], card['isSozai'], card['extract'], card['HP'], card['ATK'], card['DEF'], 0, card['resourceATK'], card['resourceDEF'], rank_to_rankid(card['resourceRANK'])))
        try:
            card['id'] = cursor.lastrowid
        except Exception:
            pass
    conn.commit()
    # 断片化を防ぎたいのでバキュームする
    cursor.execute('''VACUUM''')
    conn.commit()
    conn.close()

def get_all_cards():
    """全件取得"""
    conn = sqlite3.connect('cards.db')
    cursor = conn.cursor()
    data = []
    sql = f"""SELECT * FROM gacha_cards"""
    cursor.execute(sql)
    for item in cursor:
        data.append(item)
    conn.close()
    return data

def get_cards_by_rankid(rankid, is_sozai=0):
    """指定ランクIDかつ素材フラグで絞り込み取得

    rankid: int (ランクID) - None を渡すとランク条件を無視
    is_sozai: 0/1
    """
    conn = sqlite3.connect('cards.db')
    cursor = conn.cursor()
    data = []
    if rankid is None:
        sql = f"""SELECT * FROM gacha_cards WHERE isSozai == {int(is_sozai)}"""
    else:
        sql = f"""SELECT * FROM gacha_cards WHERE rank == {int(rankid)} AND isSozai == {int(is_sozai)}"""
    cursor.execute(sql)
    for item in cursor:
        data.append(item)
    conn.close()
    return data

def get_cards_by_sozai(is_sozai=1):
    """素材フラグで絞り込み取得（isSozai=1 等）"""
    return get_cards_by_rankid(None, is_sozai)

def get_card_from_id(card_id):
    """指定idのデータ取得"""
    conn = sqlite3.connect('cards.db')
    cursor = conn.cursor()
    data = []
    sql = f"""SELECT * FROM gacha_cards WHERE id == {int(card_id)}"""
    cursor.execute(sql)
    for item in cursor:
        data.append(item)
    conn.close()
    return data

def get_card_from_pageid(pageid):
    """指定pageidのデータ取得"""
    conn = sqlite3.connect('cards.db')
    cursor = conn.cursor()
    data = []
    sql = f"""SELECT * FROM gacha_cards WHERE pageid == {int(pageid)}"""
    cursor.execute(sql)
    for item in cursor:
        data.append(item)
    conn.close()
    return data

def get_random_card_by_rank(rank):
    """指定ランクの中からランダムに1件取得"""
    conn = sqlite3.connect('cards.db')
    cursor = conn.cursor()
    data = []
    sql = f"""SELECT * FROM gacha_cards WHERE rank == {int(rank)} ORDER BY RANDOM() LIMIT 1"""
    cursor.execute(sql)
    for item in cursor:
        data.append(item)
    conn.close()
    return data

def update_favorite(card_id, value):
    """お気に入り状態の更新"""
    conn = sqlite3.connect('cards.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''UPDATE gacha_cards SET favorite = ? WHERE id = ?''', (int(value), int(card_id)))
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()

def rankup_card(target_id, next_rankid, atk, defence, hp, sozai_id):
    """カードのランクアップ"""
    conn = sqlite3.connect('cards.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''UPDATE gacha_cards SET rank = ?, HP= ?, ATK = ?, DEF = ? WHERE id = ?''',
            (str(next_rankid), str(hp), str(atk), str(defence), int(target_id))
        )
        cursor.execute(f"""DELETE FROM gacha_cards WHERE id = {int(sozai_id)}""")
        conn.commit()
    except Exception as e:
        print(e)
    conn.close()