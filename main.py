import sys
import time
import requests
from pathlib import Path
from datetime import datetime

from img_to_pdf import merge_images_to_pdf


def print_current_time():
    now = datetime.now()
    print(now.strftime("%m-%d %H:%M:%S"), end=" ")

def batch_download(base_url):
    # 判断用户传的 url 是否自带格式
    img_format = base_url.split('.')[-1]
    if img_format == "jpg" or img_format == "png":
        img_has_format = True
    else:
        img_has_format = False

    # 处理 url
    base_url = base_url.split('_')[0]

    # 从 URL 中提取作品 ID，用于后续文件名命名
    artwork_id = base_url.split('/')[-1]

    # 设置对于网络请求的最大尝试次数
    max_retries = 3

    headers = {
        "accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "priority": "u=1, i",
        "referer": "https://www.pixiv.net/",
        "sec-ch-ua": '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "image",
        "sec-fetch-mode": "no-cors",
        "sec-fetch-site": "cross-site",
        "sec-fetch-storage-access": "active",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/148.0.0.0 Safari/537.36"
    }

    page = 0
    print()
    print_current_time()
    print(f"[开始任务] 目标作品 ID: {artwork_id}")

    folder_path = Path(artwork_id)

    try:
        folder_path.mkdir(exist_ok=True)
        print_current_time()
        print(f"[准备阶段] 文件夹 '{folder_path}' 创建成功（或已存在）")
    except PermissionError:
        print_current_time()
        print("[准备失败] 权限不足，无法创建文件夹")
        sys.exit(1)
    except OSError as e:
        print_current_time()
        print(f"[准备失败] 创建文件夹时出错: {e}")
        sys.exit(1)
    
    # 测试请求地址，png or jpg
    if not img_has_format:
        for attempt in range(1, max_retries + 1):
            try:
                png_status = requests.get(f"{base_url}_p{page}.png", headers=headers, timeout=20).status_code
                if png_status == 200:
                    print_current_time()
                    print("[准备阶段] 已确认图片格式为 png, 等待 5 秒后任务正式开始...")
                    img_format = "png"
                    time.sleep(5)
                    break
                elif png_status == 404:
                    print_current_time()
                    print("[准备阶段] 已确认图片格式不是 png, 等待 5 秒后尝试 jpg...")
                    time.sleep(5)
                    jpg_status = requests.get(f"{base_url}_p{page}.jpg", headers=headers, timeout=20).status_code
                    if jpg_status == 200:
                        print_current_time()
                        print("[准备阶段] 已确认图片格式为 jpg, 等待 5 秒后任务正式开始...")
                        img_format = "jpg"
                        time.sleep(5)
                        break
                    else:
                        print_current_time()
                        print("[准备失败] 未发现可以爬取的图片格式")
                        sys.exit(1)
                else:
                    print_current_time()
                    print(f"[请求异常] 服务器返回了未预期的状态码: {png_status}")
                    print_current_time()
                    print("[提示] 请检查是否由于请求过快导致 IP 被暂时封禁。")
                    sys.exit(1)
            except requests.RequestException as e:
                print_current_time()
                print(f"[网络错误] 第 {attempt} 次尝试, 请求发生异常中断: {e}")
                if attempt == max_retries:
                    print_current_time()
                    print("[网络错误] 已到达最大尝试次数, 程序退出")
                    sys.exit(1)
    else:
        print_current_time()
        print(f"[准备阶段] 链接已提供图片格式为 {img_format}")

    while True:
        # 1. 动态构造当前页面的图片链接和保存的文件名
        target_url = f"{base_url}_p{page}.{img_format}"
        filename = f"{artwork_id}_p{page}.{img_format}"

        print()
        print_current_time()
        print(f"[当前进度] 正在尝试下载页码: p{page}")
        print_current_time()
        print(f"[请求地址] {target_url}")

        for attempt in range(1, max_retries + 1):
            try:
                # 发送请求，设置超时时间防止卡死
                response = requests.get(target_url, headers=headers, timeout=20)

                # 2. 如果返回 200，说明图片存在，执行下载
                if response.status_code == 200:
                    with open(f"./{artwork_id}/{filename}", "wb") as f:
                        f.write(response.content)
                    print_current_time()
                    print(f"[下载成功] 图片已成功保存为: {filename}")

                    # 准备请求下一页
                    page += 1

                    # 3. 遵守规范，每次成功爬取后等待 10 秒
                    print_current_time()
                    print("[安全冷却] 为防止触发风控，等待 10 秒后继续...")
                    time.sleep(10)
                    break

                # 4. 如果返回 404，说明已经到了最后一页，优雅退出
                elif response.status_code == 404:
                    print()
                    print_current_time()
                    print("[任务结束] 收到 404 错误。判定该漫画已下载完毕。")
                    print_current_time()
                    print(f"[统计结果] 共计成功下载 {page} 张图片。")
                    print()

                    # 合并 pdf
                    print_current_time()
                    print("[收尾工作] 合并图片为 pdf ", end="")
                    merge_images_to_pdf(artwork_id, f"{artwork_id}.pdf", img_format, page)
                    sys.exit(0)

                # 5. 处理其他非 200/404 的异常状态码（如 403 封禁、502 报错等）
                else:
                    print_current_time()
                    print(f"[请求异常] 服务器返回了未预期的状态码: {response.status_code}")
                    print_current_time()
                    print("[提示] 请检查是否由于请求过快导致 IP 被暂时封禁。")
                    sys.exit(1)

            except requests.RequestException as e:
                print_current_time()
                print(f"[网络错误] 第 {attempt} 次尝试, 请求发生异常中断: {e}")
                if attempt == max_retries:
                    print_current_time()
                    print("[网络错误] 已到达最大尝试次数, 程序退出")
                    sys.exit(1)


if __name__ == "__main__":
    # 确保用户通过命令行传入了 URL 参数
    if len(sys.argv) < 2:
        print("错误: 未检测到目标 URL。")
        print("用法提示: python main.py <url>")
        print("示例: python main.py https://i.pximg.net/img-original/img/2025/06/27/01/29/21/xxxxxxxx_px.png")
        sys.exit(1)

    # 获取命令行传入的第一个参数（即 URL）
    input_url = sys.argv[1].strip()
    batch_download(input_url)
