import os
import re

from request_util import send_request
from parsel import Selector
from loguru import logger


headers = {
    "sec-ch-ua-platform": '"Windows"',
    "Referer": "https://www.wildberries.ru/catalog/261653810/feedbacks?imtId=228683437&size=406562558",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    "sec-ch-ua-mobile": "?0",
}


def xpath(text: str, query: str) -> Selector:
    return Selector(text=text).xpath(query=query)


def get_video_info(html):
    try:
        video_id_element = xpath(
            html,
            "//video[contains(@poster, 'videofeedback')]/@poster",
        ).get()

        if not video_id_element:
            logger.error("❌ Не найден атрибут poster у тега <video>")
            return None, None

        match_id = re.search(r"\/([a-f0-9-]+)\/preview\.webp", video_id_element)
        match_link = re.search(r"(https://[^/]+/[^/]+/)", video_id_element)

        if not match_id:
            logger.error("❌ Не удалось найти ID видео в poster")
            return None, None

        if not match_link:
            logger.error("❌ Не удалось найти ссылку на базовый URL видео")
            return None, None

        video_id = match_id.group(1)
        video_link = match_link.group(1)
        print(f"🎯 Найден ID: {video_id}")
        print(f"🎯 Найден link: {video_link}")

        return video_id, video_link

    except Exception as e:
        logger.exception("❌ Ошибка при обработке HTML")
        return None, None


def download_m3u8(m3u8_url, video_id):
    response = send_request("GET", url=m3u8_url, headers=headers)
    if response.status_code == 200:
        with open(f"video/{video_id}.m3u8", "w", encoding="utf-8") as file:
            file.write(response.text)
        print("✅ Видео скачано")
    else:
        print(f"❌ Ошибка {response.status_code}")
        return None
    return f"{video_id}.m3u8"


def parse_m3u8(m3u8_file):
    """Парсит .m3u8 и извлекает ссылки на ts-файлы"""
    ts_files = []
    with open(f"video/{m3u8_file}", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                ts_files.append(line)
    return ts_files


def download_ts_files(base_url, ts_files):
    """Скачивает все .ts файлы"""
    os.makedirs("temp_ts", exist_ok=True)
    downloaded_files = []

    for ts_file in ts_files:
        ts_url = ts_file if ts_file.startswith("http") else f"{base_url}/{ts_file}"
        ts_path = os.path.join("temp_ts", ts_file)

        print(f"📥 Скачиваем {ts_url}...")
        response = send_request("GET", url=ts_url, stream=True, headers=headers)
        if response.status_code == 200:
            with open(ts_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
            downloaded_files.append(ts_path)
        else:
            print(f"❌ Ошибка загрузки: {ts_url}")

    return downloaded_files


def merge_ts_to_mp4(ts_files, output_file):
    """Объединяет .ts файлы в один .mp4"""
    with open(output_file, "wb") as mp4_file:
        for ts_file in ts_files:
            with open(ts_file, "rb") as f:
                mp4_file.write(f.read())

    print(f"✅ Видео сохранено в {output_file}")

    # Очистка временных файлов
    for ts_file in ts_files:
        os.remove(ts_file)
    os.rmdir("temp_ts")


def delete_m3u8():
    path = 'video'
    for file in os.listdir(path):
        if file.endswith('.m3u8'):
            filepath = os.path.join(path, file)
            os.remove(filepath)
    logger.info("Лишние файлы удалены")


def download_and_merge_video(video_link, video_id):
    m3u8_url = f"{video_link}/index.m3u8"
    base_url = f"{video_link}/"
    output_filename = f"video/{video_id}.mp4"
    m3u8_file = download_m3u8(m3u8_url, video_id)
    if not m3u8_file:
        return

    ts_files = parse_m3u8(m3u8_file)
    ts_files = download_ts_files(base_url, ts_files)
    delete_m3u8()

    if ts_files:
        merge_ts_to_mp4(ts_files, output_filename)
