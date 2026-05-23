import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import http.server
import socketserver
import urllib.request
import socket
import time
from datetime import datetime

PORT = 8000

# --- KOLORYSTYKA ---
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

# --- FUNKCJE SIECIOWE (Pomocnicze) ---
def get_local_ip():
    try:
        # Metoda domyślna (wymaga działającego interfejsu sieciowego skierowanego na zewnątrz)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            # Fallback (bardzo użyteczny na Linuxie bez internetu)
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

# --- KLASA APLIKACJI ---
class ModernClipboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dynamiczny Schowek Sieciowy")
        self.root.geometry("950x600") # Lekko poszerzyłem okno na nowy przycisk
        self.root.configure(bg=COLORS["bg"])

        # 1. Pasek adresowy i IP
        top_frame = tk.Frame(root, bg=COLORS["panel"], pady=10, padx=10)
        top_frame.pack(fill=tk.X)
        
        tk.Label(top_frame, text="Adres powiązany:", bg=COLORS["panel"], fg=COLORS["text_fg"]).pack(side=tk.LEFT)
        self.ip_entry = tk.Entry(top_frame, width=35, bg=COLORS["text_bg"], fg=COLORS["text_fg"], 
                                 insertbackground="white", relief=tk.FLAT)
        self.ip_entry.insert(0, f"http://{get_local_ip()}:{PORT}")
        self.ip_entry.pack(side=tk.LEFT, padx=10)
        
        # Bindowanie entera - zaktualizuj dane, gdy użytkownik wpisze nowy adres i wciśnie Enter
        self.ip_entry.bind("<Return>", self.fetch_data_from_address)

        tk.Label(top_frame, text="(Wciśnij Enter, aby pobrać)", bg=COLORS["panel"], fg="gray").pack(side=tk.LEFT)

        # 2. Pasek narzędzi
        btn_frame = tk.Frame(root, bg=COLORS["bg"], pady=5, padx=10)
        btn_frame.pack(fill=tk.X)

        buttons = [
            ("📋 Kopiuj", self.copy_text),
            ("📝 Wklej", self.paste_text),
            ("✂ Wytnij", self.cut_text),
            ("🗑 Wyczyść", self.clear_text),
            ("💾 Zapisz", self.save_to_file),
            ("🔄 Pobierz z sieci", self.fetch_data_from_address),
            ("🚀 Wyślij do sieci", self.send_data_to_address) # Nowy przycisk wysyłania
        ]
        
        for text, cmd in buttons:
            btn = tk.Button(btn_frame, text=text, command=cmd, bg=COLORS["btn_bg"], fg=COLORS["btn_fg"], 
                            relief=tk.FLAT, padx=10, cursor="hand2")
            btn.pack(side=tk.LEFT, padx=2)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=COLORS["accent"]))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=COLORS["btn_bg"]))

        # 3. Pole tekstowe z obsługą skrótów
        self.text_area = tk.Text(root, bg=COLORS["text_bg"], fg=COLORS["text_fg"], 
                                 insertbackground="white", relief=tk.FLAT, font=("Consolas", 11))
        self.text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)
        
        # BINDOWANIE SKRÓTÓW
        self.text_area.bind("<Control-a>", self.select_all)
        self.text_area.bind("<Control-c>", self.copy_text)
        self.text_area.bind("<Control-v>", self.paste_text)
        self.text_area.bind("<Control-x>", self.cut_text)

        # 4. Logi
        self.log_area = tk.Text(root, height=5, bg=COLORS["log_bg"], fg=COLORS["log_fg"], 
                                font=("Consolas", 9), relief=tk.FLAT, state=tk.DISABLED)
        self.log_area.pack(fill=tk.X, padx=10, pady=10)

        # Uruchom serwer
        threading.Thread(target=self.start_server, daemon=True).start()
        self.log(f"Aplikacja gotowa. Lokalny serwer nasłuchuje na {PORT}")

    # --- METODY ---
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
        self.log("Skopiowano do schowka lokalnego.")

    def paste_text(self, event=None):
        try:
            text = self.root.clipboard_get()
            self.text_area.insert(tk.INSERT, text)
            self.log("Wklejono tekst ze schowka.")
        except: pass

    def cut_text(self, event=None):
        self.copy_text()
        self.text_area.delete(tk.SEL_FIRST, tk.SEL_LAST)
        self.log("Wycięto tekst.")

    def clear_text(self):
        self.text_area.delete("1.0", tk.END)
        self.log("Wyczyszczono formularz.")

    def save_to_file(self):
        f = filedialog.asksaveasfilename(defaultextension=".txt")
        if f:
            with open(f, "w", encoding="utf-8") as file:
                file.write(self.text_area.get("1.0", tk.END))
            self.log(f"Zapisano do: {f}")

    def fetch_data_from_address(self, event=None):
        """Pobiera dane z adresu wpisanego w pole ip_entry i aktualizuje formularz"""
        url = self.ip_entry.get().strip()
        
        def fetch():
            try:
                self.log(f"Pobieranie danych z {url}...")
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=3) as response:
                    data = response.read().decode('utf-8')
                    # Przekazanie danych do głównego wątku UI
                    self.root.after(0, self._update_text_area, data)
            except Exception as e:
                self.root.after(0, self.log, f"Błąd komunikacji: {e}")
                
        # Uruchamiamy w osobnym wątku, aby nie zamrozić UI podczas oczekiwania
        threading.Thread(target=fetch, daemon=True).start()

    def send_data_to_address(self):
        """Wysyła dane z formularza pod adres wpisany w pole ip_entry"""
        url = self.ip_entry.get().strip()
        # Pobieramy tekst z pola i konwertujemy do bajtów, co jest wymagane przez urllib dla żądań POST
        data_to_send = self.text_area.get("1.0", tk.END).rstrip('\n').encode('utf-8')
        
        def send():
            try:
                self.log(f"Wysyłanie danych do {url}...")
                req = urllib.request.Request(url, data=data_to_send, method="POST")
                req.add_header('Content-Length', len(data_to_send))
                with urllib.request.urlopen(req, timeout=3) as response:
                    if response.status == 200:
                        self.root.after(0, self.log, "Pomyślnie wysłano dane.")
                    else:
                        self.root.after(0, self.log, f"Wysłano, ale serwer zwrócił kod: {response.status}")
            except Exception as e:
                self.root.after(0, self.log, f"Błąd komunikacji: {e}")
                
        # Uruchamiamy w osobnym wątku, aby nie zamrozić UI
        threading.Thread(target=send, daemon=True).start()

    def _update_text_area(self, data):
        """Funkcja pomocnicza wywoływana w wątku głównym dla bezpieczeństwa UI tkinter"""
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.INSERT, data)
        self.log("Zaktualizowano dane z sieci.")

    def start_server(self):
        # Przekazujemy referencję na aplikację, aby serwer mógł z niej korzystać
        app_ref = self
        
        class Handler(http.server.BaseHTTPRequestHandler):
            
            # Wyciszamy logi w konsoli, skoro mamy własny panel logów w UI
            def log_message(self, format, *args):
                pass
            
            # OBSŁUGA ZAPYTAŃ O POBRANIE DANYCH
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/plain; charset=utf-8')
                self.end_headers()
                
                # Pobranie tekstu bezpośrenio z widgetu
                current_text = app_ref.text_area.get("1.0", tk.END).rstrip('\n')
                self.wfile.write(current_text.encode('utf-8'))
                
            # OBSŁUGA PRZYCHODZĄCYCH DANYCH (np. z Curl, skryptów, innej instancji apki)
            def do_POST(self):
                length = int(self.headers.get('Content-Length', 0))
                if length > 0:
                    data = self.rfile.read(length).decode('utf-8')
                    # Przekazanie przychodzącego tekstu do UI
                    app_ref.root.after(0, app_ref._update_text_area, data)
                    app_ref.root.after(0, app_ref.log, f"Otrzymano dane od {self.client_address[0]}")
                    
                self.send_response(200)
                self.end_headers()
        
        # Pozwala na szybki restart serwera na tym samym porcie po zamknięciu
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            httpd.serve_forever()

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernClipboardApp(root)
    root.mainloop()