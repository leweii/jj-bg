import os

import cv2
import numpy as np
from modelscope.outputs import OutputKeys
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

UPLOAD_FOLDER = "./upload"
OUTPUT_FOLDER = "./output"

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


def crop_image_by_alpha_channel(input_image: np.ndarray | str, output_path: str):
    img_array = cv2.imread(input_image, cv2.IMREAD_UNCHANGED) if isinstance(input_image, str) else input_image
    if img_array.shape[2] != 4:
        raise ValueError("Input image must have an alpha channel")

    alpha_channel = img_array[:, :, 3]
    bbox = cv2.boundingRect(alpha_channel)
    x, y, w, h = bbox
    cropped_img_array = img_array[y:y + h, x:x + w]
    cv2.imwrite(output_path, cropped_img_array)
    return output_path


if __name__ == '__main__':
    image_bytes = open("./upload/1.png", "rb").read()
    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_UNCHANGED)
    final_img = convert_image_to_white_background(image=img)
    if final_img is None:
        raise Exception()
    universal_matting = pipeline(Tasks.universal_matting, model='damo/cv_unet_universal-matting')
    result = universal_matting(final_img)
    cv2.imwrite(os.path.join(OUTPUT_FOLDER, "1.whiteboard.png"), result[OutputKeys.OUTPUT_IMG])
    cv2.imwrite(os.path.join(OUTPUT_FOLDER, "1.mask.png"), result[OutputKeys.OUTPUT_IMG][:, :, 3])
    # result = universal_matting('https://modelscope.oss-cn-beijing.aliyuncs.com/demo/image-matting/1.png')
    # cv2.imwrite('result.png', result[OutputKeys.OUTPUT_IMG])
