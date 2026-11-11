# TextVigil — Quick Start Guide (Windows PowerShell)

## Option A: One-Click Batch Scripts (Recommended)

```powershell
cd "D:\90 days\90-days-90-projects-day-18-messageshield"
.\setup.bat
.\run.bat
```

Then open **http://127.0.0.1:8000** in your browser.

---

## Option B: Manual PowerShell Setup

### 1. Create & Activate Python Virtual Environment (Python 3.12 recommended)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Copy Environment Config

```powershell
if (!(Test-Path ".env")) { Copy-Item ".env.example" ".env" }
```

### 3. Download Dataset, Train Models & Generate Sample Assets

```powershell
python scripts\download_dataset.py
python scripts\train_models.py
python scripts\generate_demo_assets.py
```

### 4. Install & Build React Frontend

```powershell
cd frontend
npm install
npm run build
cd ..
```

### 5. Start TextVigil

Production single-port mode (`http://127.0.0.1:8000`):

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

Or Development HMR mode (`http://127.0.0.1:5173` + API on `:8000`):

```powershell
.\run.bat --dev
```

### 6. Run Tests

```powershell
.\test.bat
```
