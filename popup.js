document.getElementById("parse-video").addEventListener("click", async () => {
    document.getElementById("status").innerText = "⏳ Видео скачивается";
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        const response = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            function: extractHTML,
        });

        if (response && response[0].result) {
            await fetch("http://127.0.0.1:5000/parse_html", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    url: tab.url,
                    html: response[0].result,
                }),
            });

            document.getElementById("status").innerText = "✅ Видео скачано";
            setTimeout(() => window.close(), 1000); // Закрываем окно через 1 сек
        } else {
            document.getElementById("status").innerText = "❌ Ошибка: Не удалось получить HTML";
        }
    } catch (error) {
        document.getElementById("status").innerText = "❌ Ошибка запроса";
        console.error(error);
    }
});

function extractHTML() {
    return document.documentElement.outerHTML; // Получаем HTML всей страницы
}
