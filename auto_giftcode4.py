"""
====================================================================
  BOT QUET & NAP GIFTCODE TELEPET 24/7 (BAN TOI UU NANG CAO)
  Tai khoan: ACC 4 (@Wind_trader - ID: 8735204819)
  TINH NANG NANG CAP:
      - TU DONG LAY INIT_DATA MOI QUA TELETHON (Khong bao gio het han)
      - BE KHOA MOI DANG LINK RUT GON (Layma, Link4m, Linktop, Traffictop, TrafficHub, Traffic68, v.v.)
      - CHE DO AUTO-FARM VO HAN: Tu dong tao / xoay vong tai khoan web cao sach kho ma
      - Tu dong nap thang Xu vao vi TelePet ngay sau khi lay code
      - Vong lap quet lien tuc 24/7 (Mac dinh: 2 phut / lan)
      - Tu dong reset danh sach ma da nap luc 00:00:05 GMT+7 moi ngay
====================================================================
"""

import time
import requests
import urllib.parse
import re
import os
import base64
import random
import string
import asyncio
import sqlite3
from datetime import datetime, timezone, timedelta
from colorama import Fore, Style, init

from telethon import TelegramClient
from telethon.tl.functions.messages import RequestWebViewRequest

init(autoreset=True)

# -----------------------------------------------------------------
#  CAU HINH HE THONG
# -----------------------------------------------------------------
API_ID = 39182276
API_HASH = "f02b155d895a3a3fbf8a1cbe810b5338"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_PATH = os.path.join(SCRIPT_DIR, "telepet_acc4")

API_URL = "https://kien.kiemtienngay.us/public/api.php"
FALLBACK_INIT_DATA = "query_id=AAHTpagIBAAAANOlqAiQ0PGe&user=%7B%22id%22%3A8735204819%2C%22first_name%22%3A%22Uweuweuweuweu%22%2C%22last_name%22%3A%22Osas%22%2C%22username%22%3A%22Wind_trader%22%2C%22language_code%22%3A%22vi%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FDf9UdWj_lcG78CMooXZXyDrc8fEcf5WhBgsEGeTbFMByWu-kovHAeZlzin8RyNAt.svg%22%7D&auth_date=1793281870&signature=bNSi2MX02oj99MWLXRvg6r00mp3-7KwsshBifoG1AsuwpH45yCaBGjMXQRob_--zWrx8bBw8Yn-QnHP8s41_Bg&hash=c7c6fdea481982de2cefda0c0662fffeab0c98e822b2aa1b52473621a51143ca"
CURRENT_INIT_DATA = FALLBACK_INIT_DATA
REDEEMED_CODES_TODAY = set()

# Chu ky quet giftcode moi (giay)
SCAN_INTERVAL_SECONDS = 60  # 1 phut quet 1 lan  # 2 phut quet 1 lan

# CHE DO AUTO-FARM VO HAN:
# Khi bat, bot se tu dong xoay vong tai khoan web de cao sach kho ma 200k+ code
AUTO_FARM_ROTATION = True 
FARM_ACCOUNTS_PER_CYCLE = 1  # So tai khoan web tao moi moi chu ky (~12-16 ma ~70k-100k Xu / acc)

HEADERS_TELEPET = {
    "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
    "origin": "https://kien.kiemtienngay.us",
    "referer": "https://kien.kiemtienngay.us/public/nhiemvu.php",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36",
    "accept": "*/*",
}

DEFAULT_WEB_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://kiemtienngay.us/'
}

web_session = requests.Session()
web_session.headers.update(DEFAULT_WEB_HEADERS)
WEB_USER = "hungzai_bot1_2026"
WEB_PASS = "Pass123456@"

def log(tag, msg, color=Fore.WHITE):
    t = datetime.now().strftime("%H:%M:%S")
    print(f"[{t}] [{tag}] {color}{msg}{Style.RESET_ALL}", flush=True)

