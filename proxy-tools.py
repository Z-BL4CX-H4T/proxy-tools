import sys
import requests
import socks
import socket
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QFileDialog, QProgressBar
)
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class ProxyLoader(QThread):
    update_signal = pyqtSignal(str)
    finish_signal = pyqtSignal(list)

    def __init__(self, urls):
        super().__init__()
        self.urls = urls

    def run(self):
        proxies = []
        for url in self.urls:
            url = url.strip()
            if not url.startswith("http"):
                continue
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    lines = r.text.strip().splitlines()
                    proxies.extend([l.strip() for l in lines if l.strip()])
                    self.update_signal.emit(f"✔ Sukses load {len(lines)} proxy dari {url}")
                else:
                    self.update_signal.emit(f"✘ Gagal load dari {url}")
            except Exception as e:
                self.update_signal.emit(f"✘ Error load dari {url}: {e}")
            time.sleep(0.05)
        self.finish_signal.emit(proxies)

def parse_proxy(proxy_str):
    proxy_str = proxy_str.strip()
    proxy_type = "http" 

    if proxy_str.startswith("http://"):
        proxy_type = "http"
        proxy_str = proxy_str[7:]
    elif proxy_str.startswith("https://"):
        proxy_type = "https"
        proxy_str = proxy_str[8:]
    elif proxy_str.startswith("socks4://"):
        proxy_type = "socks4"
        proxy_str = proxy_str[9:]
    elif proxy_str.startswith("socks5://"):
        proxy_type = "socks5"
        proxy_str = proxy_str[9:]

    if ":" not in proxy_str:
        return None, None, None
    ip, port = proxy_str.split(":")[0:2]
    try:
        port = int(port)
    except:
        return None, None, None
    return ip, port, proxy_type

class ProxyChecker(QThread):
    update_signal = pyqtSignal(str, bool)
    progress_signal = pyqtSignal(int)
    finish_signal = pyqtSignal(int, int)

    def __init__(self, proxies):
        super().__init__()
        self.proxies = proxies

    def run(self):
        valid_count = 0
        invalid_count = 0
        total = len(self.proxies)
        for idx, proxy in enumerate(self.proxies, 1):
            result = self.check_proxy(proxy)
            if result:
                valid_count += 1
            else:
                invalid_count += 1
            self.update_signal.emit(proxy, result)
            self.progress_signal.emit(int(idx / total * 100))
        self.finish_signal.emit(valid_count, invalid_count)

    def check_proxy(self, proxy):
        ip, port, ptype = parse_proxy(proxy)
        if not ip:
            return False

        try:
            if ptype in ["http", "https"]:
                pro = {"http": f"http://{ip}:{port}", "https": f"http://{ip}:{port}"}
                r = requests.get("http://httpbin.org/ip", proxies=pro, timeout=5)
                if r.status_code == 200:
                    return True
            elif ptype == "socks4":
                s = socks.socksocket()
                s.set_proxy(socks.SOCKS4, ip, port)
                s.settimeout(5)
                s.connect(("httpbin.org", 80))
                s.close()
                return True
            elif ptype == "socks5":
                s = socks.socksocket()
                s.set_proxy(socks.SOCKS5, ip, port)
                s.settimeout(5)
                s.connect(("httpbin.org", 80))
                s.close()
                return True
        except:
            return False
        return False

class ProxyTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PROXY TOOL — GREEN EDITION")
        self.setGeometry(200, 80, 900, 700)
        self.proxies = []

        self.build_ui()
        self.apply_theme()

    def apply_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0))
        palette.setColor(QPalette.Base, QColor(0, 0, 0))
        palette.setColor(QPalette.Text, QColor(0, 255, 0))
        self.setPalette(palette)

    def build_ui(self):
        layout = QVBoxLayout()

        title = QLabel("PROXY CHECKER TOOL")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Consolas", 22, QFont.Bold))
        title.setStyleSheet("color:#00FF00;")
        layout.addWidget(title)

        self.input_area = QTextEdit()
        self.input_area.setPlaceholderText("Paste URL proxy di sini (satu per baris)...")
        self.input_area.setStyleSheet("background:#000; color:#00FF00; border:1px solid #00FF00;")
        layout.addWidget(self.input_area)

        btns = QHBoxLayout()
        self.btn_get_proxy = QPushButton("Get Proxy dari URL")
        self.btn_load_file = QPushButton("Load Proxy dari File")
        self.btn_check = QPushButton("Check Proxy")
        self.btn_save = QPushButton("Save Proxy Valid")
        self.btn_clear = QPushButton("Clear")

        for b in (self.btn_get_proxy, self.btn_load_file, self.btn_check, self.btn_save, self.btn_clear):
            b.setStyleSheet("background:#003300; color:#00FF00; font-weight:bold; padding:6px;")
            btns.addWidget(b)
        layout.addLayout(btns)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setStyleSheet("QProgressBar {border:1px solid #00FF00; text-align:center; color:#00FF00;} QProgressBar::chunk {background:#00FF00;}")
        layout.addWidget(self.progress)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("background:#000; color:#00FF00; border:1px solid #00FF00;")
        layout.addWidget(self.output)

        self.setLayout(layout)

        self.btn_get_proxy.clicked.connect(self.load_proxy_from_url)
        self.btn_load_file.clicked.connect(self.load_proxy_from_file)
        self.btn_check.clicked.connect(self.start_check)
        self.btn_save.clicked.connect(self.save_valid)
        self.btn_clear.clicked.connect(self.clear_all)

    def load_proxy_from_url(self):
        urls = self.input_area.toPlainText().splitlines()
        if not urls:
            self.output.append("⚠ Masukkan URL proxy di input area!")
            return
        self.output.append("⏳ Mulai load proxy dari URL...")
        self.thread_loader = ProxyLoader(urls)
        self.thread_loader.update_signal.connect(lambda msg: self.output.append(msg))
        self.thread_loader.finish_signal.connect(self.finish_load_proxy)
        self.thread_loader.start()

    def finish_load_proxy(self, proxies):
        cleaned = []
        for p in proxies:
            ip, port, _ = parse_proxy(p)
            if ip:
                cleaned.append(p)
        self.proxies = cleaned
        self.output.append(f"✔ Selesai load proxy! Total: {len(cleaned)} proxy.")
        display_count = min(50, len(cleaned))
        self.output.append("▼ 50 Proxy pertama:")
        for p in self.proxies[:display_count]:
            self.output.append(p)
        self.output.append("… (Sisanya tersimpan di internal list)")

    def load_proxy_from_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Load Proxy File", "", "Text Files (*.txt)")
        if file:
            with open(file, "r") as f:
                lines = [l.strip() for l in f if l.strip()]
            cleaned = []
            for p in lines:
                ip, port, _ = parse_proxy(p)
                if ip:
                    cleaned.append(p)
            self.proxies = cleaned
            self.output.append(f"✔ Berhasil load {len(cleaned)} proxy dari file: {file}")
            display_count = min(50, len(cleaned))
            self.output.append("▼ 50 Proxy pertama:")
            for p in self.proxies[:display_count]:
                self.output.append(p)
            self.output.append("… (Sisanya tersimpan di internal list)")

    def start_check(self):
        if not self.proxies:
            self.output.append("⚠ Tidak ada proxy untuk dicek. Gunakan 'Get Proxy dari URL' atau load file terlebih dahulu!")
            return
        self.output.append("⏳ Mulai cek proxy...")
        self.progress.setValue(0)
        self.thread_check = ProxyChecker(self.proxies)
        self.thread_check.update_signal.connect(self.update_output)
        self.thread_check.progress_signal.connect(self.progress.setValue)
        self.thread_check.finish_signal.connect(self.finish_check)
        self.thread_check.start()

    def update_output(self, proxy, valid):
        if valid:
            self.output.append(f"<span style='color:#00FF00;'>{proxy} ✔ VALID</span>")
        else:
            self.output.append(f"<span style='color:red;'>{proxy} ✘ INVALID</span>")

    def finish_check(self, valid_count, invalid_count):
        self.output.append(f"✔ Proxy check selesai! VALID: {valid_count}, INVALID: {invalid_count}")
        self.progress.setValue(100)

    def save_valid(self):
        lines = self.output.toPlainText().splitlines()
        valid = [l.split()[0] for l in lines if "VALID" in l]
        if not valid:
            self.output.append("⚠ Tidak ada proxy valid untuk disimpan!")
            return
        file, _ = QFileDialog.getSaveFileName(self, "Save Valid Proxy", "valid_proxy.txt")
        if file:
            with open(file, "w") as f:
                f.write("\n".join(valid))
            self.output.append(f"✔ {len(valid)} proxy valid berhasil disimpan!")

    def clear_all(self):
        self.input_area.clear()
        self.output.clear()
        self.progress.setValue(0)
        self.output.append("<span style='color:#00FF00;'>✔ Semua area dibersihkan!</span>")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProxyTool()
    window.show()
    sys.exit(app.exec_())
