import sqlite3
from utils.utils import rank_to_rankid

def initialize_db():
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
            extract REAL NOT NULL,
            HP TEXT NOT NULL,
            ATK TEXT NOT NULL,
            DEF TEXT NOT NULL,
            favorite INTEGER NOT NULL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def save_cards(cards):
    conn = sqlite3.connect('cards.db')
    cursor = conn.cursor()
    # カードがかぶっても関係なく新しく追加していく
    for card in cards:
        cursor.execute('''
            INSERT INTO gacha_cards (pageId, title, pageUrl, imageUrl, rank, quality, isSozai, extract, HP, ATK, DEF, favorite) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (card['pageId'], card['title'], card['pageUrl'], card['imageUrl'], rank_to_rankid(card['rank']), card['quality'], card['isSozai'], card['extract'], card['HP'], card['ATK'], card['DEF'], 0))
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
    conn = sqlite3.connect('cards.db')
    cursor = conn.cursor()
    data = []
    sql = f"""SELECT * FROM gacha_cards"""
    cursor.execute(sql)
    for item in cursor:
        data.append(item)
    conn.close()
    return data

def update_favorite(card_id, value):
    conn = sqlite3.connect('cards.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''UPDATE gacha_cards SET favorite = ? WHERE id = ?''', (int(value), int(card_id)))
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()