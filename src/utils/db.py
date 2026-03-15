import sqlite3
from utils.utils import rankToRankId

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
            isSozai TEXT NOT NULL,
            extract TEXT NOT NULL,
            HP TEXT NOT NULL,
            ATK TEXT NOT NULL,
            DEF TEXT NOT NULL
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
            INSERT INTO gacha_cards (pageId, title, pageUrl, imageUrl, rank, quality, isSozai, extract, HP, ATK, DEF) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (card['pageId'], card['title'], card['pageUrl'], card['imageUrl'], rankToRankId(card['rank']), card['quality'], card['isSozai'], card['extract'], card['HP'], card['ATK'], card['DEF']))
    # 断片化云々を防ぎたいのでバキュームする（毎回でなくてもいいか？）
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
