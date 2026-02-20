# 📊 M-Pesa Transactions Analyzer

A Python backend service that parses encrypted M-Pesa PDF statements, extracts transactions, and categorizes them into actionable spending insights. Built with Flask, Celery, and Redis for asynchronous processing.

## 🤔 Problem

M-Pesa generates PDF statements that are password-protected and difficult to analyze programmatically. Transaction data is locked inside PDF tables with inconsistent formatting — multi-row cells, newline-separated values, and comma-formatted currencies. There's no easy way to answer:

- **Where am I spending the most?** (Paybills, Merchant/Till payments)
- **Who do I send the most money to?**
- **What are my monthly transaction costs?**

## ✅ Solution

This service accepts an encrypted M-Pesa PDF statement via a REST API, decrypts it, extracts tabular data using Camelot (Ghostscript-backed), sanitizes and normalizes the data with Pandas, and classifies each transaction into one of four categories:

| Category | Description |
|---|---|
| **Paybill** | Pay Bill Online transactions (e.g., utilities, subscriptions) |
| **Merchant Payment** | Till/merchant payments (e.g., retail, groceries) |
| **Send Money** | Person-to-person transfers |
| **Charge** | M-Pesa service/transaction fees |

Processing is handled **asynchronously** via Celery workers backed by Redis, with real-time progress tracking.

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│              │     │              │     │              │
│  Client App  │────▶│  Flask API   │────▶│ Celery Worker│
│              │     │  (Port 5000) │     │              │
└──────────────┘     └──────┬───────┘     └──────┬───────┘
                            │                     │
                            │    ┌────────────┐   │
                            └───▶│   Redis    │◀──┘
                                 │  (Broker)  │
                                 └────────────┘

Processing Pipeline:
PDF Upload ──▶ Decrypt (PyPDF2) ──▶ Extract Tables (Camelot)
          ──▶ Sanitize DataFrame (Pandas) ──▶ Classify Transactions (Regex)
          ──▶ Return JSON Results
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Redis (running locally or via Docker)
- Ghostscript (`brew install ghostscript` / `apt-get install ghostscript`)

### Run with Docker

```bash
# Build and run
docker build -t transactions-analyzer .
docker run -p 5000:5000 transactions-analyzer
```

### Run Locally

```bash
# Clone the repository
git clone https://github.com/bryan-mwas/transactions-analyzer.git
cd transactions-analyzer

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env  # Configure REDIS_HOST

# Start Redis (if not already running)
redis-server

# Start the Flask app + Celery worker
./start_ps.sh
```

## 📡 API Reference

### Upload a Statement

```http
POST /
Content-Type: multipart/form-data
```

| Parameter  | Type   | Description                              |
|-----------|--------|------------------------------------------|
| `file`    | File   | Encrypted M-Pesa PDF statement (≤1.5MB)  |
| `password`| String | PDF decryption password                   |

**Response** `202 Accepted`
```json
{
  "taskID": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### Poll Task Result

```http
GET /result/<taskID>
```

**Response (In Progress)**
```json
{
  "state": "PROGRESS",
  "ready": false,
  "successful": false,
  "failed": false,
  "response": { "done": 3, "total": 12 }
}
```

**Response (Complete)**
```json
{
  "state": "SUCCESS",
  "ready": true,
  "successful": true,
  "failed": false,
  "response": [
    {
      "category": "Paybill",
      "completion_time": "2024-01-15 14:30:00",
      "amount": 1500.00,
      "recipient_id": "888880",
      "recipient_name": "KPLC PREPAID",
      "receipt_id": "ABC1234XYZ"
    },
    {
      "category": "Merchant Payment",
      "completion_time": "2024-01-15 16:45:00",
      "amount": 350.00,
      "recipient_id": "123456",
      "recipient_name": "NAIVAS SUPERMARKET",
      "receipt_id": "DEF5678UVW"
    }
  ]
}
```

## 🔧 Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **API** | Flask | REST endpoint for uploads and result polling |
| **Task Queue** | Celery | Async PDF processing with progress tracking |
| **Message Broker** | Redis | Task broker and result backend |
| **PDF Extraction** | Camelot + Ghostscript | Table extraction from PDF pages |
| **PDF Decryption** | PyPDF2 | Decrypt password-protected statements |
| **Data Processing** | Pandas | DataFrame sanitization and normalization |
| **Classification** | Regex (re) | Transaction categorization via pattern matching |
| **Containerization** | Docker | Reproducible deployment with non-root user |

## 📁 Project Structure

```
transactions-analyzer/
├── app.py                          # Flask app + API routes
├── tasks.py                        # Celery task definitions
├── packages/
│   └── pdfLoader/
│       ├── load_pdf.py             # MpesaLoader — PDF decryption & table extraction
│       └── process_data.py         # TransactionFactory — classification engine
├── Dockerfile                      # Multi-stage Docker build
├── .dockerignore
├── requirements.txt
├── poetry.lock
├── start_ps.sh                     # Startup script (Flask + Celery)
└── README.md
```

## 🔍 Key Design Decisions

1. **Async processing with Celery** — PDF parsing is CPU-intensive and can take seconds per page. Celery workers prevent the API from blocking, and clients can poll for progress.

2. **Validation at the PDF metadata level** — The `MpesaLoader` verifies the PDF was created by `Safaricom PLC` with subject `M-PESA Statement` before processing, rejecting invalid uploads early.

3. **Regex-based classification** — Each transaction type has distinct patterns in the M-Pesa statement format. Regex matching provides fast, deterministic classification without requiring ML models.

4. **Temporary file cleanup** — Uploaded PDFs are written to `NamedTemporaryFile` and explicitly cleaned up in a `finally` block to prevent disk accumulation.

5. **Non-root Docker user** — The container runs as `appuser` (UID 10001) following Docker security best practices.

## 📄 License

This project is open source. See [LICENSE](LICENSE) for details.

## 👤 Author

**Brian Mwathi** — [GitHub](https://github.com/bryan-mwas) · [LinkedIn](https://www.linkedin.com/in/brian-wangome-27645b141/)
