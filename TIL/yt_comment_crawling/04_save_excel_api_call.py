import os
from collections.abc import Sequence
from typing import Any, TypedDict, cast
import pandas as pd

from dotenv import load_dotenv
from googleapiclient.discovery import Resource, build  # type: ignore[import-untyped]
from googleapiclient.errors import HttpError  # type: ignore[import-untyped]

from icecream import ic


load_dotenv(".env")


class CommentItem(TypedDict):
    comment_id: str
    text: str
    author: str


class CrawledCommentItem(CommentItem):
    video_id: str
    video_link: str
    title: str
    channelTitle: str


class YoutubeAPI:
    def __init__(self, api_key: str):
        self.youtube_api: Resource = cast(
            Resource, build("youtube", "v3", developerKey=api_key)
        )

    def video_search_list(self, query: str, max_results: int = 10) -> str:
        search_res: dict[str, Any] = cast(
            dict[str, Any],
            self.youtube_api.search()
            .list(
            q=query,
            part="id,snippet",
            maxResults=max_results,
        )
            .execute(),
        )
        video_ids: list[str] = []
        for item in cast(list[dict[str, Any]], search_res.get("items", [])):
            if item["id"]["kind"] == "youtube#video":
                video_ids.append(item["id"]["videoId"])
        return ",".join(video_ids)

    def video(self, video_ids: str) -> list[dict[str, str]]:
        video_list_res: dict[str, Any] = cast(
            dict[str, Any],
            self.youtube_api.videos().list(
            part="snippet,statistics",
            id=video_ids,
        ).execute(),
        )
        videos: list[dict[str, str]] = []
        for item in cast(list[dict[str, Any]], video_list_res.get("items", [])):
            videos.append(
                {
                    "video_id": item["id"],
                    "title": item["snippet"]["title"],
                    "channelTitle": item["snippet"]["channelTitle"],
                    "commentCount": item["statistics"]["commentCount"],
                }
            )
        return videos

    def comment(self, video_id: str, max_cnt: int = 10) -> list[CommentItem]:
        comment_list_res: dict[str, Any] = cast(
            dict[str, Any],
            self.youtube_api.commentThreads().list(
            videoId=video_id,
            part="id,replies,snippet",
            maxResults=max_cnt,
        ).execute(),
        )
        comments: list[CommentItem] = []
        for comment in cast(list[dict[str, Any]], comment_list_res.get("items", [])):
            snippet = comment["snippet"]["topLevelComment"]["snippet"]
            comments.append(
                {
                    "comment_id": comment["id"],
                    "text": snippet["textOriginal"],
                    "author": snippet["authorDisplayName"],
                }
            )
        return comments

    def save_to_excel(
        self, search_results: Sequence[dict[str, Any]], filename: str
    ) -> None:
        df: pd.DataFrame = pd.DataFrame(search_results)
        df.to_excel(filename, index=False)

    def crawl_comment_by_keyword(
        self, keyword: str, video_max_cnt: int = 5
    ) -> list[CrawledCommentItem]:
        video_ids: str = self.video_search_list(keyword, video_max_cnt)
        r_video: list[dict[str, str]] = self.video(video_ids)
        all_comments: list[CrawledCommentItem] = []

        for video in r_video:
            cnt = int(video["commentCount"])
            if cnt > 100:
                cnt = 100
            try:
                comment_list = self.comment(video["video_id"], cnt)
            except HttpError as e:
                # 댓글이 비활성화된 영상(commentsDisabled)은 건너뛴다.
                if getattr(e, "resp", None) and e.resp.status == 403:
                    ic(
                        "댓글 수집 스킵",
                        {
                            "video_id": video["video_id"],
                            "reason": "commentsDisabled or forbidden",
                        },
                    )
                    continue
                raise

            video_link = f"https://www.youtube.com/watch?v={video['video_id']}"
            for comment in comment_list:
                all_comments.append(
                    {
                        **comment,
                        "video_id": video["video_id"],
                        "video_link": video_link,
                        "title": video["title"],
                        "channelTitle": video["channelTitle"],
                    }
                )

        return all_comments
            

if __name__ == "__main__":
    DEVELOPER_KEY: str | None = os.getenv("YOUTUBE_API_KEY")
    if DEVELOPER_KEY is None:
        raise ValueError("YOUTUBE_API_KEY가 설정되지 않았습니다.")
    api = YoutubeAPI(DEVELOPER_KEY)
    
    # for item in r_video:
    #     ic(item)
    # comment_results=  api.comment("obhyzqJQd9k",61)
    # api.save_to_excel(comment_results, "comment_results.xlsx")
    keyword = "코카콜라"
    l= api.crawl_comment_by_keyword(keyword,video_max_cnt=10)
    api.save_to_excel(l, f"{keyword}.xlsx")
