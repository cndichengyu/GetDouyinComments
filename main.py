import asyncio
from datetime import datetime
from typing import Any
import os
import httpx
import pandas as pd
from tqdm import tqdm
from common import common
import requests
import re

url = "https://www.douyin.com/aweme/v1/web/comment/list/"
reply_url = url + "reply/"

with open('cookie.txt','r') as f:
    cookie = f.readline().strip()

# 抖音视频URL列表
video_urls = [
    "https://v.douyin.com/1iGjrccgq5I/",
    "https://v.douyin.com/dNSbOFi71pY/",
    "https://v.douyin.com/pGrLdrknufo/",
    "https://v.douyin.com/4XAc3ONhLVg/",
    "https://v.douyin.com/fX1BEmM8cs8/",
    "https://v.douyin.com/pccJTvWvW7w/"
]

# 从抖音URL中提取aweme_id
def get_aweme_id_from_url(url):
    try:
        # 跟随重定向获取实际URL
        response = requests.get(url, allow_redirects=True, timeout=10)
        actual_url = response.url
        
        # 从实际URL中提取aweme_id，支持video和note两种格式
        match = re.search(r'/(video|note)/(\d+)', actual_url)
        if match:
            return match.group(2)
        return None
    except Exception as e:
        print(f"解析URL {url} 失败: {e}")
        return None

async def get_comments_async(client: httpx.AsyncClient, aweme_id: str, cursor: str = "0", count: str = "50") -> dict[
    str, Any]:
    params = {"aweme_id": aweme_id, "cursor": cursor, "count": count, "item_type": 0}
    headers = {"cookie": cookie}
    params, headers = common(url, params, headers)
    response = await client.get(url, params=params, headers=headers)
    await asyncio.sleep(0.8)
    try:
        return response.json()
    except ValueError:
        # Return an empty dictionary if the response is not valid JSON.
        # Alternatively, you could raise an exception here to indicate that the cookies might be expired or invalid.
        return {}



async def fetch_all_comments_async(aweme_id: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=600) as client:
        cursor = 0
        all_comments = []
        has_more = 1
        with tqdm(desc="Fetching comments", unit="comment") as pbar:
            while has_more:
                response = await get_comments_async(client, aweme_id, cursor=str(cursor))
                comments = response.get("comments", [])
                if isinstance(comments, list):
                    all_comments.extend(comments)
                    pbar.update(len(comments))
                has_more = response.get("has_more", 0)
                if has_more:
                    cursor = response.get("cursor", 0)
                await asyncio.sleep(1)
        return all_comments


async def get_replies_async(client: httpx.AsyncClient, semaphore, aweme_id: str, comment_id: str, cursor: str = "0",
                            count: str = "50") -> dict:
    params = {"cursor": cursor, "count": count, "item_type": 0, "item_id": aweme_id, "comment_id": comment_id}
    headers = {"cookie": cookie}
    params, headers = common(reply_url, params, headers)
    async with semaphore:
        response = await client.get(reply_url, params=params, headers=headers)
        await asyncio.sleep(0.3)
        # print(response.text)
        try:
            return response.json()
        except ValueError:
            # Return an empty dictionary if the response is not valid JSON.
            # Alternatively, you could raise an exception here to indicate that the cookies might be expired or invalid.
            return {}


async def fetch_replies_for_comment(client: httpx.AsyncClient, semaphore, aweme_id: str, comment: dict, pbar: tqdm) -> list:
    comment_id = comment["cid"]
    has_more = 1
    cursor = 0
    all_replies = []
    while has_more and comment["reply_comment_total"] > 0:
        response = await get_replies_async(client, semaphore, aweme_id, comment_id, cursor=str(cursor))
        replies = response.get("comments", [])
        if isinstance(replies, list):
            all_replies.extend(replies)
        has_more = response.get("has_more", 0)
        if has_more:
            cursor = response.get("cursor", 0)
        await asyncio.sleep(0.5)
    pbar.update(1)
    return all_replies


async def fetch_all_replies_async(aweme_id: str, comments: list) -> list:
    all_replies = []
    async with httpx.AsyncClient(timeout=600) as client:
        semaphore = asyncio.Semaphore(10)  # 在这里创建信号量
        with tqdm(total=len(comments), desc="Fetching replies", unit="comment") as pbar:
            tasks = [fetch_replies_for_comment(client, semaphore, aweme_id, comment, pbar) for comment in comments]
            results = await asyncio.gather(*tasks)
            for result in results:
                all_replies.extend(result)
    return all_replies


def process_comments(comments: list[dict[str, Any]]) -> pd.DataFrame:
    data = [{
        "评论ID": c['cid'],
        "评论内容": c['text'],
        "评论图片": c['image_list'][0]['origin_url']['url_list'] if c['image_list'] else None,
        "点赞数": c['digg_count'],
        "评论时间": datetime.fromtimestamp(c['create_time']).strftime('%Y-%m-%d %H:%M:%S'),
        "用户昵称": c['user']['nickname'],
        "用户主页链接": f"https://www.douyin.com/user/{c['user']['sec_uid']}",
        "用户抖音号": c['user'].get('unique_id', '未知'),
        "用户签名": c['user'].get('signature', '未知'),
        "回复总数": c['reply_comment_total'],
        "ip归属":c['ip_label']
    } for c in comments]
    return pd.DataFrame(data)


