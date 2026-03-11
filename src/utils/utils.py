import requests

HEADER = {
    "Content-Type":"application/json", 
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
}

def doApi(url):
    response = requests.get(url, headers=HEADER)
    response.raise_for_status()  # エラー時にすぐ分かる
    return response