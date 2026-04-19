# セットアップファイル
import json
import os

SETTINGS_FILE = "settings.json"

def load_settings():
    """settings.json から設定を読み込む"""
    default_settings = {
        "dark_theme"          : False,
        "volume"              : 0.0,
        "bgm_gacha"           : "",
        "bgm_zukan"           : "",
        "bgm_mockbattle"      : "",
        "bgm_mockbattle_fight": "",
        "bgm_powerup"         : "",
        "bgm_sortie"          : "",
        "bgm_sortie_fight"    : "",
        "bgm_sortie_reward"   : "",
        "bgm_achievements"    : "",
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # デフォルト値で補完
                for key, value in default_settings.items():
                    if key not in settings:
                        settings[key] = value
                return settings
        except Exception:
            pass
    return default_settings

def save_settings(settings):
    """設定を settings.json に保存"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        return True
    except Exception:
        return False

def get_dark_theme():
    """ダークテーマの設定を取得"""
    settings = load_settings()
    return settings.get("dark_theme", False)

def get_volume():
    """音量取得"""
    settings = load_settings()
    return settings.get("volume", 0.0)

def change_volume(value):
    """音量変更"""
    settings = load_settings()
    settings["volume"] = value
    save_settings(settings)
    return value

def toggle_dark_theme(value):
    """ダークテーマの切り替え（ON/OFF）"""
    settings = load_settings()
    settings["dark_theme"] = value
    save_settings(settings)
    return value