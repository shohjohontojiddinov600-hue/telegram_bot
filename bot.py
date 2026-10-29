import asyncio
import html
import logging
import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
    MessageHandler,
    filters,
)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("Telegram token topilmadi. .env faylida TELEGRAM_TOKEN ni ko'rsating.")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

GOOGLE_HEADERS = {
    "User-Agent": "GoogleTranslate/6.28.0.05.419073042 (Linux; U; Android 11; Pixel 5)"
}
GOOGLE_API_URL = "https://translate.google.com/translate_a/single"


class RenderHealthCheckHandler(BaseHTTPRequestHandler):
    """Render.com Web Service port talabi uchun mini-vebserver."""
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Telegram Tarjimon Bot serverda 24/7 faol ishlamoqda!".encode("utf-8"))

    def log_message(self, format, *args):
        # Render ping loglari bilan konsolni to'ldirmaslik uchun
        pass


def start_render_web_server():
    """Render.com da bot Deploy failed bo'lmasligi uchun port ochadi."""
    port = int(os.environ.get("PORT", 10000))
    try:
        server = HTTPServer(("0.0.0.0", port), RenderHealthCheckHandler)
        logging.info("Render Web Server %s-portda ishga tushdi...", port)
        server.serve_forever()
    except Exception as exc:
        logging.warning("Web server xatosi (lokal kompyuterda bo'lsa xavotir olmang): %s", exc)

# Qo'llab-quvvatlanadigan mashhur tillar ro'yxati:
LANGUAGES = {
    "uz": {"name": "O‘zbekcha", "flag": "🇺🇿"},
    "ru": {"name": "Ruscha", "flag": "🇷🇺"},
    "en": {"name": "Inglizcha", "flag": "🇬🇧"},
    "ko": {"name": "Koreyscha", "flag": "🇰🇷"},
    "ja": {"name": "Yaponcha", "flag": "🇯🇵"},
    "de": {"name": "Nemischa", "flag": "🇩🇪"},
    "tr": {"name": "Turkcha", "flag": "🇹🇷"},
    "ar": {"name": "Arabcha", "flag": "🇸🇦"},
    "fr": {"name": "Fransuzcha", "flag": "🇫🇷"},
    "zh-CN": {"name": "Xitoycha", "flag": "🇨🇳"},
    "es": {"name": "Ispancha", "flag": "🇪🇸"},
    "it": {"name": "Italyancha", "flag": "🇮🇹"},
    "tg": {"name": "Tojikcha", "flag": "🇹🇯"},
    "kk": {"name": "Qozoqcha", "flag": "🇰🇿"},
    "ky": {"name": "Qirg‘izcha", "flag": "🇰🇬"},
    "fa": {"name": "Forscha", "flag": "🇮🇷"},
}

# Asosiy klaviatura tugmalari:
BTN_AUTO = "🔄 Avto (UZ ⇄ RU)"
BTN_RU = "🇷🇺 Ruscha"
BTN_EN = "🇬🇧 Inglizcha"
BTN_KO = "🇰🇷 Koreyscha"
BTN_JA = "🇯🇵 Yaponcha"
BTN_DE = "🇩🇪 Nemischa"
BTN_TR = "🇹🇷 Turkcha"
BTN_MORE_LANGS = "🌐 Barcha 100+ tillar"
BTN_HELP = "ℹ️ Yordam"

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [BTN_AUTO],
        [BTN_RU, BTN_EN],
        [BTN_KO, BTN_JA],
        [BTN_DE, BTN_TR],
        [BTN_MORE_LANGS, BTN_HELP],
    ],
    resize_keyboard=True,
)


def get_lang_info(lang_code: str) -> tuple[str, str]:
    """Til kodi bo'yicha bayroq va nomni qaytaradi."""
    info = LANGUAGES.get(lang_code.lower())
    if info:
        return info["flag"], info["name"]
    return "🌐", lang_code.upper()


