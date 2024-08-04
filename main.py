import base64
import os
import json
import time
import concurrent.futures
from CSolver.Hcap.hcap import Solver
from colorama import Fore, Style
from tls_client import Session
from random import choice
import ua_generator

gray = Fore.LIGHTBLACK_EX
orange = Fore.LIGHTYELLOW_EX
lightblue = Fore.LIGHTBLUE_EX

class log:
    @staticmethod
    def slog(type, color, message, time):
        if time != None:
            msg = f"{gray} [ {color}{type}{gray} ] [ {color}{message}{gray} ] [ {Fore.CYAN}{time:.2f}s{gray} ]"
        else: 
            msg = f"{gray} [ {color}{type}{gray} ] [ {color}{message}{gray} ]"
        print(log.center(msg))
        
    @staticmethod
    def ilog(type, color, message):
        msg = f"{gray} [ {color}{type}{gray} ] [ {color}{message}{gray} ]"
        inputmsg = input(log.center(msg) + " ")
        return inputmsg

    @staticmethod
    def log(type, color, message):
        msg = f"{gray} [ {color}{type}{gray} ] [ {color}{message}{gray} ]{Style.RESET_ALL}"
        print(log.center(msg))

    @staticmethod
    def success(message, time):
        log.slog('+', Fore.GREEN, message, time)

    @staticmethod
    def fail(message):
        log.log('X', Fore.RED, message)

    @staticmethod
    def warn(message):
        log.log('!', Fore.YELLOW, message)

    @staticmethod
    def info(message):
        log.log('i', lightblue, message)
        
    @staticmethod
    def input(message):
        return log.ilog('i', lightblue, message)

    @staticmethod
    def working(message):
        log.log('-', orange, message)

    @staticmethod
    def center(text):
        t_width = 80
        textlen = len(text)
        if textlen >= t_width:
            return text
        l_pad = (t_width - textlen) // 2
        return ' ' * l_pad + text

# Global counters
joined = 0
solved = 0
errors = 0

# Load tokens from file
with open('tokens.txt', 'r') as file:
    lines = file.read().splitlines()
    tokens = [line.split(":")[-1] for line in lines]

# UI function
def ui():
    print(Fore.CYAN + """
\t   _____            _               
\t  / ____|          | |              
\t | |    _   _ _ __ | |__   ___ _ __ 
\t | |   | | | | '_ \| '_ \ / _ \ '__|
\t | |___| |_| | |_) | | | |  __/ |   
\t  \_____\__, | .__/|_| |_|\___|_|   
\t         __/ | |                    
\t        |___/|_|                   
""")
ui()
print("\n")

def solve(url, key, rqdata, proxy):
    global solved
    with open("config.json") as conf:
        config = json.load(conf)
        startedSolving = time.time()
        solution = Solver(config['CSolver-key']).solve('hCaptchaEnterprise', key, url, proxy, rqdata)    
        log.success(f"Solved --> {solution[:30]}...", round(time.time()-startedSolving))
        solved += 1
        return solution

def xtrack(ua):
    return base64.b64encode(json.dumps({
        "os": str(ua.ch.platform),
        "browser": str(ua.browser),
        "device": str(ua.platform),
        "system_locale": "en-US",
        "browser_user_agent": str(ua),
        "browser_version": "110.0.5481.192",
        "os_version": ua.ch.platform_version,
        "referrer": "",
        "referring_domain": "",
        "referrer_current": "",
        "referring_domain_current": "",
        "release_channel": "stable",
        "client_build_number": 5645383,
        "client_event_source": None
    }).encode()).decode()

