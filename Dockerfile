FROM python:3.12-bookworm

WORKDIR /root

RUN apt-get update && apt-get install -y \
    wget \
    && rm -rf /var/lib/apt/lists/*
    
RUN pip install fastapi uvicorn playwright playwright-stealth

RUN playwright install chromium --with-deps

COPY . .
CMD ["uvicorn", "api.scraper:app", "--host", "0.0.0.0", "--port", "8000"]