def _google_translate_advanced(text: str, sl: str = "auto", tl: str = "uz") -> dict:
    """
    Google Translate rasmiy mobil API orqali tarjima va lug'at ma'lumotlarini olish.
    """
    params = [
        ("client", "at"),
        ("dt", "t"),
        ("dt", "bd"),
        ("dt", "rm"),
        ("dt", "ss"),
        ("dj", "1"),
        ("sl", sl),
        ("tl", tl),
        ("q", text),
    ]
    response = requests.get(GOOGLE_API_URL, params=params, headers=GOOGLE_HEADERS, timeout=8)
    response.raise_for_status()
    data = response.json()

    sentences = data.get("sentences", [])
    translated_text = "".join(s.get("trans", "") for s in sentences if "trans" in s).strip()
    detected_lang = data.get("src", sl)

    # Transkripsiya (talaffuz):
    transliteration = ""
    for s in sentences:
        if "src_translit" in s:
            transliteration = s["src_translit"]
            break
        elif "translit" in s:
            transliteration = s["translit"]

    # Lug'at ma'lumotlari:
    dictionary_entries = []
    dict_data = data.get("dict", [])
    for entry in dict_data:
        pos = entry.get("pos", "")
        terms = entry.get("terms", [])
        if terms:
            dictionary_entries.append({
                "pos": pos,
                "terms": terms[:6],
            })

    # Sinonimlar:
    synonyms = []
    synsets = data.get("synsets", [])
    for syn in synsets:
        pos = syn.get("pos", "")
        for item in syn.get("entry", []):
            syn_words = item.get("synonym", [])
            if syn_words:
                synonyms.append(f"[{pos}] {', '.join(syn_words[:5])}")

    return {
        "text": text,
        "translated": translated_text,
        "src_lang": detected_lang,
        "target_lang": tl,
        "translit": transliteration,
        "dictionary": dictionary_entries,
        "synonyms": synonyms[:3],
    }


def format_translation_card(res: dict) -> str:
    """Tarjima natijasini Telegram uchun chiroyli HTML kartochka formatida tayyorlaydi."""
    src_flag, src_name = get_lang_info(res["src_lang"])
    tgt_flag, tgt_name = get_lang_info(res["target_lang"])

    orig_escaped = html.escape(res["text"])
    trans_escaped = html.escape(res["translated"])

    card = [
        f"<b>{src_flag} Asl matn ({src_name}):</b>",
        f"<i>{orig_escaped}</i>",
        "",
        f"<b>{tgt_flag} Tarjima ({tgt_name}):</b>",
        f"<b>{trans_escaped}</b>",
    ]

    # O'qilishi / Talaffuz (Koreys, Yapon, Xitoy, Rus, Arab kabi tillarda juda foydali):
    if res.get("translit"):
        card.append(f"\n🗣 <i>Talaffuz (O‘qilishi): {html.escape(res['translit'])}</i>")

    # Lug'at ma'lumotlari:
    if res.get("dictionary"):
        card.append("\n📚 <b>Lug‘at:</b>")
        pos_names = {
            "noun": "Ot",
            "verb": "Fe‘l",
            "adjective": "Sifat",
            "adverb": "Ravish",
            "pronoun": "Olmosh",
        }
        for d in res["dictionary"][:3]:
            pos_label = pos_names.get(d["pos"].lower(), d["pos"].capitalize())
            card.append(f"🔹 <i>{pos_label}:</i> {', '.join(d['terms'])}")

    # Sinonimlar:
    if res.get("synonyms"):
        card.append("\n🔁 <b>Sinonimlar:</b>")
        for syn in res["synonyms"]:
            card.append(f"• {html.escape(syn)}")

    return "\n".join(card)


def build_inline_buttons(src_lang: str, tgt_lang: str, text: str) -> InlineKeyboardMarkup:
    """Tarjima ostidagi interaktiv tugmalar."""
    short_text = text[:40]
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"🔄 Qayta o‘girish ({tgt_lang.upper()} ➡️ {src_lang.upper()})", callback_data=f"swap:{tgt_lang}:{src_lang}"),
        ],
        [
            InlineKeyboardButton("📋 Do‘stlarga ulashish", switch_inline_query=short_text),
            InlineKeyboardButton("❌ O‘chirish", callback_data="delete"),
        ],
    ])