def process_replies(replies: list[dict[str, Any]], comments: pd.DataFrame) -> pd.DataFrame:
    data = [
        {
            "评论ID": c["cid"],
            "评论内容": c["text"],
            "评论图片": c['image_list'][0]['origin_url']['url_list'] if c['image_list'] else None,
            "点赞数": c["digg_count"],
            "评论时间": datetime.fromtimestamp(c["create_time"]).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "用户昵称": c["user"]["nickname"],
            "用户主页链接": f"https://www.douyin.com/user/{c['user']['sec_uid']}",
            "用户抖音号": c['user'].get('unique_id', '未知'),
            "用户签名": c['user'].get('signature', '未知'),
            "回复的评论": c["reply_id"],
            "具体的回复对象": c["reply_to_reply_id"]
            if c["reply_to_reply_id"] != "0"
            else c["reply_id"],
            "回复给谁": comments.loc[comments['评论ID'] == c["reply_id"], '用户昵称'].values[0]
            if c["reply_to_reply_id"] == "0"
            else c["reply_to_username"],
            "ip归属":c.get('ip_label','未知')
        }
        for c in replies
    ]
    return pd.DataFrame(data)


def save(data: pd.DataFrame, filename: str):
    data.to_csv(filename, index=False)





# 存储所有视频的评论和回复
all_videos_comments = []
all_videos_replies = []

async def process_video(url):
    aweme_id = get_aweme_id_from_url(url)
    if not aweme_id:
        print(f"无法从URL {url} 提取aweme_id，跳过此视频")
        return
    
    print(f"处理视频 URL: {url}")
    print(f"提取到的 aweme_id: {aweme_id}")
    
    # 评论部分
    all_comments = await fetch_all_comments_async(aweme_id)
    print(f"Found {len(all_comments)} comments.")
    all_comments_ = process_comments(all_comments)
    
    # 添加视频信息到评论数据
    all_comments_['视频URL'] = url
    all_comments_['aweme_id'] = aweme_id
    all_comments_['评论类型'] = '一级评论'
    all_videos_comments.append(all_comments_)
    
    base_dir = f"data/v1/{aweme_id}"
    os.makedirs(base_dir, exist_ok=True)
    comments_file = os.path.join(base_dir, "comments.csv")
    save(all_comments_, comments_file)

    # 回复部分 如果不需要直接注释掉
    all_replies = await fetch_all_replies_async(aweme_id, all_comments)
    print(f"Found {len(all_replies)} replies")
    print(f"Found {len(all_replies) + len(all_comments)} in totals")
    all_replies = process_replies(all_replies, all_comments_)
    
    # 添加视频信息到回复数据
    all_replies['视频URL'] = url
    all_replies['aweme_id'] = aweme_id
    all_replies['评论类型'] = '二级评论'
    all_videos_replies.append(all_replies)
    
    replies_file = os.path.join(base_dir, "replies.csv")
    save(all_replies, replies_file)

async def main():
    for url in video_urls:
        await process_video(url)
        print("\n" + "="*50 + "\n")
    
    # 整合所有视频的评论和回复
    if all_videos_comments or all_videos_replies:
        # 创建整合目录
        merged_dir = "data/merged"
        os.makedirs(merged_dir, exist_ok=True)
        
        # 合并一级评论
        if all_videos_comments:
            merged_comments = pd.concat(all_videos_comments, ignore_index=True)
            merged_comments_file = os.path.join(merged_dir, "all_comments.csv")
            save(merged_comments, merged_comments_file)
            print(f"已将所有一级评论整合到 {merged_comments_file}")
        
        # 合并二级评论
        if all_videos_replies:
            merged_replies = pd.concat(all_videos_replies, ignore_index=True)
            merged_replies_file = os.path.join(merged_dir, "all_replies.csv")
            save(merged_replies, merged_replies_file)
            print(f"已将所有二级评论整合到 {merged_replies_file}")
        
        # 合并所有评论（一级和二级）
        if all_videos_comments or all_videos_replies:
            all_comments_list = []
            if all_videos_comments:
                all_comments_list.append(pd.concat(all_videos_comments, ignore_index=True))
            if all_videos_replies:
                all_comments_list.append(pd.concat(all_videos_replies, ignore_index=True))
            
            merged_all = pd.concat(all_comments_list, ignore_index=True)
            merged_all_file = os.path.join(merged_dir, "all_comments_and_replies.csv")
            save(merged_all, merged_all_file)
            print(f"已将所有评论（一级和二级）整合到 {merged_all_file}")


# 运行 main 函数
if __name__ == "__main__":
    asyncio.run(main())
    print('done!')
