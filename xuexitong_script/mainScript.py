import os
import re
import requests
from fpdf import FPDF
from PIL import Image

"""
    使用说明：
        1、本脚本版本依赖于:
            python = 3.10.6及以上;
            requests = 2.32.3; 命令: pip install requests
            fpdf = 1.72; 命令: pip install fpdf
            pillow =  11.0.0; 命令: pip install pillow

        2、教程：
            参考配套说明文档 "README.md"。
            图片路径基础URL格式参考如下：
            base_url = "https://s3.ananas.chaoxing.com/sv-w7/doc/51/18/e4/127ef24fab63d580372a890efd5dc250/thumb/"
            输入相关链接请只保留到thumb之前的所有部分，之后跟随的1.png等请删去。
"""

# 请求超时时间（秒）
REQUEST_TIMEOUT = 30
# 单次下载最大字节数（100MB，防止恶意大文件撑爆磁盘）
MAX_FILE_SIZE = 100 * 1024 * 1024
# 最大重试次数
MAX_RETRIES = 3


def sanitize_filename(name):
    """
    清理文件名，移除不安全的路径字符，防止路径穿越攻击
    只保留字母、数字、下划线、中划线、中文、句点
    """
    safe = re.sub(r'[^\w\-. \u4e00-\u9fff]', '_', name)
    # 将连续两点替换为下划线（防止 ../ 路径穿越）
    safe = safe.replace('..', '_')
    safe = safe.strip(' .')
    if not safe:
        safe = 'output'
    return safe


def is_valid_url(url):
    """
    验证 URL 格式是否合法
    仅允许 http/https 协议，防止 file:// 等协议注入
    """
    return bool(re.match(r'^https?://\S+', url))


