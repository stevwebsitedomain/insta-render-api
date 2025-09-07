# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget gnupg2 ca-certificates unzip \
    fonts-liberation libnss3 libxss1 libasound2 \
    libatk1.0-0 libatk-bridge2.0-0 libgtk-3-0 libgbm1 libx11-xcb1 \
    libxcomposite1 libxcursor1 libxdamage1 libxrandr2 libappindicator3-1 \
    libdbus-1-3 curl \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome 114 explicitly to match ChromeDriver
RUN wget https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.199-1_amd64.deb \
    && dpkg -i google-chrome-stable_114.0.5735.199-1_amd64.deb || apt-get -f install -y \
    && rm google-chrome-stable_114.0.5735.199-1_amd64.deb

# Install Chromium driver
RUN apt-get update && apt-get install -y chromium-driver && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements & install
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy app code
COPY . .

# Expose port
EXPOSE ${PORT}

# Run app with gunicorn using Render PORT variable
CMD ["bash", "-lc", "gunicorn --bind 0.0.0.0:${PORT} app:app --workers 1 --threads 4"]
