import http.server
import socketserver

PORT = 8000
shared_text = "Wpisz coś tutaj..."

HTML_PAGE = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lokalny Schowek</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            background-color: #1e1e1e; /* Ciemne tło strony */
            color: #e0e0e0; /* Jasny tekst */
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            padding: 2rem; 
            margin: 0; 
        }
        h1 { 
            margin-bottom: 1rem; 
        }
        textarea { 
            width: 100%; 
            max-width: 800px; 
            height: 300px; 
            padding: 15px; 
            font-size: 16px; 
            background-color: #252526; /* Ciemniejsze tło pola tekstowego */
            color: #e0e0e0; /* Jasny tekst w polu */
            border: 2px solid #3c3c3c; /* Ciemna ramka */
            border-radius: 8px; 
            resize: vertical; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.3); /* Mocniejszy cień dla głębi */
        }
        textarea:focus { 
            border-color: #007acc; /* Niebieski akcent przy pisaniu */
            outline: none; 
        }
        .controls { 
            display: flex; 
            gap: 10px; 
            margin-top: 15px; 
            width: 100%; 
            max-width: 800px; 
            align-items: center; 
            justify-content: space-between; 
        }
        button { 
            padding: 10px 20px; 
            font-size: 16px; 
            background-color: #007acc; 
            color: white; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            transition: background-color 0.2s; 
        }
        button:hover { 
            background-color: #1188dd; /* Jaśniejszy niebieski po najechaniu */
        }
        #status { 
            font-size: 14px; 
            color: #aaaaaa; /* Szary tekst statusu */
        }
    </style>
</head>
<body>
    <h1>Lokalny Schowek</h1>
    <textarea id="box" placeholder="Zacznij pisać..."></textarea>
    <div class="controls">
        <button onclick="sendText()">Wyślij tekst (Zapisz)</button>
        <span id="status"></span>
    </div>

    <script>
        const box = document.getElementById('box');
        const status = document.getElementById('status');

        // Funkcja pobierająca tekst z serwera
        function loadText() {
            fetch('/text')
                .then(response => response.text())
                .then(text => {
                    // Aktualizuj pole tylko, jeśli użytkownik w nim aktualnie nie pisze
                    if (document.activeElement !== box) {
                        box.value = text;
                    }
                })
                .catch(err => console.error("Błąd połączenia", err));
        }

        // Funkcja wysyłająca tekst na serwer
        function sendText() {
            const text = box.value;
            status.innerText = 'Wysyłanie...';
            fetch('/text', {
                method: 'POST',
                body: text
            }).then(() => {
                status.innerText = 'Zapisano: ' + new Date().toLocaleTimeString();
                setTimeout(() => status.innerText = '', 3000);
            }).catch(() => {
                status.innerText = 'Błąd zapisu!';
            });
        }

        // Pobieraj tekst co 2 sekundy (automatyczna synchronizacja)
        setInterval(loadText, 2000);
        
        // Pobierz przy pierwszym załadowaniu strony
        window.onload = loadText;
    </script>
</body>
</html>
"""

class RequestHandler(http.server.BaseHTTPRequestHandler):
    # Wyłącz logowanie każdego zapytania w konsoli (żeby nie śmiecić)
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        global shared_text
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        elif self.path == '/text':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(shared_text.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global shared_text
        if self.path == '/text':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            shared_text = post_data.decode('utf-8')
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

with socketserver.TCPServer(("0.0.0.0", PORT), RequestHandler) as httpd:
    print(f"✅ Serwer działa!")
    print(f"👉 Na tym komputerze otwórz przeglądarkę i wejdź na: http://localhost:{PORT}")
    print(f"👉 Aby połączyć się z drugiego komputera, musisz podać adres IP tego komputera w sieci lokalnej (np. http://192.168.x.x:{PORT})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nZatrzymywanie serwera...")