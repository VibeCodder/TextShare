import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import http.server
import socketserver
import urllib.request
import socket
import time
import platform
import subprocess
from datetime import datetime

PORT = 8000

# --- COLORS ---
COLORS = {
    "bg": "#1e1e1e",
    "panel": "#252526",
    "text_bg": "#1e1e1e",
    "text_fg": "#e0e0e0",
    "accent": "#007acc",
    "accent_hover": "#1188dd",
    "btn_bg": "#3c3c3c",
    "btn_fg": "#ffffff",
    "log_bg": "#000000",
    "log_fg": "#4ec9b0"
}

# --- NETWORK HELPER FUNCTIONS ---
def get_all_local_ips():
    """Gathers all potential local IP addresses (especially useful for VMs)"""
    ips = []
    
    # Method 1: Active socket (often catches the main outgoing interface)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.append(s.getsockname()[0])
        s.close()
    except Exception:
        pass

    # Method 2: Precise system command for Linux (perfect for VMs)
    if platform.system() == "Linux":
        try:
            output = subprocess.check_output(["hostname", "-I"]).decode("utf-8")
            for ip in output.split():
                if ip not in ips and not ip.startswith("127."):
                    ips.append(ip)
        except Exception:
            pass

    # Method 3: From network hostname (Fallback for Windows/Mac)
    try:
        hostname = socket.gethostname()
        _, _, host_ips = socket.gethostbyname_ex(hostname)
        for ip in host_ips:
            if ip not in ips and not ip.startswith("127."):
                ips.append(ip)
    except Exception:
        pass

    # If everything fails
    if not ips:
        ips = ["127.0.0.1"]
        
    return [f"http://{ip}:{PORT}" for ip in ips]

