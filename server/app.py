import requests

from flask import Flask, request, jsonify
from flask_cors import CORS

from utils import download_and_merge_video, get_video_info
from loguru import logger

app = Flask(__name__)
CORS(app)


@app.route("/parse_html", methods=["POST"])
def parse_html():
    try:
        data = request.json
        html = data.get("html", "")

        video_id, video_link = get_video_info(html)

        if not video_link or not video_id:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Не удалось получить информацию о видео",
                    }
                ),
                400,
            )

        download_and_merge_video(video_link=video_link, video_id=video_id)
        return jsonify(
            {"status": "success", "message": "Операция по скачиванию проведена успешно"}
        )

    except requests.exceptions.RequestException as e:
        logger.exception("❌ Ошибка при загрузке видео")
        return (
            jsonify({"status": "error", "message": "Ошибка при скачивании видео"}),
            500,
        )

    except Exception as e:
        logger.exception("❌ Внутренняя ошибка сервера")
        return jsonify({"status": "error", "message": "Внутренняя ошибка сервера"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