# -----------------------------------------------------------------
#  HAM TU DONG LAY INIT_DATA MOI TU TELEGRAM
# -----------------------------------------------------------------
def ensure_valid_session():
    """Kiem tra tinh toan ven cua file sqlite session, tu sua neu bi loi malformed"""
    session_file = f"{SESSION_PATH}.session"
    is_valid = False
    if os.path.exists(session_file):
        try:
            conn = sqlite3.connect(session_file)
            c = conn.cursor()
            c.execute("PRAGMA integrity_check")
            res = c.fetchall()
            c.close()
            conn.close()
            if res and res[0][0] == "ok":
                is_valid = True
        except Exception:
            is_valid = False

    if not is_valid and os.path.exists(session_file):
        for ext in [".session", ".session-journal"]:
            fpath = f"{SESSION_PATH}{ext}"
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except Exception:
                    pass

        raw_secret = os.getenv("TELEGRAM_SESSION_B64_ACC4") or os.getenv("TELEGRAM_SESSION_B64")
        if raw_secret:
            clean_b64 = re.sub(r"\s+", "", raw_secret.strip())
            try:
                data = base64.b64decode(clean_b64)
                with open(session_file, "wb") as f:
                    f.write(data)
                log("INFO", f"Da tu dong sua & khoi phuc session Telegram ({len(data)} bytes)", Fore.CYAN)
            except Exception as e:
                log("ERR", f"Khong the giai ma base64 session: {e}", Fore.RED)

async def fetch_fresh_init_data():
    global CURRENT_INIT_DATA
    log("+", "Dang ket noi Telegram de lay init_data moi...", Fore.CYAN)
    
    session_file = f"{SESSION_PATH}.session"
    session_secret = os.getenv("TELEGRAM_SESSION_B64_ACC4") or os.getenv("TELEGRAM_SESSION_B64")
    if session_secret and (not os.path.exists(session_file) or os.path.getsize(session_file) < 25000):
        try:
            clean_b64 = re.sub(r"\s+", "", session_secret.strip())
            with open(session_file, "wb") as f:
                f.write(base64.b64decode(clean_b64))
        except Exception as e:
            log("WARN", f"Khong the khoi phuc session tu Secret: {e}", Fore.YELLOW)

    if not os.path.exists(session_file):
        log("INFO", "Su dung token init_data san co (@Wind_trader)...", Fore.CYAN)
        CURRENT_INIT_DATA = CURRENT_INIT_DATA or FALLBACK_INIT_DATA
        return CURRENT_INIT_DATA

    ensure_valid_session()
    try:
        client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
        await client.connect()
        if not await client.is_user_authorized():
            log("WARN", "Session telepet_acc4 chua duoc xac thuc, dung init_data san co!", Fore.YELLOW)
            await client.disconnect()
            CURRENT_INIT_DATA = CURRENT_INIT_DATA or FALLBACK_INIT_DATA
            return CURRENT_INIT_DATA
        
        bot = await client.get_input_entity("kiemtien6789_bot")
        web_view = await client(RequestWebViewRequest(
            peer=bot,
            bot=bot,
            platform="android",
            from_bot_menu=False,
            url="https://kien.kiemtienngay.us/public/"
        ))
        await client.disconnect()

        fragment = urllib.parse.urlparse(web_view.url).fragment
        params = urllib.parse.parse_qs(fragment)
        fresh = params.get("tgWebAppData", [None])[0]
        if fresh:
            CURRENT_INIT_DATA = fresh
            log("OK", "Da cap nhat init_data thanh cong!", Fore.GREEN)
        return CURRENT_INIT_DATA
    except Exception as e:
        log("WARN", f"Loi ket noi Telethon ({e}), dung init_data san co!", Fore.YELLOW)
        CURRENT_INIT_DATA = CURRENT_INIT_DATA or FALLBACK_INIT_DATA
        return CURRENT_INIT_DATA

def get_fresh_init_data_sync():
    return asyncio.run(fetch_fresh_init_data())

def refresh_profile():
    try:
        r = requests.post(API_URL, headers=HEADERS_TELEPET, data={"action": "me", "init_data": CURRENT_INIT_DATA}, timeout=10)
        res = r.json()
        if res.get("ok"):
            return res.get("user")
    except:
        pass
    return None

