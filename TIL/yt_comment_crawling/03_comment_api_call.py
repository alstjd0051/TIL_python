import os
from typing import Any, TypedDict
import json

from dotenv import load_dotenv
from googleapiclient.discovery import build  # type: ignore[import-untyped]
from icecream import ic


load_dotenv(".env")


class VideoItem(TypedDict):
    video_id: str
    title: str
    channelTitle: str
    commentCount: str


class CommentItem(TypedDict):
    comment_id: str
    text: str
    author: str


class YoutubeAPI:
    def __init__(self, api_key: str):
        self.youtube_api: Any = build("youtube", "v3", developerKey=api_key)

    def youtube_search(self, query: str) -> str:
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

    def video(self, video_ids: str) -> list[VideoItem]:
        video_list_res = self.youtube_api.videos().list(
            part="snippet,statistics",
            id=video_ids,
        ).execute()
        r: list[VideoItem] = []
        for item in video_list_res.get("items", []):
            r.append({"video_id":item['id'],
            "title":item['snippet']['title'],
            "channelTitle":item['snippet']['channelTitle'],
            "commentCount":item['statistics']['commentCount'
            ]})
        return r

    def comment(self, video_id: str, max_cnt: int = 10) -> list[CommentItem]:
        comment_list_res = self.youtube_api.commentThreads().list(
            videoId=video_id,
            part="id,replies,snippet",
            maxResults=max_cnt,
        ).execute()

        for comment in comment_list_res.get("items", []):
            snippet = comment['snippet']['topLevelComment']['snippet']
            map = {"videoId":video_id,"textOriginal":snippet['textOriginal'],"authorDisplayName":snippet['authorDisplayName']}
            ic(map)
            # ic(snippet)

if __name__ == "__main__":
    DEVELOPER_KEY: str | None = os.getenv("YOUTUBE_API_KEY")
    if DEVELOPER_KEY is None:
        raise ValueError("YOUTUBE_API_KEY가 설정되지 않았습니다.")
    api = YoutubeAPI(DEVELOPER_KEY)
    # video_ids = api.youtube_search("업무 자동화")
    # r_video = api.video(video_ids)
    # for item in r_video:
    #     ic(item)
    api.comment("obhyzqJQd9k",61)
