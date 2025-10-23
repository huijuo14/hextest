FROM python:3.9-slim

# Install Firefox and essentials
RUN apt-get update && apt-get install -y \
    firefox-esr \
    wget \
    xvfb \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install specific geckodriver version
RUN wget -q https://github.com/mozilla/geckodriver/releases/download/v0.30.0/geckodriver-v0.30.0-linux64.tar.gz \
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
CMD ["gunicorn", "--config", "gunicorn_config.py", "app:app"]