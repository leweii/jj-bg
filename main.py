import cv2
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from modelscope.outputs import OutputKeys


def print_hi(name):
    print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.


if __name__ == '__main__':
    print_hi('PyCharm')

universal_matting = pipeline(Tasks.universal_matting, model='damo/cv_unet_universal-matting')
result = universal_matting('https://modelscope.oss-cn-beijing.aliyuncs.com/demo/image-matting/1.png')
cv2.imwrite('result.png', result[OutputKeys.OUTPUT_IMG])