def build_language_picker() -> InlineKeyboardMarkup:
    """100+ tillar menyusi uchun qulay tugmalar."""
    buttons = []
    row = []
    for code, info in LANGUAGES.items():
        btn = InlineKeyboardButton(f"{info['flag']} {info['name']}", callback_data=f"setlang:{code}")
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton("🔙 Menyuga qaytish", callback_data="close_lang")])
    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["target_lang"] = "auto"
    user = update.effective_user
    first_name = user.first_name if user and user.first_name else "do'stim"
    welcome_text = (
        f"🌟 <b>Assalomu alaykum, {html.escape(first_name)}!</b>\n\n"
        "Men **Ko‘p tilli Universal Tarjimon Botman!** 🚀\n\n"
        "Quyidagi mashhur tillarga bir lahzada tarjima qila olaman:\n"
        "• 🇰🇷 <b>Koreyscha</b>\n"
        "• 🇬🇧 <b>Inglizcha</b>\n"
        "• 🇯🇵 <b>Yaponcha</b>\n"
        "• 🇩🇪 <b>Nemischa</b>\n"
        "• 🇷🇺 <b>Ruscha</b>\n"
        "• 🇹🇷 <b>Turkcha</b> va yana 100+ dunyo tillari!\n\n"
        "<i>Quyidagi menyudan kerakli tilni tanlang yoki shunchaki istalgan matn yuboring!</i>"
    )
    await update.message.reply_text(
        welcome_text,
        reply_markup=MAIN_KEYBOARD,
        parse_mode=ParseMode.HTML,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📖 <b>Botdan foydalanish bo‘yicha qo‘llanma:</b>\n\n"
        "1. **Tugmalardan tilni tanlang:**\n"
        "   • 🇰🇷 <b>Koreyscha</b> — Koreys tiliga tarjima\n"
        "   • 🇬🇧 <b>Inglizcha</b> — Ingliz tiliga tarjima\n"
        "   • 🇯🇵 <b>Yaponcha</b> — Yapon tiliga tarjima\n"
        "   • 🇩🇪 <b>Nemischa</b> — Nemis tiliga tarjima\n"
        "   • 🇷🇺 <b>Ruscha</b> — Rus tiliga tarjima\n"
        "   • 🔄 <b>Avto (UZ ⇄ RU)</b> — O‘zbekcha ⇄ Ruscha avtomatik\n\n"
        "2. **Tezkor buyruqlar:**\n"
        "   • `/ko <matn>` — Koreyschaga o‘girish\n"
        "   • `/en <matn>` — Inglizchaga o‘girish\n"
        "   • `/ja <matn>` — Yaponchaga o‘girish\n"
        "   • `/de <matn>` — Nemis tiliga o‘girish\n"
        "   • `/ru <matn>` — Ruschaga o‘girish\n"
        "   • `/uz <matn>` — O‘zbekchaga o‘girish\n\n"
        "3. **Guruhlarda va do‘stlar bilan ishlatish (Inline):**\n"
        "   Istalgan chatda <code>@Tarjimon_8bot Salom</code> deb yozsangiz, to‘g‘ridan-to‘g‘ri tarjimani jo‘nata olasiz!"
    )
    await update.message.reply_text(text, reply_markup=MAIN_KEYBOARD, parse_mode=ParseMode.HTML)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    if not text:
        return

    # Menyudagi til tugmalari bosilganda:
    lang_btn_map = {
        BTN_AUTO: ("auto", "🔄 Avtomatik (UZ ⇄ RU) rejimi tanlandi!"),
        BTN_RU: ("ru", "🇷🇺 <b>Rus tili</b> tanlandi! Istalgan matn yuboring, ruschaga o‘giraman."),
        BTN_EN: ("en", "🇬🇧 <b>Ingliz tili</b> tanlandi! Istalgan matn yuboring, inglizchaga o‘giraman."),
        BTN_KO: ("ko", "🇰🇷 <b>Koreys tili</b> tanlandi! Istalgan matn yuboring, koreys tiliga o‘giraman."),
        BTN_JA: ("ja", "🇯🇵 <b>Yapon tili</b> tanlandi! Istalgan matn yuboring, yapon tiliga o‘giraman."),
        BTN_DE: ("de", "🇩🇪 <b>Nemis tili</b> tanlandi! Istalgan matn yuboring, nemis tiliga o‘giraman."),
        BTN_TR: ("tr", "🇹🇷 <b>Turk tili</b> tanlandi! Istalgan matn yuboring, turk tiliga o‘giraman."),
    }

    if text in lang_btn_map:
        target_lang, msg = lang_btn_map[text]
        context.user_data["target_lang"] = target_lang
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
        return

    elif text == BTN_MORE_LANGS:
        await update.message.reply_text(
            "🌐 <b>Quyidagi 100+ tillardan birini tanlang:</b>",
            reply_markup=build_language_picker(),
            parse_mode=ParseMode.HTML,
        )
        return

    elif text == BTN_HELP:
        await help_command(update, context)
        return

    # Buyruqlarni o'tkazib yuborish:
    if text.startswith("/"):
        return

    # Tanlangan maqsadli til:
    target_lang = context.user_data.get("target_lang", "auto")

    try:
        if target_lang == "auto":
            # Avto rejim (O'zbekcha ⇄ Ruscha)
            res = await asyncio.to_thread(_google_translate_advanced, text, sl="auto", tl="uz")
            if res["src_lang"] == "uz" or any(ch in text.lower() for ch in "ўғҳқ"):
                res = await asyncio.to_thread(_google_translate_advanced, text, sl="uz", tl="ru")
        else:
            # Aniq til tanlangan (masalan: ko, en, ja, de, ru, tr...)
            # Dastlab ushbu tanlangan tilga o'giramiz:
            res = await asyncio.to_thread(_google_translate_advanced, text, sl="auto", tl=target_lang)

            # Agar yuborilgan matn allaqachon ushbu tilda bo'lsa (masalan, koreyscha rejimida koreyscha yozsa):
            # Uni o'zbek tiliga o'giramiz:
            if res["src_lang"] == target_lang:
                res = await asyncio.to_thread(_google_translate_advanced, text, sl=target_lang, tl="uz")

        card_html = format_translation_card(res)
        inline_kb = build_inline_buttons(res["src_lang"], res["target_lang"], res["text"])

        context.user_data["last_text"] = text
        await update.message.reply_text(card_html, reply_markup=inline_kb, parse_mode=ParseMode.HTML)

    except Exception as exc:
        logging.exception("Tarjima xatosi: %s", exc)
        await update.message.reply_text("Kechirasiz, tarjima qilishda xatolik yuz berdi. Iltimos, qayta urinib ko‘ring.")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "delete":
        try:
            await query.message.delete()
        except Exception:
            pass
        return

    elif data == "close_lang":
        await query.message.edit_text("✅ Asosiy menyudasiz. Istalgan matn yuboring!")
        return

    elif data.startswith("setlang:"):
        code = data.split(":")[1]
        context.user_data["target_lang"] = code
        flag, name = get_lang_info(code)
        await query.message.edit_text(
            f"✅ <b>Maqsadli til tanlandi:</b> {flag} <b>{name}</b>\n\n"
            f"Endi istalgan matn yuboring — bot uni <b>{name}</b> tiliga tarjima qilib beradi!",
            parse_mode=ParseMode.HTML,
        )
        return

    elif data.startswith("swap:"):
        parts = data.split(":")
        new_sl, new_tl = parts[1], parts[2]
        last_text = context.user_data.get("last_text")

        if not last_text:
            await query.answer("Eski matn topilmadi.", show_alert=True)
            return

        try:
            res = await asyncio.to_thread(_google_translate_advanced, last_text, sl=new_sl, tl=new_tl)
            card_html = format_translation_card(res)
            inline_kb = build_inline_buttons(res["src_lang"], res["target_lang"], res["text"])
            await query.message.reply_text(card_html, reply_markup=inline_kb, parse_mode=ParseMode.HTML)
        except Exception as exc:
            logging.exception("Teskari tarjima xatosi: %s", exc)
            await query.answer("Tarjima qilishda xatolik yuz berdi.")