def init_web_account():
    try:
        r = web_session.get("https://kiemtienngay.us/index.php", timeout=8)
        if "Tai khoan:" not in r.text and "Dang xuat" not in r.text:
            web_session.post("https://kiemtienngay.us/register.php", data={
                "username": WEB_USER,
                "password": WEB_PASS,
                "confirm_password": WEB_PASS,
                "referrer": ""
            }, timeout=8)
            web_session.post("https://kiemtienngay.us/login.php", data={"username": WEB_USER, "password": WEB_PASS}, timeout=8)
        return True
    except Exception as e:
        log("ERR", f"Loi ket noi web kiemtienngay.us: {e}", Fore.RED)
        return False

def create_fresh_web_session():
    """Tu dong tao tai khoan web kiemtienngay.us ngau nhien de mo khoa toan bo kho GiftCode moi"""
    s = requests.Session()
    s.headers.update(DEFAULT_WEB_HEADERS)
    uname = "bot_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    pwd = "Pass123456@"
    try:
        r = s.post("https://kiemtienngay.us/register.php", data={
            "username": uname,
            "password": pwd,
            "confirm_password": pwd,
            "referrer": ""
        }, timeout=8)
        if r.status_code == 200:
            return s, uname
    except Exception as e:
        log("WARN", f"Khong tao duoc tai khoan farm: {e}", Fore.YELLOW)
    return None, None

def extract_giftcode_target_url(loc, session):
    """Be khoa moi loai link rut gon de trich xuat link giftcode goc"""
    if not loc:
        return None
        
    # 1. Link truc tiep
    if "giftcode.php?key=" in loc:
        return loc

    # 2. Link rut gon chua ?url=... (Layma, link4m, linktop, traffichub, yeujob, traffic68, trafficvn, trafficviet, v.v.)
    try:
        parsed = urllib.parse.urlparse(loc)
        target = urllib.parse.parse_qs(parsed.query).get("url", [None])[0]
        if target and "giftcode.php?key=" in target:
            return target
    except:
        pass

    # 3. Link rut gon traffictop.net hoac cac trang chuyen huong khac
    try:
        r = session.get(loc, headers=DEFAULT_WEB_HEADERS, timeout=8, allow_redirects=True)
        # Bắt biến originalUrl trong JS
        m_orig = re.search(r"var\s+originalUrl\s*=\s*['\"]([^'\"]+)['\"]", r.text)
        if m_orig:
            return m_orig.group(1)

        # Bắt link giftcode.php?key= trong HTML
        m_url = re.search(r"https?://(?:kien\.)?kiemtienngay\.us/giftcode\.php\?key=[a-zA-Z0-9]+", r.text)
        if m_url:
            return m_url.group(0)
    except Exception as e:
        log("WARN", f"Khong the doc link rut gon {loc[:45]}: {e}", Fore.YELLOW)

    return None

def process_single_task(session, tid, round_num, acc_tag=""):
    """Thuc hien 1 nhiem vu: be khoa -> tao code -> nap truc tiep vao TelePet"""
    global CURRENT_INIT_DATA, REDEEMED_CODES_TODAY
    url = f"https://kiemtienngay.us/nbk222/giftcode.php?task_id={tid}"
    try:
        r = session.get(url, allow_redirects=False, timeout=8)
        if r.status_code == 200 and "BẠN ĐÃ LẤY GIFTCODE NÀY RỒI" in r.text:
            return 0

        loc = r.headers.get("Location", "")
        if not loc:
            return 0

        target_url = extract_giftcode_target_url(loc, session)
        if not target_url:
            return 0

        headers_gift = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': target_url
        }
        r_claim = session.post(target_url, data="confirm_gift=1", headers=headers_gift, timeout=8)
        try:
            data = r_claim.json()
        except:
            return 0

        if data.get("status") == "ok":
            code = data.get("code")
            if not code or code in REDEEMED_CODES_TODAY:
                return 0
            
            reward_str = str(data.get("reward", "5000")).replace(",", "")
            reward_val = int(reward_str) if reward_str.isdigit() else 5000

            # Nap code ngay lap tuc vao TelePet
            redeem_data = {
                "action": "giftcode",
                "code": code,
                "init_data": CURRENT_INIT_DATA
            }
            r_tele = requests.post(API_URL, headers=HEADERS_TELEPET, data=redeem_data, timeout=8)
            res_tele = r_tele.json()

            if res_tele.get("ok"):
                earned = res_tele.get("amount", reward_val)
                REDEEMED_CODES_TODAY.add(code)
                log("GIFT", f"{acc_tag}Task #{tid} (L{round_num}): Ma [{code}] -> +{earned:,} Xu da nap!", Fore.GREEN)
                return earned
            else:
                err_msg = str(res_tele.get('error', ''))
                if "chào cậu" in err_msg.lower() or "hi chào" in err_msg.lower():
                    log("LIMIT", f"{acc_tag}Tai khoan TelePet da cham NGUONG TOI DA GiftCode trong ngay! Server chan: '{err_msg}'", Fore.RED)
                    return -999  # Ma bao hieu da bi gioi han ngay
                if any(k in err_msg.lower() for k in ["da", "toi da", "het", "ton tai"]):
                    REDEEMED_CODES_TODAY.add(code)
                log("WARN", f"{acc_tag}Task #{tid}: Ma [{code}] -> {err_msg}", Fore.YELLOW)
    except Exception as e:
        log("ERR", f"{acc_tag}Loi Task #{tid}: {e}", Fore.RED)
    return 0

