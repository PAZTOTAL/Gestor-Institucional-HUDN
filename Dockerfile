FROM python:3.12-slim

# Dependencias del sistema: compilacion + ODBC + Cairo + Playwright/Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gnupg2 apt-transport-https \
    build-essential libffi-dev \
    unixodbc-dev \
    libcairo2-dev libfreetype6-dev \
    libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libatspi2.0-0 libx11-6 \
    libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libasound2 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ODBC Driver 17 for SQL Server (Debian 12 / Bookworm — metodo moderno sin apt-key)
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | \
      gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] \
      https://packages.microsoft.com/debian/12/prod bookworm main" \
      > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && rm -rf /var/lib/apt/lists/*

# Locale UTF-8 para soporte de ñ, tildes y caracteres especiales
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONIOENCODING=utf-8

WORKDIR /app

# Instalar dependencias Python (usa archivo limpio sin paquetes Windows)
COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt

# Instalar navegador Playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/playwright-browsers
RUN python -m playwright install chromium

# Copiar codigo fuente
COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
