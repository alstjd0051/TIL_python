import os
from dotenv import load_dotenv
from googleapiclient.discovery import build  # type: ignore[import-untyped]

load_dotenv(".env")

DEVELOPER_KEY = os.getenv("YOUTUBE_API_KEY")


def youtube_search(query: str):
    youtube_api = build("youtube", "v3", developerKey=DEVELOPER_KEY)
    search_res = youtube_api.search().list(
        q=query,
        part="id,snippet",
        maxResults=10,
    ).execute()
    for item in search_res.get("items", []):
        print(item)

if __name__ == "__main__":
    youtube_search("업무 자동화")