def join(token):
    global joined, solved, errors
    ua = ua_generator.generate(platform='ios', browser='safari')
    with open("config.json") as jn:
        check = json.load(jn)
        invite_code = check.get('invite')
    proxy = choice(open("proxies.txt", "r").readlines()).strip() if len(open("proxies.txt", "r").readlines()) != 0 else None

    session = Session(client_identifier="safari_ios_17_1", random_tls_extension_order=True)

    if proxy and proxy.count(":") == 1:
        session.proxies = {
            "http": "http://" + proxy,
            "https": "http://" + proxy
        }
    elif proxy and proxy.count(":") == 3:
        username, password, ip, port = proxy.split(":")
        session.proxies = {
            "http": f"http://{username}:{password}@{ip}:{port}",
            "https": f"http://{username}:{password}@{ip}:{port}"
        }

    headers_finger = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Referer': 'https://discord.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-GPC': '1',
        'User-Agent': str(ua),
        'X-Track': xtrack(ua),
    }

    response = session.get('https://discord.com/api/v9/experiments', headers=headers_finger)
    if response.status_code == 200:
        data = response.json()
        fingerprint = data["fingerprint"]
        log.info(f"Fingerprint --> {fingerprint[:20]}...")
    else:
        errors += 1

    headers = {
        "authorization": token,
        "x-super-properties": xtrack(ua),
        "sec-fetch-dest": "empty",
        "x-debug-options": "bugReporterEnabled",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "accept": "*/*",
        "accept-language": "en-GB",
        "user-agent": str(ua),
        "x-fingerprint": fingerprint
    }

    while True:
        sj = time.time()
        response = session.post(f"https://discord.com/api/v9/invites/{invite_code}", headers=headers)
        if response.status_code == 400:
            log.working(f"Solving --> {token[:50]}...")
            captcha_solution = solve(
                "https://discord.com",
                response.json()['captcha_sitekey'],
                response.json()['captcha_rqdata'],
                proxy
            )
            payload = {
                "captcha_key": captcha_solution,
                'captcha_rqtoken': response.json()['captcha_rqtoken']
            }
            newresponse = session.post(f"https://discord.com/api/v9/invites/{invite_code}", headers=headers, json=payload)
            if newresponse.status_code == 200:
                nj = time.time()
                log.success(f"Joined --> {token[:50]}...", round(nj-sj, 2))
                joined += 1
                change_nickname(ua, session, invite_code, token)
                break
            else:
                log.fail(f"Failed to join after captcha --> {token[:50]}... --> {newresponse.text}")
                errors += 1
        elif response.status_code == 200:
            nj = time.time()
            log.success(f"Joined --> {token[:50]}...", round(nj-sj, 2))
            joined += 1
            change_nickname(ua, session, invite_code, token)
            break
        else:
            log.fail(f"Failed to join --> {token[:50]}... --> {response.text}")
            errors += 1
            break

def change_nickname(ua, session, token):
    with open("config.json") as config_file:
        config_data = json.load(config_file)
        invite_url = f"https://discord.gg/{config_data.get('invite')}"

    def get_guild_id(invite_url):
        invite_code = invite_url.split('/')[-1]
        response = session.get(f'https://discord.com/api/v9/invites/{invite_code}')
        if response.status_code == 200:
            return response.json()['guild']['id']
        else:
            return None

    guild_id = get_guild_id(invite_url)
    if not guild_id:
        log.fail(f"Failed to change name --> {token[:50]}...")
        return

    nickname = config_data.get('nickname')

    headers = {
        "authorization": token,
        "accept": "*/*",
        'accept-encoding': 'gzip, deflate, br',
        "accept-language": "en-GB",
        "content-length": "90",
        "content-type": "application/json",
        "origin": "https://discord.com",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": str(ua),
        "x-debug-options": "bugReporterEnabled",
        "x-super-properties": xtrack(ua)
    }

    response = session.patch(f"https://discord.com/api/v9/guilds/{guild_id}/members/@me/nick", headers=headers,
                             json={"nick": nickname})

    if response.status_code == 200:
        log.success(f'Changed Name --> {token[:50]} --> {nickname}', None)
    else:
        log.fail(f"Failed to change name --> {token[:50]}... --> {response.text}")

def main():
    os.system('cls')

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(join, token) for token in tokens]
        concurrent.futures.wait(futures, return_when=concurrent.futures.ALL_COMPLETED)

if __name__ == "__main__":
    main()
