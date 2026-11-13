import os
import re
import json
import urllib.request
import urllib.error
from flask import Flask, render_template_string, request, Response

app = Flask(__name__)

API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not API_KEY:
    print("WARNING: OPENROUTER_API_KEY environment variable is not set!")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "google/gemini-2.5-flash" 

SYSTEM_INSTRUCTION = (
    "You are an expert mycologist specializing EXCLUSIVELY in Button Mushroom (Agaricus bisporus) cultivation. "
    "Provide concise, practical, and highly direct advice tailored strictly to button mushrooms. "
    "Focus on compost preparation (Phase I & II), casing layer management (peat moss/lime), "
    "temperature drops for pinning (16-18°C), moisture control, and common diseases like Wet Bubble (Mycogone) "
    "and Bacterial Blotch. "
    "CRITICAL FORMATTING RULE: Output strictly in clean, plain text paragraphs and simple lists. "
    "NEVER use markdown formatting, asterisks (*), hash characters (#), backticks, or bold/italic markers."
)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mush AI - Button Mushroom Assistant</title>
    <!-- Import Plus Jakarta Sans Font -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-main: #f7f4ee;       /* Warm cream agricultural background */
            --bg-surface: #ffffff;    /* Clean white container/header */
            --bg-card: #f0ece1;       /* Subtle card/chip background */
            --accent: #f2542d;        /* SmartMushroom signature burnt-orange CTA */
            --accent-hover: #d94520;
            --text-main: #112217;     /* Deep forest green primary text */
            --text-muted: #556358;    /* Muted secondary text */
            --border: #e2dccb;        /* Warm organic border */
            --user-bubble: #112217;   /* Deep forest green for user messages */
            --bot-bubble: #ffffff;    /* White bot response container */
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
        
        body {
            background-color: var(--bg-main);
            color: var(--text-main);
            display: flex;
            flex-direction: column;
            height: 100vh;
            max-width: 900px;
            margin: 0 auto;
            border-left: 1px solid var(--border);
            border-right: 1px solid var(--border);
        }

        header {
            background-color: var(--bg-surface);
            padding: 16px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border);
            box-shadow: 0 2px 4px rgba(17, 34, 23, 0.02);
            flex-shrink: 0;
        }

        .brand { display: flex; align-items: center; gap: 14px; }
        .brand-icon { 
            font-size: 24px; 
            background: linear-gradient(135deg, #112217, #2d5a3f); 
            padding: 10px; 
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(17, 34, 23, 0.15);
        }
        .brand-text h1 { font-size: 1.2rem; font-weight: 700; color: var(--text-main); letter-spacing: -0.01em; }
        .brand-text p { font-size: 0.8rem; color: var(--text-muted); margin-top: 2px; font-weight: 500; }

        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 18px;
            scroll-behavior: smooth;
        }

        .message {
            max-width: 82%;
            padding: 14px 18px;
            border-radius: 14px;
            line-height: 1.6;
            font-size: 0.95rem;
            white-space: pre-wrap;
            word-wrap: break-word;
            box-shadow: 0 2px 6px rgba(17, 34, 23, 0.04);
        }

        .user-message {
            align-self: flex-end;
            background-color: var(--user-bubble);
            color: #ffffff;
            border-bottom-right-radius: 4px;
        }

        .bot-message {
            align-self: flex-start;
            background-color: var(--bot-bubble);
            color: var(--text-main);
            border: 1px solid var(--border);
            border-bottom-left-radius: 4px;
        }

        .presets {
            display: flex;
            gap: 10px;
            padding: 12px 24px;
            overflow-x: auto;
            background-color: var(--bg-surface);
            border-top: 1px solid var(--border);
            flex-shrink: 0;
        }

        .presets::-webkit-scrollbar { height: 4px; }
        .presets::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

        .chip {
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.82rem;
            font-weight: 500;
            white-space: nowrap;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .chip:hover {
            border-color: var(--accent);
            color: var(--accent);
            background-color: rgba(242, 84, 45, 0.05);
        }

        .input-area {
            padding: 16px 24px;
            background-color: var(--bg-surface);
            border-top: 1px solid var(--border);
            display: flex;
            gap: 12px;
            flex-shrink: 0;
        }

        input[type="text"] {
            flex: 1;
            background-color: var(--bg-main);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 12px 20px;
            color: var(--text-main);
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.2s;
        }

        input[type="text"]:focus { border-color: var(--accent); }

        button {
            background-color: var(--accent);
            color: #ffffff;
            border: none;
            border-radius: 50%;
            width: 48px;
            height: 48px;
            font-weight: bold;
            font-size: 1.1rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background-color 0.2s, transform 0.1s;
            box-shadow: 0 4px 10px rgba(242, 84, 45, 0.25);
            flex-shrink: 0;
        }

        button:hover { background-color: var(--accent-hover); transform: scale(1.05); }

        @media (max-width: 768px) {
            body { border: none; height: 100vh; }
            .message { max-width: 90%; }
        }
    </style>
</head>
<body>

    <header>
        <div class="brand">
            <div class="brand-icon">🍄</div>
            <div class="brand-text">
                <h1>Mush AI</h1>
                <p>Your button mushroom expert online</p>
            </div>
        </div>
    </header>

    <div class="chat-container" id="chat">
        <div class="message bot-message">
Hello Farmer! 🍄 Welcome to your professional Button Mushroom (Agaricus bisporus) cultivation hub. Ask me about Phase I/II composting, casing layer preparation, temperature shock management, or disease control.
        </div>
    </div>

    <div class="presets">
        <div class="chip" onclick="sendPreset('Guide me through Phase I and Phase II composting for button mushrooms.')"> Composting Guide</div>
        <div class="chip" onclick="sendPreset('How do I prepare and apply the peat moss casing layer?')"> Casing Setup</div>
        <div class="chip" onclick="sendPreset('What is the precise temperature shock procedure for pinning?')"> Pinning Shock</div>
        <div class="chip" onclick="sendPreset('How do I prevent and treat Wet Bubble disease (Mycogone)?')"> Disease Control</div>
    </div>

    <div class="input-area">
        <input type="text" id="userInput" placeholder="Ask about button mushroom cultivation..." onkeypress="if(event.key === 'Enter') sendMessage()">
        <button onclick="sendMessage()">➔</button>
    </div>

    <script>
        let conversationHistory = [];

        function appendMessage(role, text) {
            const chat = document.getElementById('chat');
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${role}-message`;
            msgDiv.innerText = text;
            chat.appendChild(msgDiv);
            chat.scrollTop = chat.scrollHeight;
            return msgDiv;
        }

        function sendPreset(text) {
            document.getElementById('userInput').value = text;
            sendMessage();
        }

        async function sendMessage() {
            const inputField = document.getElementById('userInput');
            const text = inputField.value.trim();
            if (!text) return;

            inputField.value = '';
            appendMessage('user', text);

            conversationHistory.push({ role: "user", content: text });
            if (conversationHistory.length > 6) {
                conversationHistory = conversationHistory.slice(-6);
            }

            const botMsgDiv = appendMessage('bot', '⚡ Analyzing...');

            try {
                const response = await fetch('/chat_stream', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ history: conversationHistory })
                });

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                botMsgDiv.innerText = '';
                let fullText = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    const chunk = decoder.decode(value, { stream: true });
                    botMsgDiv.innerText += chunk;
                    fullText += chunk;
                    const chat = document.getElementById('chat');
                    chat.scrollTop = chat.scrollHeight;
                }

                if (fullText) {
                    conversationHistory.push({ role: "assistant", content: fullText });
                }
            } catch (err) {
                botMsgDiv.innerText = "Error connecting to server. Please try again.";
            }
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/chat_stream", methods=["POST"])
def chat_stream():
    data = request.json or {}
    history = data.get("history", [])

    if not API_KEY:
        def err_gen():
            yield "Error: OPENROUTER_API_KEY environment variable is not set."
        return Response(err_gen(), mimetype="text/plain")

    messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}] + history

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": True,
        "temperature": 0.3,
        "max_tokens": 2048
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OPENROUTER_URL, 
        data=req_data, 
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "Button Mushroom Agronomist"
        }, 
        method="POST"
    )

    def generate():
        try:
            with urllib.request.urlopen(req) as response:
                for line in response:
                    line_str = line.decode("utf-8").strip()
                    if line_str.startswith("data: "):
                        data_content = line_str[6:].strip()
                        if data_content == "[DONE]":
                            break
                        try:
                            chunk_json = json.loads(data_content)
                            delta = chunk_json.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content")
                            if content:
                                clean_content = re.sub(r'[*#_`]', '', content)
                                yield clean_content
                        except json.JSONDecodeError:
                            continue
        except urllib.error.HTTPError as e:
            yield f"\n[API Error {e.code}: {e.read().decode('utf-8')}]"
        except Exception as e:
            yield f"\n[Error: {str(e)}]"

    return Response(generate(), mimetype="text/plain")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
