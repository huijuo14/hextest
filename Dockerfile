FROM python:3.9-slim

# Install Firefox with ALL dependencies + wget
RUN apt-get update && apt-get install -y \
    firefox-esr \
    wget \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libxt6 \
    libx11-xcb1 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install geckodriver v0.36.0
RUN wget -q https://github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-linux64.tar.gz \
    && tar -xf geckodriver*.tar.gz -C /usr/local/bin/ \
    && rm geckodriver*.tar.gz \
    && chmod +x /usr/local/bin/geckodriver

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create profile directory
RUN mkdir -p /app/firefox_profile

EXPOSE 5000
CMD ["python", "app.py"]