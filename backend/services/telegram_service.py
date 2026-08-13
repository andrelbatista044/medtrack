import httpx
from ..database import settings


async def send_message(chat_id: str, text: str, reply_markup: dict | None = None) -> bool:
    if not settings.telegram_bot_token or not chat_id:
        return False
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage", json=payload)
        response.raise_for_status()
    return True