# --- MAIN APP CLASS ---
class ModernClipboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dynamic Network Clipboard")
        self.root.geometry("950x600")
        self.root.configure(bg=COLORS["bg"])

        # Style configuration for ttk.Combobox to match the dark theme
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground=COLORS["text_bg"], 
                        background=COLORS["panel"], foreground=COLORS["text_fg"], 
                        bordercolor=COLORS["panel"], arrowcolor=COLORS["text_fg"])

        # 1. Address and IP Bar
        top_frame = tk.Frame(root, bg=COLORS["panel"], pady=10, padx=10)
        top_frame.pack(fill=tk.X)
        
        tk.Label(top_frame, text="Target Address:", bg=COLORS["panel"], fg=COLORS["text_fg"]).pack(side=tk.LEFT)
        
        # Fetch address list and create dropdown
        addresses = get_all_local_ips()
        self.ip_entry = ttk.Combobox(top_frame, values=addresses, width=35, font=("Consolas", 10))
        self.ip_entry.set(addresses[0]) # Set default
        self.ip_entry.pack(side=tk.LEFT, padx=10)
        
        # Bind Enter key - update data when user types a new address and presses Enter
        self.ip_entry.bind("<Return>", self.fetch_data_from_address)

        tk.Label(top_frame, text="(Check dropdown if you are on a VM)", bg=COLORS["panel"], fg="gray").pack(side=tk.LEFT)

        # 2. Toolbar
        btn_frame = tk.Frame(root, bg=COLORS["bg"], pady=5, padx=10)
        btn_frame.pack(fill=tk.X)

        buttons = [
            ("📋 Copy", self.copy_text),
            ("📝 Paste", self.paste_text),
            ("✂ Cut", self.cut_text),
            ("🗑 Clear", self.clear_text),
            ("💾 Save", self.save_to_file),
            ("🔄 Fetch from network", self.fetch_data_from_address),
            ("🚀 Send to network", self.send_data_to_address)
        ]
        
        for text, cmd in buttons:
            btn = tk.Button(btn_frame, text=text, command=cmd, bg=COLORS["btn_bg"], fg=COLORS["btn_fg"], 
                            relief=tk.FLAT, padx=10, cursor="hand2")
            btn.pack(side=tk.LEFT, padx=2)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=COLORS["accent"]))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=COLORS["btn_bg"]))

        # 3. Text area with shortcut handling
        self.text_area = tk.Text(root, bg=COLORS["text_bg"], fg=COLORS["text_fg"], 
                                 insertbackground="white", relief=tk.FLAT, font=("Consolas", 11))
        self.text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)
        
        # SHORTCUT BINDINGS
        self.text_area.bind("<Control-a>", self.select_all)
        self.text_area.bind("<Control-c>", self.copy_text)
        self.text_area.bind("<Control-v>", self.paste_text)
        self.text_area.bind("<Control-x>", self.cut_text)

        # 4. Logs
        self.log_area = tk.Text(root, height=6, bg=COLORS["log_bg"], fg=COLORS["log_fg"], 
                                font=("Consolas", 9), relief=tk.FLAT, state=tk.DISABLED)
        self.log_area.pack(fill=tk.X, padx=10, pady=10)

        # Start server
        threading.Thread(target=self.start_server, daemon=True).start()
        self.log(f"App ready. Local server listening on {PORT}")
        self.log(f"Detected local IPs: {', '.join([a.replace(f'http://', '').replace(f':{PORT}', '') for a in addresses])}")

    # --- METHODS ---
    def log(self, msg):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def select_all(self, event):
        self.text_area.tag_add(tk.SEL, "1.0", tk.END)
        return "break"

    def copy_text(self, event=None):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.text_area.get(tk.SEL_FIRST, tk.SEL_LAST) if self.text_area.tag_ranges(tk.SEL) else self.text_area.get("1.0", tk.END))
        self.log("Copied to local clipboard.")

    def paste_text(self, event=None):
        try:
            text = self.root.clipboard_get()
            self.text_area.insert(tk.INSERT, text)
            self.log("Pasted text from clipboard.")
        except: pass

    def cut_text(self, event=None):
        self.copy_text()
        self.text_area.delete(tk.SEL_FIRST, tk.SEL_LAST)
        self.log("Cut text.")

    def clear_text(self):
        self.text_area.delete("1.0", tk.END)
        self.log("Cleared the form.")

    def save_to_file(self):
        f = filedialog.asksaveasfilename(defaultextension=".txt")
        if f:
            with open(f, "w", encoding="utf-8") as file:
                file.write(self.text_area.get("1.0", tk.END))
            self.log(f"Saved to: {f}")

    def fetch_data_from_address(self, event=None):
        url = self.ip_entry.get().strip()
        def fetch():
            try:
                self.log(f"Fetching data from {url}...")
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=3) as response:
                    data = response.read().decode('utf-8')
                    self.root.after(0, self._update_text_area, data)
            except Exception as e:
                self.root.after(0, self.log, f"Communication error: {e}")
        threading.Thread(target=fetch, daemon=True).start()

    def send_data_to_address(self):
        url = self.ip_entry.get().strip()
        data_to_send = self.text_area.get("1.0", tk.END).rstrip('\n').encode('utf-8')
        def send():
            try:
                self.log(f"Sending data to {url}...")
                req = urllib.request.Request(url, data=data_to_send, method="POST")
                req.add_header('Content-Length', len(data_to_send))
                with urllib.request.urlopen(req, timeout=3) as response:
                    if response.status == 200:
                        self.root.after(0, self.log, "Data sent successfully.")
                    else:
                        self.root.after(0, self.log, f"Sent, but server returned code: {response.status}")
            except Exception as e:
                self.root.after(0, self.log, f"Communication error: {e}")
        threading.Thread(target=send, daemon=True).start()

    def _update_text_area(self, data):
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.INSERT, data)
        self.log("Updated data from network.")

    def start_server(self):
        app_ref = self
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass
            
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/plain; charset=utf-8')
                self.end_headers()
                current_text = app_ref.text_area.get("1.0", tk.END).rstrip('\n')
                self.wfile.write(current_text.encode('utf-8'))
                
            def do_POST(self):
                length = int(self.headers.get('Content-Length', 0))
                if length > 0:
                    data = self.rfile.read(length).decode('utf-8')
                    app_ref.root.after(0, app_ref._update_text_area, data)
                    app_ref.root.after(0, app_ref.log, f"Received data from {self.client_address[0]}")
                self.send_response(200)
                self.end_headers()
        
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
            httpd.serve_forever()

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernClipboardApp(root)
    root.mainloop()