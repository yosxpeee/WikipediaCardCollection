import asyncio
from utils.utils import fetch_json, debug_print

# APIエンドポイントのベースURLを定義（必要に応じて）
WIKIPEDIA_BASE = "https://ja.wikipedia.org/w/api.php"
WIKIRANK_BASE = "https://api.wikirank.net/api.php"
WIKIPEDIA_SUMMARY_BASE = "https://ja.wikipedia.org/api/rest_v1/page/summary/"

async def fetch_random_wiki_articles(debug_mode: bool, count: int) -> list:
    """Wikipediaからランダムな記事のリストを取得する。"""
    random_url = f"{WIKIPEDIA_BASE}?format=json&action=query&list=random&rnnamespace=0&rnlimit={count}"
    debug_print(debug_mode, f"get random url: {random_url}")
    try:
        j = await fetch_json(debug_mode, random_url)
        if "error" in j or j == {}:
            debug_print(debug_mode, f"エラーデータ (Random): {j}")
            return []
        return j.get("query", {}).get("random", [])
    except Exception as e:
        debug_print(debug_mode, f"例外発生 (Random): error={e}")
        return []

async def fetch_wikirank_data(debug_mode: bool, title_quote: str) -> dict:
    """WikiRank APIから指定されたタイトルのランクデータを取得する。"""
    rank_url = f"{WIKIRANK_BASE}?name={title_quote}&lang=ja"
    debug_print(debug_mode, f"get rank data url: {rank_url}")
    try:
        j = await fetch_json(debug_mode, rank_url)
        if j.get("result", "") == "not found":
            debug_print(debug_mode, f"エラーデータ (WikiRank): {j}")
            return {}
        return j
    except Exception as e:
        debug_print(debug_mode, f"例外発生 (WikiRank): error={e}")
        return {}

async def fetch_wiki_info_data(debug_mode: bool, title_quote: str) -> dict:
    """Wikipedia APIから記事の基本情報（画像、ページプロパティなど）を取得する。"""
    # 必要なプロパティを全て含めるようにURLを構築
    info_url = f"{WIKIPEDIA_BASE}?format=json&action=query&titles={title_quote}&prop=info%7Cpageimages%7Cpageprops%7Cpageviews%7Ccategories&inprop=url%7Ctalkid&pithumbsize=600"
    debug_print(debug_mode, f"get info data url: {info_url}")
    try:
        return await fetch_json(debug_mode, info_url)
    except Exception as e:
        debug_print(debug_mode, f"例外発生 (Info): error={e}")
        return {}

async def fetch_wiki_summary(debug_mode: bool, title_quote: str) -> str:
    """Wikipedia REST APIから記事の概要（Extract）を取得する。"""
    summary_url = f"{WIKIPEDIA_SUMMARY_BASE}{title_quote}"
    debug_print(debug_mode, f"get summary url: {summary_url}")
    try:
        j = await fetch_json(debug_mode, summary_url)
        if "status" in j:
            debug_print(debug_mode, f"エラーデータ (Summary): {j}")
            return "ERROR"
        return j.get("extract", "")
    except Exception as e:
        debug_print(debug_mode, f"例外発生 (Summary): error={e}")
        return "ERROR"