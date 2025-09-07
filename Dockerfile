# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# Install system dependencies and Chromium
RUN apt-get update && apt-get install -y \
    wget gnupg2 ca-certificates unzip \
    fonts-liberation libnss3 libxss1 libasound2 \
    libatk1.0-0 libatk-bridge2.0-0 libgtk-3-0 libgbm1 libx11-xcb1 \
    libxcomposite1 libxcursor1 libxdamage1 libxrandr2 libappindicator3-1 \
    libdbus-1-3 curl apt-transport-https sudo \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome 114 stable
RUN wget https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.199-1_amd64.deb \
    && dpkg -i google-chrome-stable_114.0.5735.199-1_amd64.deb || apt-get -f install -y

# Install ChromeDriver for Chrome 114
RUN wget https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver \
    && rm chromedriver_linux64.zip

WORKDIR /app

# Copy requirements & install
COPY requirements.txt . 
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the app code
COPY . .

EXPOSE ${PORT}

# Run the Flask app with Gunicorn
CMD ["bash", "-lc", "gunicorn --bind 0.0.0.0:${PORT} app:app --workers 1 --threads 4"]

