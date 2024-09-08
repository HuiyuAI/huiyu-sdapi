from flask import Flask, request, jsonify
import webuiapi
import upyun
from io import BytesIO
from PIL import Image
import mozjpeg_lossless_optimization
import concurrent.futures
from typing import List
import uuid
from logger import logger
import time
import threading
import requests
import configparser


config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')


app = Flask(__name__)
api = webuiapi.WebUIApi(host='127.0.0.1', port=7860)
up = upyun.UpYun(
    service=config.get('upyun', 'service'),
    username=config.get('upyun', 'username'),
    password=config.get('upyun', 'password')
)


# ========================= 服务端固定参数 ===========================
g_server_base_url = config.get('server', 'server_base_url')
g_server_upload_success_callback_url = '/service/callback/sd/uploadSuccessCallback'
g_server_upload_success_callback_token = config.get('server', 'server_upload_success_callback_token')
# ==================================================================


# ========================= upyun固定参数 ===========================
g_upyun_path_prefix = config.get('upyun', 'path_prefix')
g_upyun_file_suffix = '.jpg'
# ==================================================================


# ======================== txt2img固定参数 ==========================
# 重置设置
g_txt2img_override_settings_restore_afterwards = False
# 噪声种子偏移ENSD
g_txt2img_eta = 31337
# 保存图片至本地
g_txt2img_save_images = True
# 高分辨率采样步数 0为和steps一致
g_txt2img_hr_second_pass_steps = 0

g_txt2img_fixed_params = {
    'override_settings_restore_afterwards': g_txt2img_override_settings_restore_afterwards,
    'eta': g_txt2img_eta,
    'save_images': g_txt2img_save_images,
    'hr_second_pass_steps': g_txt2img_hr_second_pass_steps
}
# ==================================================================


# ======================== upscale固定参数 ==========================
# 重置设置
g_upscale_override_settings_restore_afterwards = False
# 噪声种子偏移ENSD
g_upscale_eta = 31337
# 保存图片至本地
g_upscale_save_images = True
# 缩放模式 0 Just resize, 1 Crop and resize, 2 Resize and fill, 3 Just resize (latent upscale)
g_upscale_resize_mode = 0
# 脚本名称
g_upscale_script_name = 'SD upscale'
# 脚本参数 /scripts/sd_upscale.py -> def run(self, p, _, overlap, upscaler_index, scale_factor)
g_upscale_script_args = [None, 64, 'R-ESRGAN 4x+ Anime6B', 2]

g_upscale_fixed_params = {
    'override_settings_restore_afterwards': g_upscale_override_settings_restore_afterwards,
    'eta': g_upscale_eta,
    'save_images': g_upscale_save_images,
    'resize_mode': g_upscale_resize_mode,
    'script_name': g_upscale_script_name,
    'script_args': g_upscale_script_args
}
# ==================================================================


# ========================== extra固定参数 ==========================
# 等比缩放模式0 指定分辨率缩放模式1
g_extra_resize_mode = 0
# 高清化算法
g_extra_upscaler_1 = 'R-ESRGAN 4x+ Anime6B'
# Should the backend return the generated image? 测试好像效果相同
g_extra_show_extras_results = True

g_extra_fixed_params = {
    'resize_mode': g_extra_resize_mode,
    'upscaler_1': g_extra_upscaler_1,
    'show_extras_results': g_extra_show_extras_results,
}
# ==================================================================


@app.route('/txt2img', methods=['POST'])
def txt2img():
    data = request.get_json()
    logger.info("txt2img request body: %s", data)

    res_image_uuid = data['res_image_uuid']
    res_image_url_uuid = data['res_image_url_uuid']
    enable_extra = data['enable_extra']
    upscaling_resize = data['upscaling_resize']
    params = {
        'override_settings': {
            'sd_model_checkpoint': data['sd_model_checkpoint'],
            'sd_vae': data['sd_vae']
        },
        'prompt': data['prompt'] + ',' + data['default_prompt'] + ',' + data['lora'],
        'negative_prompt': data['negative_prompt'] + ',' + data['default_negative_prompt'],
        'sampler_name': data['sampler_name'],
        'steps': data['steps'],
        'enable_hr': data['enable_hr'],
        'hr_upscaler': data['hr_upscaler'],
        'denoising_strength': data['denoising_strength'],
        'hr_scale': data['hr_scale'],
        'width': data['width'],
        'height': data['height'],
        'batch_size': data['batch_size'],
        'n_iter': data['n_iter'],
        'cfg_scale': data['cfg_scale'],
        'seed': data['seed'],
        'alwayson_scripts': data.get('alwayson_scripts', {})
    }
    response = txt2img_generate(params, res_image_uuid, res_image_url_uuid, enable_extra, upscaling_resize)
    return jsonify(response)


