FROM python:3.11-slim

# Install Firefox and dependencies
RUN apt-get update && apt-get install -y \
    firefox-esr \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install geckodriver
RUN wget -q https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz \
    && tar -xf geckodriver*.tar.gz -C /usr/local/bin/ \
    && rm geckodriver*.tar.gz \
    && chmod +x /usr/local/bin/geckodriver

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create profile directory
RUN mkdir -p /app/firefox_profile

EXPOSE 8000
CMD ["python", "app.py"]