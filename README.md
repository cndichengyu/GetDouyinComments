# 抖音评论采集工具

## 项目简介

这是一个用于采集抖音视频评论的工具，可以批量获取多个抖音视频的评论和回复，并将数据整合到CSV文件中。

## 功能特点

- 支持批量采集多个抖音视频的评论
- 自动提取视频URL中的aweme_id
- 支持获取一级评论和二级评论（回复）
- 数据自动保存为CSV格式，便于后续分析
- 支持将所有视频的评论整合到一个文件中
- 支持处理不同类型的抖音内容（视频和图文）

## 环境要求

- Python 3.7+
- 所需依赖包：
  - cookiesparser==1.3
  - httpx==0.27.2
  - pandas==2.2.3
  - PyExecJS==1.5.1
  - Requests==2.32.3
  - tqdm==4.66.1

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. **准备cookie**：
   - 在浏览器中登录抖音网页版
   - 打开开发者工具，复制cookie信息
   - 将cookie信息粘贴到`cookie.txt`文件中

2. **配置视频URL**：
   - 在`main.py`文件中，修改`video_urls`列表，添加你要采集的抖音视频URL

3. **运行脚本**：
   ```bash
   python main.py
   ```

4. **查看结果**：
   - 采集的数据会保存在`data/v1/`目录下，每个视频对应一个文件夹
   - 整合后的数据会保存在`data/merged/`目录下

## 数据结构

### 评论数据（comments.csv）
- 评论ID
- 评论内容
- 评论图片
- 点赞数
- 评论时间
- 用户昵称
- 用户主页链接
- 用户抖音号
- 用户签名
- 回复总数
- ip归属
- 视频URL
- aweme_id
- 评论类型

### 回复数据（replies.csv）
- 评论ID
- 评论内容
- 评论图片
- 点赞数
- 评论时间
- 用户昵称
- 用户主页链接
- 用户抖音号
- 用户签名
- 回复的评论
- 具体的回复对象
- 回复给谁
- ip归属
- 视频URL
- aweme_id
- 评论类型

## 注意事项

1. **cookie有效期**：cookie会定期失效，需要定期更新
2. **请求频率**：工具已经设置了合理的请求间隔，不要频繁运行，以免被抖音封禁
3. **数据量**：对于评论较多的视频，采集时间会较长，请耐心等待
4. **网络稳定性**：确保网络连接稳定，避免采集过程中中断

## 示例

### 配置视频URL

```python
# 抖音视频URL列表
video_urls = [
    "https://v.douyin.com/1iGjrccgq5I/",
    "https://v.douyin.com/dNSbOFi71pY/",
    "https://v.douyin.com/pGrLdrknufo/",
    "https://v.douyin.com/4XAc3ONhLVg/",
    "https://v.douyin.com/fX1BEmM8cs8/",
    "https://v.douyin.com/pccJTvWvW7w/"
]
```

### 运行结果

```
处理视频 URL: https://v.douyin.com/1iGjrccgq5I/
提取到的 aweme_id: 7481498601680538934
Fetching comments: 8comment [00:02,  3.23comment/s]
Found 8 comments.
Fetching replies: 100%|█████████████████████| 8/8 [00:01<00:00,  5.05comment/s]
Found 1 replies
Found 9 in totals

==================================================

# 其他视频的处理结果...

已将所有一级评论整合到 data/merged\all_comments.csv
已将所有二级评论整合到 data/merged\all_replies.csv
已将所有评论（一级和二级）整合到 data/merged\all_comments_and_replies.csv
done!
```

## 常见问题

1. **无法提取aweme_id**：
   - 可能是因为URL格式不正确或视频已被删除
   - 工具支持处理`/video/`和`/note/`两种格式的URL

2. **采集失败**：
   - 检查cookie是否有效
   - 检查网络连接是否正常
   - 尝试降低请求频率

3. **数据不完整**：
   - 可能是因为抖音限制了评论的获取
   - 尝试更新cookie后重新采集

## 许可证

本项目仅供学习和研究使用，不得用于商业用途。

## 免责声明

使用本工具时，请遵守抖音的用户协议和相关法律法规，不要滥用工具进行大规模采集。

---