@app.route('/img2img', methods=['POST'])
def img2img():
    data = request.get_json()


@app.route('/upscale', methods=['POST'])
def upscale():
    data = request.get_json()
    logger.info("extra request body: %s", data)

    res_image_uuid = data['res_image_uuid']
    res_image_url_uuid = data['res_image_url_uuid']
    image_uuid = data['image_uuid']
    params = {
        'override_settings': {
            'sd_model_checkpoint': data['sd_model_checkpoint'],
            'sd_vae': data['sd_vae']
        },
        'prompt': data['prompt'],
        'negative_prompt': data['negative_prompt'],
        'sampler_name': data['sampler_name'],
        'steps': data['steps'],
        'denoising_strength': data['denoising_strength'],
        'width': data['width'],
        'height': data['height'],
        'batch_size': data['batch_size'],
        'n_iter': data['n_iter'],
        'cfg_scale': data['cfg_scale'],
        'seed': data['seed']
    }
    response = upscale_generate(params, image_uuid, res_image_uuid, res_image_url_uuid)
    return jsonify(response)


@app.route('/extra', methods=['POST'])
def extra():
    data = request.get_json()
    logger.info("extra request body: %s", data)

    res_image_uuid = data['res_image_uuid']
    res_image_url_uuid = data['res_image_url_uuid']
    image_uuid = data['image_uuid']
    upscaling_resize = data['upscaling_resize']
    response = extra_generate(image_uuid, upscaling_resize, res_image_uuid, res_image_url_uuid)
    return jsonify(response)


def txt2img_generate(params: dict, res_image_uuid: str, res_image_url_uuid: str, enable_extra: bool, upscaling_resize: int) -> dict:
    start_time = time.time()
    params.update(g_txt2img_fixed_params)

    # 跑图
    logger.info("txt2img params: %s", params)
    result = api.txt2img(**params)
    logger.info("txt2img sd generate done, elapsed time: %s seconds", time_diff(start_time))

    res_image = result.image

    if enable_extra:
        # 启用工序三：高清化extra
        logger.info("txt2img enable extra")
        extra_params = {
            'image': result.image,
            'upscaling_resize': upscaling_resize
        }
        extra_params.update(g_extra_fixed_params)

        # 高清化extra跑图
        start_time2 = time.time()
        logger.info("txt2img extra params: %s", extra_params)
        extra_result = api.extra_single_image(**extra_params)
        logger.info("txt2img extra sd generate done, elapsed time: %s seconds", time_diff(start_time2))
        res_image = extra_result.image

    # 异步压缩上传
    async_compress_and_upload(res_image, res_image_uuid, res_image_url_uuid)

    # 返回结果
    response = {
        'code': 200,
        'msg': 'success',
        'data': {
            'res_image_uuid': res_image_uuid,
            'info': result.info,
            'parameters': result.parameters
        }
    }
    logger.info("txt2img end, total elapsed time: %s seconds, response: %s", time_diff(start_time), response)
    return response


def img2img_generate() -> dict:
    pass


def upscale_generate(params: dict, image_uuid: str, res_image_uuid: str, res_image_url_uuid: str) -> dict:
    start_time = time.time()
    # 下载图片
    img_pil = download_image_from_upyun(image_uuid)
    logger.info("upscale origin image download done, elapsed time: %s seconds", time_diff(start_time))

    params['images'] = [img_pil]
    params.update(g_upscale_fixed_params)

    # 跑图
    start_time2 = time.time()
    logger.info("upscale params: %s", params)
    result = api.img2img(**params)
    logger.info("upscale sd generate done, elapsed time: %s seconds", time_diff(start_time2))

    # 异步压缩上传
    async_compress_and_upload(result.image, res_image_uuid, res_image_url_uuid)

    # 返回结果
    response = {
        'code': 200,
        'msg': 'success',
        'data': {
            'res_image_uuid': res_image_uuid,
            'info': result.info,
            'parameters': result.parameters
        }
    }
    logger.info("upscale end, total elapsed time: %s seconds, response: %s", time_diff(start_time), response)
    return response


