import base64
import json
import os
import random
import threading
import concurrent.futures
from CSolver.Hcap.hcap import Solver
import time
import requests
from colorama import Fore, Style
from tls_client import Session
import ua_generator

# Constants for colors
cyan = Fore.CYAN
gray = Fore.LIGHTBLACK_EX + Fore.WHITE
reset = Fore.RESET
colorful = Fore.LIGHTMAGENTA_EX + Fore.LIGHTCYAN_EX
pink = Fore.LIGHTGREEN_EX + Fore.LIGHTMAGENTA_EX
green = Fore.GREEN

# Global counters
joined = 0
solved = 0
errors = 0

# Load tokens from file
with open('tokens.txt', 'r') as file:
    tokens = [line.strip().split(":")[-1] for line in file.readlines()]

# UI function
def ui():
    print(cyan + """
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

# Solve function
def solve(url, key, rqdata, proxy):
    global solved
    with open("config.json") as conf_file:
        config = json.load(conf_file)
        started_solving = time.time()
        solution = Solver.solve('hCaptchaEnterprise', config['CSolver-key'], key, url, proxy, rqdata)    
        print(f"{colorful}[ Solved ] {gray}|{pink} {cyan}[ {solution[-32:]} ] {reset}| [ {round(time.time()-started_solving)}s ]")
        solved += 1
        return solution

# Generate xtrack
def xtrack(ua):
    return base64.b64encode(json.dumps({
        "os": str(ua.ch.platform),
        "browser": str(ua.browser),
        "device": str(ua.platform),
        "system_locale": "en-US",
        "browser_user_agent": str(ua),
        "browser_version": "110.0.5481.192",
        "os_version": ua.ch.platform_version,
        "release_channel": "stable",
        "client_build_number": 5645383,
        "client_event_source": None
    }).encode()).decode()

# Join function
def join(token):
    global joined, solved, errors
    ua = ua_generator.generate(platform='ios', browser='safari')
    with open("config.json") as config_file:
        config_data = json.load(config_file)
        invite_code = config_data.get('invite')
    
    proxy_list = open("proxies.txt", "r").readlines()
    proxy = random.choice(proxy_list).strip() if proxy_list else None

    session = Session(client_identifier="safari_ios_17_1", random_tls_extension_order=True)

    if proxy and proxy.count(":") == 3:
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
        print(f"{pink}[ Fingerprint ] {reset}| {colorful}[ {fingerprint} ]")
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
        response = session.post(f"https://discord.com/api/v9/invites/{invite_code}", headers=headers)
        if response.status_code == 400:
            print(f"[ {colorful}Solving Captcha ] {gray}| [ {green}{token[:50]}**** ] ")
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
            new_response = session.post(f"https://discord.com/api/v9/invites/{invite_code}", headers=headers, json=payload)
            if new_response.status_code == 200:
                print(f"[ {colorful}Joined ] {gray}|{cyan}[ {token[:50]}**** ]")
                joined += 1
                break
            else:
                print(f"[ {colorful}Failed to Join After Captcha ] {gray}| {cyan}[ {token[:50]}**** ] {reset}[ {new_response.text} ]")
                errors += 1
        elif response.status_code == 200:
            print(f"[ {colorful}Joined Successfully ] {gray}|{cyan}[ {token[:50]}**** ]")
            joined += 1
            break
        else:
            print(f"[ {colorful}Failed To Join ] {gray}| {cyan}[ {token[:50]}**** ] {reset}[ {response.text} ]")
            errors += 1
            break

# Main function
def main():
    os.system('cls')

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(join, token) for token in tokens]
        concurrent.futures.wait(futures, return_when=concurrent.futures.ALL_COMPLETED)

    input("Press ENTER to quit")

if __name__ == "__main__":
    main()
