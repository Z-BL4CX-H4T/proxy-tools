import requests
import threading
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from colorama import init, Fore

init(autoreset=True)

DEFAULT_PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt"
]

def fetch_proxies():
    proxies = set()
    print(Fore.YELLOW + "\n🔄 Mengambil proxy dari semua sumber...")
    for url in DEFAULT_PROXY_SOURCES:
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                lines = res.text.strip().splitlines()
                proxies.update(lines)
                print(Fore.GREEN + f"✅ {url} ({len(lines)} proxy)")
        except Exception as e:
            print(Fore.RED + f"❌ {url} -> Gagal: {e}")
    with open("proxies_raw.txt", "w") as f:
        f.write("\n".join(proxies))
    print(Fore.GREEN + f"\n✅ Total proxy disimpan ke proxies_raw.txt: {len(proxies)}\n")

def check_proxy(proxy, proxy_type, timeout=5):
    proxy_dict = {
        "http": f"http://{proxy}",
        "https": f"https://{proxy}",
        "socks4": f"socks4://{proxy}",
        "socks5": f"socks5://{proxy}"
    }
    try:
        start = time.time()
        response = requests.get("http://httpbin.org/ip", proxies={
            "http": proxy_dict[proxy_type], "https": proxy_dict[proxy_type]
        }, timeout=timeout)
        latency = round(time.time() - start, 2)
        if response.status_code == 200:
            geo_info = get_geo_info(proxy.split(':')[0])
            result = f"{proxy},{proxy_type},{latency}s,{geo_info}"
            print(Fore.GREEN + f"[ALIVE] {result}", flush=True)
            with open("proxies_alive.csv", "a") as f:
                f.write(result + "\n")
    except:
        print(Fore.RED + f"[DEAD]  {proxy:<21}", flush=True)

def get_geo_info(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}?fields=country,city,query", timeout=3)
        if res.status_code == 200:
            data = res.json()
            return f"{data['query']} ({data['city']}, {data['country']})"
    except:
        return "Unknown"

def run_checker(file_name, proxy_type):
    if not os.path.exists(file_name):
        print(Fore.RED + "❌ File tidak ditemukan.")
        return

    with open("proxies_alive.csv", "w") as f:
        f.write("IP:Port,Type,Latency,Location\n")

    with open(file_name, "r") as f:
        proxies = [line.strip() for line in f if line.strip()]

    print(f"\n🔍 Memeriksa {len(proxies)} proxy...\n")
    with ThreadPoolExecutor(max_workers=50) as executor:
        for proxy in proxies:
            executor.submit(check_proxy, proxy, proxy_type)

    print(Fore.GREEN + "\n✅ Pemeriksaan selesai. Hasil disimpan di proxies_alive.csv\n")

def menu():
    ascii_art = f"""{Fore.GREEN}

██████╗ ██████╗  ██████╗ ██╗  ██╗██╗   ██╗  ████████╗ ██████╗  ██████╗ ██╗     ███████╗
██╔══██╗██╔══██╗██╔═══██╗╚██╗██╔╝╚██╗ ██╔╝  ╚══██╔══╝██╔═══██╗██╔═══██╗██║     ██╔════╝
██████╔╝██████╔╝██║   ██║ ╚███╔╝  ╚████╔╝█████╗██║   ██║   ██║██║   ██║██║     ███████╗
██╔═══╝ ██╔══██╗██║   ██║ ██╔██╗   ╚██╔╝ ╚════╝██║   ██║   ██║██║   ██║██║     ╚════██║
██║     ██║  ██║╚██████╔╝██╔╝ ██╗   ██║        ██║   ╚██████╔╝╚██████╔╝███████╗███████║
╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝        ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝╚══════╝                            
				by Z-SH4DOWSPEECH
"""
    print(ascii_art)

    while True:
        print(Fore.GREEN + "\n==== TOOLS GET PROXY + CHECKER ====")
        print(Fore.RED + "1." + Fore.WHITE + " Get Proxy dari URL")
        print(Fore.RED + "2." + Fore.WHITE + " Proxy Checker (.txt input)")
        print(Fore.RED + "3." + Fore.WHITE + " Lihat proxy hidup")
        print(Fore.RED + "4." + Fore.WHITE + " Keluar\n")

        pilihan = input(Fore.CYAN + "Pilih menu [1-4]: ").strip()

        if pilihan == "1":
            fetch_proxies()
        elif pilihan == "2":
            file_name = input("Masukkan nama file proxy (contoh: proxies_raw.txt): ").strip()
            print("\nPilih jenis proxy:")
            print("1. HTTP\n2. SOCKS4\n3. SOCKS5")
            tipe = input("Pilih [1/2/3]: ").strip()
            proxy_type = {"1": "http", "2": "socks4", "3": "socks5"}.get(tipe)
            if proxy_type:
                run_checker(file_name, proxy_type)
            else:
                print(Fore.RED + "❌ Jenis proxy tidak valid.")
        elif pilihan == "3":
            if os.path.exists("proxies_alive.csv"):
                print(Fore.GREEN + "\n📄 Daftar proxy hidup:")
                with open("proxies_alive.csv", "r") as f:
                    for line in f.readlines()[1:]:
                        print(line.strip())
            else:
                print(Fore.RED + "❌ File proxies_alive.csv belum ada.")
        elif pilihan == "4":
            print(Fore.YELLOW + "👋 Keluar...")
            break
        else:
            print(Fore.RED + "❌ Pilihan tidak valid.")

if __name__ == "__main__":
    menu()
