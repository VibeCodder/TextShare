import http.server
import socketserver

START_PORT = 8000
MAX_PORT = 8010
shared_text = ""

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Local Clipboard</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            background-color: #1e1e1e;
            color: #e0e0e0; 
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
            background-color: #252526; 
            color: #e0e0e0; 
            border: 2px solid #3c3c3c; 
            border-radius: 8px; 
            resize: vertical; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.3); 
        }
        textarea:focus { 
            border-color: #007acc; 
            outline: none; 
        }
        .controls { 
            display: flex; 
            margin-top: 15px; 
            width: 100%; 
            max-width: 800px; 
            align-items: center; 
            justify-content: space-between; 
        }
        .btn-group {
            display: flex;
            gap: 10px;
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
            background-color: #1188dd; 
        }
        button.secondary {
            background-color: #3c3c3c;
        }
        button.secondary:hover {
            background-color: #555555;
        }
        #status { 
            font-size: 14px; 
            color: #aaaaaa; 
            text-align: right;
        }
    </style>
</head>
<body>
    <h1>Local Clipboard</h1>
    <textarea id="box" placeholder="Start typing..."></textarea>
    <div class="controls">
        <div class="btn-group">
            <button onclick="sendText()">Save text</button>
            <button onclick="copyToClipboard()" class="secondary">Copy</button>
            <button onclick="pasteFromClipboard()" class="secondary">Paste</button>
        </div>
        <span id="status"></span>
    </div>

    <script>
        const box = document.getElementById('box');
        const status = document.getElementById('status');

        // Function to fetch text from the server
        function loadText() {
            fetch('/text')
                .then(response => response.text())
                .then(text => {
                    // Update field only if the user is not currently typing in it
                    if (document.activeElement !== box) {
                        box.value = text;
                    }
                })
                .catch(err => console.error("Connection error", err));
        }

        // Function to send text to the server
        function sendText() {
            const text = box.value;
            status.innerText = 'Saving...';
            fetch('/text', {
                method: 'POST',
                body: text
            }).then(() => {
                status.innerText = 'Saved: ' + new Date().toLocaleTimeString();
                setTimeout(() => status.innerText = '', 3000);
            }).catch(() => {
                status.innerText = 'Save error!';
            });
        }

        // Copy to clipboard
        function copyToClipboard() {
            navigator.clipboard.writeText(box.value)
                .then(() => {
                    status.innerText = 'Copied to clipboard!';
                    setTimeout(() => status.innerText = '', 3000);
                })
                .catch(err => {
                    status.innerText = 'Copy error!';
                    console.error('Error:', err);
                });
        }

        // Paste from clipboard (may require permissions and HTTPS)
        function pasteFromClipboard() {
            navigator.clipboard.readText()
                .then(text => {
                    box.value = text;
                    status.innerText = 'Pasted!';
                    sendText(); // Automatically save to server after pasting
                })
                .catch(err => {
                    status.innerText = 'Paste error (missing permissions/HTTPS)!';
                    console.error('Error:', err);
                });
        }

        // Fetch text every 2 seconds (auto-sync)
        setInterval(loadText, 2000);
        
        // Fetch on first page load
        window.onload = loadText;
    </script>
</body>
</html>
"""

class RequestHandler(http.server.BaseHTTPRequestHandler):
    # Disable logging of every request in the console
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

# Klasa serwera z flagą pozwalającą na natychmiastowe ponowne użycie portu
class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

# Pętla szukająca wolnego portu
for port in range(START_PORT, MAX_PORT + 1):
    try:
        with ReusableTCPServer(("0.0.0.0", port), RequestHandler) as httpd:
            print(f"✅ Server is running!")
            print(f"👉 On this computer, open a browser and go to: http://localhost:{port}")
            print(f"👉 To connect from another computer, use this computer's local IP address (e.g., http://localhost:{port})")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nStopping server...")
            break # Zakończ pętlę, jeśli serwer wystartował bez błędów
    except OSError as e:
        if e.errno == 98: # Address already in use
            print(f"⚠️ Port {port} is busy. Trying next port...")
        else:
            raise # Wyrzuć błąd, jeśli to coś innego niż zajęty port
else:
    print(f"❌ Could not find an open port between {START_PORT} and {MAX_PORT}.")