def scan_account_tasks(session, acc_name=""):
    """Quet sach tat ca nhiem vu cua 1 tai khoan web (2 luot)"""
    try:
        r_home = session.get("https://kiemtienngay.us/index.php", timeout=8)
        task_links = re.findall(r'href=["\']([^"\']*giftcode\.php\?task_id=\d+)["\']', r_home.text)
        task_ids = sorted(list(set([int(re.search(r'task_id=(\d+)', l).group(1)) for l in task_links])))
    except:
        task_ids = []

    if not task_ids:
        task_ids = [1, 2, 3, 4, 5, 6, 8, 9, 10, 13, 14, 15, 16]

    tag = f"[{acc_name}] " if acc_name else ""
    log("INFO", f"{tag}Dang quet {len(task_ids)} nhiem vu GiftCode...", Fore.CYAN)

    acc_coins = 0
    acc_codes = 0

    for round_num in [1, 2]:
        for tid in task_ids:
            earned = process_single_task(session, tid, round_num, tag)
            if earned == -999:
                return -999, 0
            if earned > 0:
                acc_coins += earned
                acc_codes += 1
            time.sleep(1)

    if acc_codes > 0:
        log("DONE", f"{tag}DA NAP XONG {acc_codes} MA MOI | +{acc_coins:,} Xu!", Fore.GREEN)
    return acc_coins, acc_codes

def scan_and_redeem_giftcodes():
    u = refresh_profile()
    if u and u.get("locked") == 2:
        log("LIMIT", "Tai khoan TelePet da cham gioi han GiftCode hom nay (locked=2)! Tam dung farm den ngay mai de an toan.", Fore.YELLOW)
        return -999

    total_coins_earned = 0
    total_codes_earned = 0

    # 1. Quet tai khoan chinh WEB_USER
    if init_web_account():
        coins, codes = scan_account_tasks(web_session, "Chính")
        if coins == -999:
            return -999
        total_coins_earned += coins
        total_codes_earned += codes

    # 2. Che do Auto-Farm: Tao tai khoan web moi de hut tron kho 200,000+ GiftCode
    if AUTO_FARM_ROTATION:
        for idx in range(1, FARM_ACCOUNTS_PER_CYCLE + 1):
            s_fresh, fresh_user = create_fresh_web_session()
            if s_fresh and fresh_user:
                log("FARM", f"Bat dau vong Farm #{idx} voi tai khoan: {fresh_user}", Fore.MAGENTA)
                f_coins, f_codes = scan_account_tasks(s_fresh, f"Farm-{fresh_user[4:]}")
                if f_coins == -999:
                    return -999
                total_coins_earned += f_coins
                total_codes_earned += f_codes
                time.sleep(2)

    return total_coins_earned

def get_seconds_until_midnight_vn():
    vn_tz = timezone(timedelta(hours=7))
    now_vn = datetime.now(vn_tz)
    tomorrow = now_vn.date() + timedelta(days=1)
    midnight = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 5, tzinfo=vn_tz)
    return int((midnight - now_vn).total_seconds())

