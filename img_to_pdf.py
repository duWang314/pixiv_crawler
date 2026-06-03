import sys
import os
from PIL import Image


def merge_images_to_pdf(folder_name, output_pdf_name, current_img_format, current_img_count):
    # 1. 精确指定 1 到 16 的顺序，避免字符串排序导致的页码错乱
    image_paths = [os.path.join(folder_name, f"{folder_name}_p{i}.{current_img_format}") for i in range(0, current_img_count)]

    images = []

    # 2. 检查并加载所有图片
    for path in image_paths:
        if not os.path.exists(path):
            print(f"错误：未找到文件 {path}，请检查图片是否齐全。")
            return

        img = Image.open(path)

        # 3. 处理透明通道
        # 很多 PNG 图片带有透明通道（RGBA 模式），直接转 PDF 可能会导致透明部分变成黑色。
        # 这里为透明图片铺上白色底色，确保漫画显示正常。
        if current_img_format == "png":
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                bg = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    bg.paste(img, mask=img.split()[3])  # 使用透明通道作为掩码
                else:
                    bg.paste(img)
                images.append(bg)
            else:
                # 普通的 RGB 或其他模式，直接转换并存入列表
                images.append(img.convert("RGB"))
        elif current_img_format == "jpg":
            images.append(img.convert("RGB"))

    # 4. 合并并保存为多页 PDF
    if images:
        # 以第一张图片为基础，将后续所有图片以追加页（append_images）的形式存入同一个 PDF
        images[0].save(f"./{folder_name}/{output_pdf_name}", save_all=True, append_images=images[1:])
        print(f"成功！已将 {len(images)} 张图片整合成：{output_pdf_name}")


if __name__ == "__main__":
    # 当前目录下的指定文件夹
    folder_dir = sys.argv[1].strip()
    # 想要输出的 PDF 文件名
    output_pdf = sys.argv[2].strip()
    # 图片格式
    img_format = sys.argv[3].strip()
    # 图片张数
    img_count = int(sys.argv[4].strip())

    merge_images_to_pdf(folder_dir, output_pdf, img_format, img_count)