async def quick_cmd_translate(update: Update, context: ContextTypes.DEFAULT_TYPE, target_lang: str) -> None:
    """Tezkor buyruqlar orqali tarjima qilish (/ko, /en, /ja, /de, /ru, /uz...)."""
    text = " ".join(context.args)
    flag, name = get_lang_info(target_lang)
    if not text:
        await update.message.reply_text(f"Iltimos, matn yozing. Masalan:\n/{target_lang} Salom dunyo")
        return
    try:
        res = await asyncio.to_thread(_google_translate_advanced, text, sl="auto", tl=target_lang)
        card_html = format_translation_card(res)
        inline_kb = build_inline_buttons(res["src_lang"], res["target_lang"], res["text"])
        await update.message.reply_text(card_html, reply_markup=inline_kb, parse_mode=ParseMode.HTML)
    except Exception as exc:
        logging.exception("Buyruq tarjima xatosi: %s", exc)
        await update.message.reply_text(f"Tarjima xatosi yuz berdi.")


async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Telegram inline qidiruv (har qanday guruh yoki shaxsiy chatda turib tarjima qilish)."""
    query = update.inline_query.query.strip()
    if not query:
        return

    try:
        res_ru = await asyncio.to_thread(_google_translate_advanced, query, sl="auto", tl="ru")
        res_en = await asyncio.to_thread(_google_translate_advanced, query, sl="auto", tl="en")
        res_ko = await asyncio.to_thread(_google_translate_advanced, query, sl="auto", tl="ko")
        res_ja = await asyncio.to_thread(_google_translate_advanced, query, sl="auto", tl="ja")

        results = [
            InlineQueryResultArticle(
                id="1",
                title=f"🇷🇺 Ruscha: {res_ru['translated'][:30]}",
                description=res_ru["translated"],
                input_message_content=InputTextMessageContent(
                    f"🇷🇺 <b>Ruscha tarjima:</b>\n{html.escape(res_ru['translated'])}",
                    parse_mode=ParseMode.HTML,
                ),
            ),
            InlineQueryResultArticle(
                id="2",
                title=f"🇬🇧 Inglizcha: {res_en['translated'][:30]}",
                description=res_en["translated"],
                input_message_content=InputTextMessageContent(
                    f"🇬🇧 <b>Inglizcha tarjima:</b>\n{html.escape(res_en['translated'])}",
                    parse_mode=ParseMode.HTML,
                ),
            ),
            InlineQueryResultArticle(
                id="3",
                title=f"🇰🇷 Koreyscha: {res_ko['translated'][:30]}",
                description=res_ko["translated"],
                input_message_content=InputTextMessageContent(
                    f"🇰🇷 <b>Koreyscha tarjima:</b>\n{html.escape(res_ko['translated'])}\n<i>{html.escape(res_ko.get('translit', ''))}</i>",
                    parse_mode=ParseMode.HTML,
                ),
            ),
            InlineQueryResultArticle(
                id="4",
                title=f"🇯🇵 Yaponcha: {res_ja['translated'][:30]}",
                description=res_ja["translated"],
                input_message_content=InputTextMessageContent(
                    f"🇯🇵 <b>Yaponcha tarjima:</b>\n{html.escape(res_ja['translated'])}\n<i>{html.escape(res_ja.get('translit', ''))}</i>",
                    parse_mode=ParseMode.HTML,
                ),
            ),
        ]
        await update.inline_query.answer(results, cache_time=10)
    except Exception as exc:
        logging.exception("Inline query xatosi: %s", exc)


def main() -> None:
    # Render.com Web Service uchun mini veb-serverni ishga tushirish (Deploy failed bo'lmasligi uchun):
    threading.Thread(target=start_render_web_server, daemon=True).start()

    while True:
        try:
            try:
                asyncio.get_event_loop()
            except RuntimeError:
                asyncio.set_event_loop(asyncio.new_event_loop())

            app = ApplicationBuilder().token(TOKEN).build()

            app.add_handler(CommandHandler("start", start))
            app.add_handler(CommandHandler("help", help_command))

            # Tezkor til buyruqlari:
            app.add_handler(CommandHandler("ko", lambda u, c: quick_cmd_translate(u, c, "ko")))
            app.add_handler(CommandHandler("en", lambda u, c: quick_cmd_translate(u, c, "en")))
            app.add_handler(CommandHandler("ja", lambda u, c: quick_cmd_translate(u, c, "ja")))
            app.add_handler(CommandHandler("de", lambda u, c: quick_cmd_translate(u, c, "de")))
            app.add_handler(CommandHandler("ru", lambda u, c: quick_cmd_translate(u, c, "ru")))
            app.add_handler(CommandHandler("uz", lambda u, c: quick_cmd_translate(u, c, "uz")))
            app.add_handler(CommandHandler("tr", lambda u, c: quick_cmd_translate(u, c, "tr")))

            app.add_handler(CallbackQueryHandler(handle_callback))
            app.add_handler(InlineQueryHandler(inline_query_handler))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

            print("Ko‘p tilli Universal Tarjimon Bot ishga tushdi...")
            app.run_polling(allowed_updates=Update.ALL_TYPES)
        except Exception as exc:
            logging.error("Botda xatolik yoki internet uzildi: %s. 5 soniyadan so‘ng qayta ulanadi...", exc)
            time.sleep(5)


if __name__ == "__main__":
    main()
