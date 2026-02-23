import json
import os
from pathlib import Path

from dotenv import load_dotenv
from googleapiclient.discovery import build  # type: ignore[import-untyped]

load_dotenv(".env")


class YoutubeAPI:
    def __init__(self,api_key):
        self.youtube_api = build("youtube", "v3", developerKey=api_key)

    def youtube_search(self, query: str):
        search_res = self.youtube_api.search().list(
            q=query,
            part="id,snippet",
            maxResults=10,
        ).execute()
        video_ids = []
        for item in search_res.get("items", []):
            if item["id"]["kind"] == "youtube#video":
                video_ids.append(item["id"]["videoId"])
        return ",".join(video_ids)

    def video(self, video_ids):
        video_list_res = self.youtube_api.videos().list(
            part="snippet,statistics",
            id=video_ids,
        ).execute()
        r= []
        for item in video_list_res.get("items", []):
            print(item)
            r.append({"video_id":item['id'],
            "title":item['snippet']['title'],
            "channelTitle":item['snippet']['channelTitle'],
            "commentCount":item['statistics']['commentCount'
            ]})
            print(f"{video_ids}.json 파일이 생성되었습니다.")
        return r

if __name__ == "__main__":
    DEVELOPER_KEY = os.getenv("YOUTUBE_API_KEY")
    api = YoutubeAPI(DEVELOPER_KEY)
    video_ids = api.youtube_search("업무 자동화")
    r_video = api.video(video_ids)
    for item in r_video:
        print(item)