def detect_total_pages(base_url, progress_callback=None):
    """
    自动检测 PPT 总页数，使用二分查找算法
    先指数增长找到上界，再二分精确定位

    参数:
        base_url: 图片基础 URL
        progress_callback: 进度回调函数，接收 (current, total, message)

    返回:
        检测到的总页数，失败返回 0
    """
    # 先确认第1页存在
    try:
        resp = requests.get(f"{base_url}1.png", timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            if progress_callback:
                progress_callback(0, 0, "无法访问第1页，请检查URL")
            return 0
    except requests.RequestException as e:
        if progress_callback:
            progress_callback(0, 0, f"网络错误: {e}")
        return 0

    # 指数增长阶段：1, 2, 4, 8, 16... 直到404
    lo, hi = 1, 2
    while True:
        try:
            resp = requests.get(f"{base_url}{hi}.png", timeout=REQUEST_TIMEOUT)
            if resp.status_code == 404:
                break
            if progress_callback:
                progress_callback(0, hi, f"正在探测总页数... 已确认到第{hi}页")
            lo = hi
            hi *= 2
            # 防止无限循环（上限 10000 页）
            if hi > 10000:
                hi = lo + 10000
                break
        except requests.RequestException:
            hi = lo + 50
            break

    # 二分查找阶段：在 (lo, hi] 区间找第一个404页
    while lo < hi - 1:
        mid = (lo + hi) // 2
        try:
            resp = requests.get(f"{base_url}{mid}.png", timeout=REQUEST_TIMEOUT)
            if resp.status_code == 404:
                hi = mid
            else:
                lo = mid
            if progress_callback:
                progress_callback(lo, hi, f"正在精确查找总页数... 当前确认到第{lo}页")
        except requests.RequestException:
            hi = mid

    if progress_callback:
        progress_callback(lo, lo, f"检测完成，共 {lo} 页")
    return lo


def download_picture(start, end, path_img, base_url):
    """
    下载指定范围内的图片
    包含超时、重试、文件大小限制等保护措施
    """
    for i in range(start, end + 1):
        url = f"{base_url}{i}.png"

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = requests.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()

                # 检查内容类型是否为图片
                content_type = response.headers.get('Content-Type', '')
                if 'image' not in content_type:
                    print(f"警告: 第{i}页返回非图片类型 ({content_type})，跳过")
                    break

                # 检查文件大小是否超出限制
                if len(response.content) > MAX_FILE_SIZE:
                    print(f"警告: 第{i}页文件过大 ({len(response.content)} bytes)，跳过")
                    break

                # 构造安全的保存路径（使用 abspath 防止路径穿越）
                file_path = os.path.abspath(os.path.join(path_img, f"{i}.png"))

                # 确保文件路径仍在 path_img 目录下（路径穿越防护）
                if not file_path.startswith(os.path.abspath(path_img)):
                    print(f"错误: 检测到路径穿越攻击，拒绝保存 {file_path}")
                    return

                with open(file_path, 'wb') as f:
                    f.write(response.content)

                print(f"{i}.png 已经成功下载")
                break  # 成功则跳出重试循环

            except requests.Timeout:
                print(f"超时下载 {i}.png (第{attempt}次尝试)")
                if attempt == MAX_RETRIES:
                    print(f"放弃下载 {i}.png（已重试{MAX_RETRIES}次）")
            except requests.RequestException as e:
                print(f"错误下载 {i}.png: {e}")
                break  # 非超时错误不重试


def convert_images_to_pdf(img_folder, output_pdf, path_pdf, start, end):
    """
    将指定范围内的图片合并为 PDF
    包含路径穿越防护和文件存在性检查
    """
    print("请等待，正在生成中……")

    file_paths = []
    for i in range(start, end + 1):
        file_path = os.path.abspath(os.path.join(img_folder, f"{i}.png"))
        if not file_path.startswith(os.path.abspath(img_folder)):
            print(f"错误: 检测到路径穿越攻击，拒绝处理 {file_path}")
            return
        file_paths.append(file_path)

    # 检查图片文件是否存在
    for fp in file_paths:
        if not os.path.exists(fp):
            print(f"Warning: {fp} does not exist.")
            return

    # 打开第一张图片以获取尺寸
    first_img = Image.open(file_paths[0])
    width, height = first_img.size

    # 创建PDF对象，使用第一张图片的尺寸
    pdf = FPDF(unit="pt", format=[width, height])

    for fp in file_paths:
        img = Image.open(fp)
        pdf.add_page()
        img_width, img_height = img.size
        x = (width - img_width) / 2
        y = (height - img_height) / 2
        pdf.image(fp, x, y, img_width, img_height)

    # 构造安全的输出路径
    safe_pdf = sanitize_filename(output_pdf)
    if not safe_pdf.endswith('.pdf'):
        safe_pdf += '.pdf'
    output_path = os.path.join(os.path.abspath(path_pdf), safe_pdf)

    pdf.output(output_path, "F")
    print(f"{safe_pdf} 生成完成")


def clean_cache(path_img, file_pattern="*.png"):
    """
    清理 images 目录下的缓存文件
    使用 glob 匹配模式，默认删除所有 png 文件
    仅在 path_img 目录内操作，防止路径穿越
    """
    import glob
    abs_path = os.path.abspath(path_img)
    if not os.path.exists(abs_path):
        print(f"目录不存在: {abs_path}")
        return 0

    # 使用 glob 匹配文件
    matched = glob.glob(os.path.join(abs_path, file_pattern))
    deleted_count = 0

    for file_path in matched:
        real_path = os.path.abspath(file_path)
        # 路径穿越防护
        if not real_path.startswith(abs_path):
            print(f"警告: 跳过越界文件 {real_path}")
            continue
        try:
            os.remove(real_path)
            print(f"已删除: {os.path.basename(real_path)}")
            deleted_count += 1
        except OSError as e:
            print(f"删除失败 {real_path}: {e}")

    print(f"共删除 {deleted_count} 个文件")
    return deleted_count


if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    path_img = os.path.join(current_dir, 'images')
    path_pdf = os.path.join(current_dir, 'out_pdf')

    if not os.path.exists(path_img):
        os.makedirs(path_img)
    if not os.path.exists(path_pdf):
        os.makedirs(path_pdf)

    base_url = str(input("请输入相关链接：")).strip()
    start, end = int(input("请输入初始位置：")), int(input("请输入结束位置："))
    file_name = str(input("请输入你的pdf名字(例如test)：")) or 'test'
    output_pdf = sanitize_filename(file_name) + '.pdf'

    download_picture(start, end, path_img, base_url)
    convert_images_to_pdf(path_img, output_pdf, path_pdf, start, end)
