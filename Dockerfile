FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    wget \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libgbm1 \
    && rm -rf /var/lib/apt/lists/*

ENV PLAYWRIGHT_BROWSERS_PATH=0

RUN pip install --no-cache-dir playwright && \
    python -m playwright install && \
    playwright install-deps

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV PYTHONPATH="/app:${PYTHONPATH}"
ENV STREAMLIT_WATCHER_TYPE="none"

EXPOSE 8501

CMD ["streamlit", "run", "app/main.py", "--server.enableCORS", "false"]
