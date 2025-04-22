```markdown
# 📄 ReciPDF Streamlit App — **Zero‑to‑Launch** Guide
A beginner‑friendly walkthrough for downloading the code and opening the ReciPDF web interface on your own computer.
---

## 🔍 What the app does
* Upload a **PDF or text recipe**.  
* The app extracts the text, highlights any “Ingredients” section, and (optionally) lets you try a mock search against Walmart‑style product fields.  
* Runs entirely in your browser—no servers or databases to set up.
---

## 🛠 What you need (**once only**)
| Tool | Why you need it | Quick install |
|------|-----------------|---------------|
| **Python 3.8 or newer** | Runs the Streamlit framework | <https://www.python.org/downloads/> <br>Windows → tick “Add Python to PATH” on installer first page |
| **Git** | Downloads the code from GitHub | macOS → `brew install git`  •  Windows → <https://git-scm.com/download/win> |
| **VS Code** (optional) | Nice editor with built‑in terminal | <https://code.visualstudio.com/> |
> 💡 **No admin rights?**  
> You can install Python for *“just me”* and Git for *“current user”* — both installers have that option.

---
## 🚀 Step‑by‑step (run every time you start fresh)

### 1. Open a terminal
* **VS Code**: `View` ▸ `Terminal` (shortcut <kbd>Ctrl</kbd>+<kbd>`</kbd>)  
* **macOS**: Launch **Terminal** from Spotlight  
* **Windows**: **PowerShell** or **Command Prompt**

### 2. Download / update the code
```bash
# ⬇️ clone the repo the first time
git clone https://github.com/<your‑username>/<repo-name>.git
cd <repo-name>
# 🔄 already have it? just update
git pull
```
> **What this does**  
> *`git clone`* copies the project folder from GitHub to your computer.  
> *`git pull`* grabs the latest changes next time.

### 3. Create a *virtual environment* (one‑time per computer)
A **virtual environment** is like a private copy of Python just for this project—so installed libraries don’t mess with other apps.
| macOS / Linux | Windows (PowerShell) |
|---------------|----------------------|
| ```bash
python3 -m venv .venv
source .venv/bin/activate
``` | ```powershell
python -m venv .venv
.\.venv\Scripts\activate
``` |
Term prompt now begins with `(.venv)` → **good sign**.
*(Later, just run the “activate” line to re‑enter the venv—no need to recreate it.)*

### 4. Install the Python libraries
```bash
pip install -r requirements.txt
```
> This reads **`requirements.txt`** and downloads **Streamlit**, **PyPDF2**, etc.  
> You only re‑run this if *requirements.txt* changes.

### 5. Launch the app
```bash
streamlit run ReciPDF_UI.py     # or app.py if that’s your main file
```
*After a few seconds you’ll see:*
```
You can now view your Streamlit app in your browser.
  Local URL:   http://localhost:8501
  Network URL: http://192.168.x.xx:8501
```
A browser tab should open automatically.  
If not, copy‑paste **`http://localhost:8501`** into Chrome/Edge/Safari.
---

## 💡 Daily developer tips
| Tip | How |
|-----|-----|
| **Auto‑reload** on file‑save | Keep the terminal running; edit *ReciPDF_UI.py* in VS Code; press **Save** → browser refreshes instantly. |
| Faster reload (mac/Linux) | `pip install watchdog` (adds fast file‑watcher). |
| Change port | `streamlit run ReciPDF_UI.py --server.port 8502` |
| Share on same Wi‑Fi | `streamlit run ReciPDF_UI.py --server.address 0.0.0.0` <br>Friend browses to `http://YOUR-LAN-IP:8501` (may need firewall allow). |
| Stop the app | Click the terminal window and press **Ctrl +C** (or **⌃ C**). |
| Leave the venv | `deactivate` (type in terminal). |
---

## ❓ Troubleshooting
| Message | Likely cause / fix |
|---------|-------------------|
| **`streamlit: command not found`** | Virtual env not active → activate it; or install requirements again. |
| **Page cannot be reached** | App not running, or running on different port → check terminal, look for `8501` line. |
| **Permission denied / `pip` fails** | On macOS use `python3 -m pip install ...` inside the venv. |
| **Port already in use** | Another Streamlit still open → close its tab and press Ctrl +C, or choose a new port. |
---

🎉  That’s it! You now have ReciPDF running locally, auto‑reloading as you tweak the code, with zero risk to system‑wide Python packages.
```
