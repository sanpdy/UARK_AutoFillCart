# 🛒 ReciPDF AI Cart Builder – Streamlit App

A sleek, AI-driven app that extracts ingredients from a recipe (PDF or text), matches them to products (mock or real), and builds a Walmart shopping cart.

---

## 🔍 What the app does

- Upload a **PDF or text recipe**
- Extracts and highlights any **Ingredients** sections
- Either:
  - Manually select mock products, or
  - Use **OpenAI** to match items and build a **real cart URL**
- Styled to resemble **Walmart’s UI**, all within Streamlit
- Runs locally in your browser — no backend required

## 🧠 Features Overview

- 📄 **PDF/TXT upload** + free-text box.
- 🧾 Auto-detection of ingredient sections.
- 🤖 Agent mode (calls OpenAI API to search, match, and build cart).
- ⚙️ Manual UI with radio selectors and justifications.
- 🎨 Custom CSS UI matching Walmart.com.
- 🧠 Session-managed cart, summary, preferences, and export link.
- 🔄 Auto-reloads on file save (with Streamlit).
- 💬 Intelligent error handling + traceback display.

---

## 🛠 Prerequisites (one-time setup)

| Tool | Purpose | Install |
|------|---------|---------|
| [**Python 3.8+**](https://www.python.org/downloads/) | Core language | Windows: check "Add Python to PATH" |
| [**Git**](https://git-scm.com/) | Clone code | macOS: `brew install git` |
| [**OpenAI API key**](https://platform.openai.com/account/api-keys) | Access GPT models | Add to `.env` file (see below) |
| [**VS Code** (optional)](https://code.visualstudio.com/) | Code editor | Clean UI with built-in terminal |

> 💡 **No admin rights?** You can install Python and Git for your user only.
---

## 🔐 API Key Setup (for GPT-powered cart builder)

1. Get your OpenAI API key from https://platform.openai.com/account/api-keys
2. Get Walmart Affiliate API Keys following the guide by Stephen Pierson
2. Create a file in the project root called `.env`
3. Add the following lines to it:

```bash
OPENAI_API_KEY=your-api-key-here
WALMART_CONSUMER_ID=...# Add you consumer ID here#...
WALMART_RSA_KEY_PATH=~/.ssh/rsa_key_20250410_v2 # points to the location of your walmart RSA Key
```

> ⚠️ Without this key, the AI-driven cart builder will fallback to mock responses.

---

## 🚀 Run the App

### 1. Clone the repo (if you haven’t)

```bash
git clone https://github.com/your-username/recipdf.git
cd recipdf
```

### 2. Create virtual environment

| macOS/Linux | Windows |
|-------------|---------|
| `python3 -m venv .venv && source .venv/bin/activate` | `python -m venv .venv && .\.venv\Scripts\activate` |

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the app

```bash
streamlit run app.py
```

> First run may take a few seconds. A browser window should auto-open at http://localhost:8501.

---

## 🧪 Modes of Use

### ✅ Manual (Mock UI)
- Select products by hand for each ingredient
- Simulated pricing / product labels
- Good for UI testing or demos

### 🤖 AI Agent Mode
- Uses GPT to extract shopping list
- Matches items using mock or real Walmart API (configurable)
- Returns a **Walmart Cart URL** and summary

Switch between modes from the **sidebar**.

---

## 📂 File Structure

```bash
📁 recipdf_app/
├── app.py                      # Streamlit frontend
├── load_env.py                # Loads .env vars
├── components/
│   └── ingredient_selector.py # Panel UI
├── agent_definitions/
│   └── unified_cart_autofill_agent.py
├── ...
📄 requirements.txt
📄 README.md
```

---

## 💡 Dev Tips
| Action                         | Command or Tip |
|-------------------------------|----------------|
| Faster reloads (macOS)        | `pip install watchdog` |
| Run on different port         | `streamlit run app.py --server.port 8502` |
| Share on LAN                  | `streamlit run app.py --server.address 0.0.0.0` |
| Stop server                   | `Ctrl+C` in terminal |
| Leave virtual environment     | `deactivate` |

---

## 🧯 Common Issues
## 🛠 Troubleshooting

| Error | Cause / Fix |
|-------|-------------|
| `streamlit: command not found` | Activate virtualenv |
| `KeyError: 'url'` or `string indices must be integers` | Your OpenAI API key is missing or quota exceeded. Add to `.env` |
| Page not loading | Try `http://localhost:8501` manually |
| Cart not generated | Check traceback – might be JSON parse error or fallback response |
| `ModuleNotFoundError`               | Ensure you're in `.venv` and all `requirements.txt` are installed |
| `Port already in use`               | Close other apps on 8501 or pick a new port |
| `TypeError: string indices must be integers` | Likely caused by a malformed result from the agent (not returning dict) |
| `Traceback in Streamlit output`     | Enable logging and use `traceback.format_exc()` to display detailed errors |
---
🎉 You're all set to explore, edit, or extend **ReciPDF** into a smarter, AI-powered grocery planner!

## 👋 Authors

Built by Joshua Upshaw and with AI Agents by Stephen Pierson, future versions adapted by Sankalp Pandey and Solomon Horn