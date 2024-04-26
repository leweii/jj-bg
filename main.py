import os
import cv2
import numpy as np
import time
from modelscope.outputs import OutputKeys
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

UPLOAD_FOLDER = "/app2/upload"
OUTPUT_FOLDER = "/app2/output"
BACKGROUND_FOLDER = "/app2/background"
OUTPUT_W_BACKGROUND_FOLDER = "/app2/output_with_background"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def convert_image_to_white_background(image: np.ndarray = None):
    try:
        if image is None:
            raise ValueError("Either image_path or image must be provided.")

        if image.shape[2] == 4:
            alpha_channel = image[:, :, 3]
            rgb_channels = image[:, :, :3]

            alpha_channel_3d = alpha_channel[:, :, np.newaxis] / 255.0
            alpha_channel_3d = np.repeat(alpha_channel_3d, 3, axis=2)

            white_background_image = np.ones_like(rgb_channels, dtype=np.uint8) * 255

            foreground = cv2.multiply(rgb_channels, alpha_channel_3d, dtype=cv2.CV_8UC3)
            background = cv2.multiply(white_background_image, 1 - alpha_channel_3d, dtype=cv2.CV_8UC3)

            processed_img = cv2.add(foreground, background)
        else:
            processed_img = image
        return processed_img
    except Exception as e:
        print(f'Error: {e}')
        return None


def crop_image_by_alpha_channel(input_image: np.ndarray):
    img_array = cv2.imread(input_image, cv2.IMREAD_UNCHANGED) if isinstance(input_image, str) else input_image
    if img_array.shape[2] != 4:
        raise ValueError("Input image must have an alpha channel")

    alpha_channel = img_array[:, :, 3]
    bbox = cv2.boundingRect(alpha_channel)
    x, y, w, h = bbox
    return img_array[y:y + h, x:x + w]


def get_all_file_names(folder_path):
    file_names = []
    for root, _, files in os.walk(folder_path):
        for file_name in files:
            if file_name.endswith(".png") or file_name.endswith(".jpg") or file_name.endswith(".jpeg"):
                file_names.append(file_name)
    return file_names


def add_alpha_channel(img):
    """ 为jpg图像添加alpha通道 """

    b_channel, g_channel, r_channel = cv2.split(img)  # 剥离jpg图像通道
    alpha_channel = np.ones(b_channel.shape, dtype=b_channel.dtype) * 255  # 创建Alpha通道

    img_new = cv2.merge((b_channel, g_channel, r_channel, alpha_channel))  # 融合通道
    return img_new


def merge_img(jpg_img, png_img, y1, y2, x1, x2):
    """ 将png透明图像与jpg图像叠加
        y1,y2,x1,x2为叠加位置坐标值
    """

    # 判断jpg图像是否已经为4通道
    if jpg_img.shape[2] == 3:
        jpg_img = add_alpha_channel(jpg_img)

    '''
    当叠加图像时，可能因为叠加位置设置不当，导致png图像的边界超过背景jpg图像，而程序报错
    这里设定一系列叠加位置的限制，可以满足png图像超出jpg图像范围时，依然可以正常叠加
    '''
    yy1 = 0
    yy2 = png_img.shape[0]
    xx1 = 0
    xx2 = png_img.shape[1]

    if x1 < 0:
        xx1 = -x1
        x1 = 0
    if y1 < 0:
        yy1 = - y1
        y1 = 0
    if x2 > jpg_img.shape[1]:
        xx2 = png_img.shape[1] - (x2 - jpg_img.shape[1])
        x2 = jpg_img.shape[1]
    if y2 > jpg_img.shape[0]:
        yy2 = png_img.shape[0] - (y2 - jpg_img.shape[0])
        y2 = jpg_img.shape[0]

    # 获取要覆盖图像的alpha值，将像素值除以255，使值保持在0-1之间
    alpha_png = png_img[yy1:yy2, xx1:xx2, 3] / 255.0
    alpha_jpg = 1 - alpha_png

    # 开始叠加
    for c in range(0, 3):
        print("y1: ", y1, ", y2: ", y2, ", x1: ", x1, ", x2: ", x2, ", c: ", c)
        jpg_img[y1:y2, x1:x2, c] = ((alpha_jpg * jpg_img[y1:y2, x1:x2, c]) + (alpha_png * png_img[yy1:yy2, xx1:xx2, c]))

    return jpg_img


if __name__ == '__main__':
    try:
        universal_matting = pipeline(Tasks.universal_matting, model='damo/cv_unet_universal-matting')
        while True:
            time.sleep(5)  # 每5秒扫描一次
            uploaded_file_names = get_all_file_names(UPLOAD_FOLDER)  # 更新文件路径列表
            executed_file_names = get_all_file_names(OUTPUT_FOLDER)  # 更新文件路径列表

            print("uploaded_file_names: ", uploaded_file_names)
            print("executed_file_names: ", executed_file_names)
            to_execute_files = list(set(uploaded_file_names) - set(executed_file_names))
            print("to_execute_files: ", to_execute_files)

            if len(to_execute_files) <= 0:
                continue

            for file in to_execute_files:
                image_bytes = open(os.path.join(UPLOAD_FOLDER, file), "rb").read()
                img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_UNCHANGED)
                final_img = convert_image_to_white_background(image=img)
                if final_img is None:
                    raise Exception()
                result_img = universal_matting(final_img)
                output_path = os.path.join(OUTPUT_FOLDER, file)
                # cropped_img = crop_image_by_alpha_channel(result_img[OutputKeys.OUTPUT_IMG])
                cropped_img = result_img[OutputKeys.OUTPUT_IMG]
                cv2.imwrite(output_path, cropped_img)

                background_file_names = get_all_file_names(BACKGROUND_FOLDER)  # 更新文件路径列表
                executed_wbg_file_names = get_all_file_names(OUTPUT_W_BACKGROUND_FOLDER)  # 更新文件路径列表
                if file in executed_wbg_file_names:
                    print("file: ", uploaded_file_names)
                    print("executed_wbg_file_names: ", executed_wbg_file_names)
                    continue
                for bg_file in background_file_names:
                    bg_img = cv2.imread(os.path.join(BACKGROUND_FOLDER, bg_file))
                    img_png = cv2.imread(output_path, cv2.IMREAD_UNCHANGED)
                    # 计算img2放置的位置
                    y1 = (bg_img.shape[0] - img_png.shape[0]) // 2
                    x1 = (bg_img.shape[1] - img_png.shape[1]) // 2
                    y2 = y1 + img_png.shape[0]
                    x2 = x1 + img_png.shape[1]

                    res_img = merge_img(bg_img, img_png, y1, y2, x1, x2)

                    # 显示合并后的图像
                    cv2.imwrite(os.path.join(OUTPUT_W_BACKGROUND_FOLDER, file), res_img)

    except KeyboardInterrupt:
        print("\n扫描已停止。")