def extra_generate(image_uuid: str, upscaling_resize: int, res_image_uuid: str, res_image_url_uuid: str) -> dict:
    start_time = time.time()
    # 下载图片
    img_pil = download_image_from_upyun(image_uuid)
    logger.info("extra origin image download done, elapsed time: %s seconds", time_diff(start_time))

    params = {
        'image': img_pil,
        'upscaling_resize': upscaling_resize
    }
    params.update(g_extra_fixed_params)

    # 跑图
    start_time2 = time.time()
    logger.info("extra params: %s", params)
    result = api.extra_single_image(**params)
    logger.info("extra sd generate done, elapsed time: %s seconds", time_diff(start_time2))

    # 异步压缩上传
    async_compress_and_upload(result.image, res_image_uuid, res_image_url_uuid)

    # 返回结果
    # 删除无用的信息
    result.info = result.info.replace('<p>', '').replace('</p>', '')
    response = {
        'code': 200,
        'msg': 'success',
        'data': {
            'res_image_uuid': res_image_uuid,
            'info': result.info,
            'parameters': result.parameters
        }
    }
    logger.info("extra end, total elapsed time: %s seconds, response: %s", time_diff(start_time), response)
    return response


def async_compress_and_upload(image: Image.Image, res_image_uuid: str, res_image_url_uuid: str) -> str:
    if res_image_url_uuid is None:
        res_image_url_uuid = str(uuid.uuid4())

    logger.info("async_compress_and_upload res_image_uuid: %s, res_image_url_uuid: %s", res_image_uuid, res_image_url_uuid)
    # 直接return res_image_url_uuid，并在子线程中压缩上传
    threading.Thread(target=compress_and_upload_and_callback, args=(image, res_image_uuid, res_image_url_uuid)).start()
    return res_image_url_uuid


def compress_and_upload_and_callback(image: Image.Image, res_image_uuid: str, res_image_url_uuid: str) -> str:
    compress_and_upload(image, res_image_uuid, res_image_url_uuid)
    # 回调java端
    upload_success_callback(res_image_uuid, res_image_url_uuid)


def compress_and_upload(image: Image.Image, res_image_uuid: str, res_image_url_uuid: str) -> str:
    if res_image_url_uuid is None:
        res_image_url_uuid = str(uuid.uuid4())
        logger.info("compress_and_upload res_image_url_uuid: %s", res_image_url_uuid)

    start_time = time.time()
    # 压缩
    optimized_jpeg_bytes = convert_to_optimized_jpeg(image)
    logger.info("compress done res_image_uuid: %s, res_image_url_uuid: %s, elapsed time: %s seconds", res_image_uuid, res_image_url_uuid, time_diff(start_time))

    start_time2 = time.time()
    # 上传
    up.put(f'{g_upyun_path_prefix}{res_image_url_uuid}{g_upyun_file_suffix}', optimized_jpeg_bytes)
    logger.info("upload done res_image_uuid: %s, res_image_url_uuid: %s, elapsed time: %s seconds", res_image_uuid, res_image_url_uuid, time_diff(start_time2))
    return res_image_url_uuid


def upload_success_callback(res_image_uuid: str, res_image_url_uuid: str) -> None:
    callback_url = g_server_base_url + g_server_upload_success_callback_url
    request_body = {
        'res_image_uuid': res_image_uuid,
        'res_image_url_uuid': res_image_url_uuid,
        'token': g_server_upload_success_callback_token
    }
    logger.info("upload_success_callback request body: %s", request_body)
    response = requests.post(callback_url, json=request_body)
    logger.info("upload_success_callback response: %s", response.json())


# def multithread_compress_and_upload(images: List[Image.Image]) -> List[str]:
#     logger.info("upload images num: %s", len(images))
#     # 多线程压缩上传
#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         future_to_image_uuid = {
#             executor.submit(compress_and_upload, image): image for image in images
#         }
#     res_image_uuid_list = []
#     for future in concurrent.futures.as_completed(future_to_image_uuid):
#         res_image_uuid = future.result()
#         res_image_uuid_list.append(res_image_uuid)
#     return res_image_uuid_list


def convert_to_optimized_jpeg(image: Image.Image) -> bytes:
    jpeg_io = BytesIO()

    image.convert("RGB").save(jpeg_io, format="JPEG", quality=85)

    jpeg_io.seek(0)
    jpeg_bytes = jpeg_io.read()

    optimized_jpeg_bytes = mozjpeg_lossless_optimization.optimize(jpeg_bytes)
    return optimized_jpeg_bytes


def download_image_from_upyun(image_uuid: str) -> Image.Image:
    img_io = BytesIO()
    up.get(f'{g_upyun_path_prefix}{image_uuid}{g_upyun_file_suffix}', img_io)
    img_pil = Image.open(img_io)
    return img_pil


def time_diff(start_time):
    return round(time.time() - start_time, 2)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=config.get('app', 'port'), debug=False)