def sleep_until_midnight():
    """Ngu yen den 00:00:05 GMT+7 roi tu dong thuc giac chay tiep ngay moi"""
    sec_to_midnight = get_seconds_until_midnight_vn()
    hrs, rem = divmod(sec_to_midnight, 3600)
    mins, secs = divmod(rem, 60)
    print("\n" + "="*66)
    log("LIMIT", f"Tai khoan da dat gioi han GiftCode hom nay (locked=2)!", Fore.YELLOW)
    log("SLEEP", f"Bot se ngu {hrs}h {mins}p {secs}s cho den 00:00:05 GMT+7 de tu dong reset ngay moi...", Fore.MAGENTA)
    print("="*66 + "\n")

    while True:
        sec_left = get_seconds_until_midnight_vn()
        if sec_left <= 5:
            break
        # In nhip tim moi 10 phut de giu runner GitHub luon song
        h_left, r_left = divmod(sec_left, 3600)
        m_left, s_left = divmod(r_left, 60)
        sleep_chunk = min(sec_left, 300) # ngu tung block 5 phut
        time.sleep(sleep_chunk)
        if sec_left > 5:
            log("WAIT", f"Dang ngu cho 00:00 GMT+7 (con lai {h_left}h {m_left}p)...", Fore.MAGENTA)

    log("RESET", "DA TOI 00:00:05 GMT+7! Reset danh sach ma va bat dau ngay moi...", Fore.GREEN)
    REDEEMED_CODES_TODAY.clear()
    get_fresh_init_data_sync()

def main():
    print(f"""
{Fore.MAGENTA}====================================================================
|  TOOL QUET & BE KHOA GIFTCODE TELEPET 24/7 (TOI UU NANG CAO)     |
|  Tai khoan: @Wind_trader (ID: 8735204819)                   |
|  - Chu ky quet: {SCAN_INTERVAL_SECONDS} giay / lan                             |
|  - Che do Auto-Farm vo han: {'BAT' if AUTO_FARM_ROTATION else 'TAT'}                                 |
|  - Tu dong lay token init_data tu Telegram                       |
|  - Tu dong be khoa moi link rut gon & nap xu truc tiep          |
|  - Tu dong reset danh sach ma luc 00:00:05 GMT+7                 |
===================================================================={Style.RESET_ALL}
    """)

    # 1. Lay token khoi dong
    get_fresh_init_data_sync()
    curr_u = refresh_profile()
    if curr_u:
        log("LOGIN", f"Ket noi: {curr_u.get('name')} (@{curr_u.get('username')}) | Xu: {curr_u.get('coins'):,}", Fore.GREEN)
        if curr_u.get("locked") == 2:
            sleep_until_midnight()
    else:
        log("ERR", "Khong the xac thuc Telegram WebApp!", Fore.RED)
        return

    last_refresh_time = time.time()

    while True:
        # Kiem tra neu sang ngay moi thi reset ma da nap
        if get_seconds_until_midnight_vn() <= 10:
            REDEEMED_CODES_TODAY.clear()
            log("RESET", "DA SANG NGAY MOI! Reset danh sach ma va lay init_data moi...", Fore.GREEN)
            get_fresh_init_data_sync()
            time.sleep(15)

        # Tu dong lam moi token Telethon moi 2 tieng de khong bao gio bi timeout
        if time.time() - last_refresh_time > 7200:
            get_fresh_init_data_sync()
            last_refresh_time = time.time()

        # Quet va nap giftcode
        status = scan_and_redeem_giftcodes()

        u = refresh_profile()
        if u:
            log("COIN", f"So du hien tai: {u.get('coins'):,} Coins", Fore.CYAN)

        # Neu bi chan limit thi ngu den 00:00:05 GMT+7
        if status == -999 or (u and u.get("locked") == 2):
            sleep_until_midnight()
        else:
            log("SLEEP", f"Nghi {SCAN_INTERVAL_SECONDS}s (1 phut) truoc khi quet chu ky tiep theo...", Fore.WHITE)
            time.sleep(SCAN_INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[STOP] Da dung bot quet GiftCode.{Style.RESET_ALL}")
