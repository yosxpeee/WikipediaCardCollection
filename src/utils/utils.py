import requests
import time

HEADER = {
    "Content-Type":"application/json", 
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
}

def doApi(url):
    while True:
        try:
            print(url)
            response = requests.get(url, headers=HEADER)
            response.raise_for_status()  # エラー時にすぐ分かる
            break
        except Exception as e:
            print(e)
            print("5秒待機してリトライします。")
            time.sleep(5)
    return response