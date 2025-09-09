from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import re
import pandas as pd
import os
from dotenv import load_dotenv
import tempfile

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Instagram credentials from environment variables for security
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME", "headquater_ai_")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "Stevene2025@")

# Set up headless Chrome options
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        return driver
    except Exception as e:
        print(f"❌ Failed to create Chrome driver: {str(e)}")
        raise Exception(f"Chrome driver setup failed: {str(e)}")

# Login to Instagram
def login_instagram(driver, username, password):
    try:
        print("🔑 Attempting to login to Instagram...")
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(5)
        
        # Find and fill username
        username_input = driver.find_element(By.NAME, "username")
        username_input.clear()
        username_input.send_keys(username)
        
        # Find and fill password
        password_input = driver.find_element(By.NAME, "password")
        password_input.clear()
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)
        
        time.sleep(8)
        
        # Check if login was successful
        current_url = driver.current_url
        if "accounts/login" in current_url:
            raise Exception("Login failed - still on login page")
        
        print("✅ Login successful!")
        
    except Exception as e:
        print(f"❌ Login failed: {str(e)}")
        raise Exception(f"Instagram login failed: {str(e)}")

# Search for hashtag
def search_hashtag(driver, tag):
    driver.get(f"https://www.instagram.com/explore/tags/{tag}/")
    time.sleep(5)

# Get post links without duplicates
def get_post_links(driver, limit=1000):
    links = set()
    last_height = driver.execute_script("return document.body.scrollHeight")

    while len(links) < limit:
        anchors = driver.find_elements(By.TAG_NAME, "a")
        for a in anchors:
            href = a.get_attribute("href")
            if href and "/p/" in href:
                links.add(href)

        # Scroll down
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:  # No new posts
            break
        last_height = new_height

    return list(links)[:limit]

# Extract bio + caption + username + phone numbers
def extract_info(driver, post_url):
    driver.get(post_url)
    time.sleep(6)

    try:
        username = driver.find_element(By.XPATH, '//a[contains(@href, "/") and @role="link"]').text
    except:
        username = "Unknown"

    try:
        caption = driver.find_element(By.XPATH, '//div[@data-testid="post-comment-root"]').text
    except:
        caption = ""

    bio = ""
    if username != "Unknown":
        try:
            driver.get(f"https://www.instagram.com/{username}/")
            time.sleep(6)

            try:
                bio_section = driver.find_element(By.CSS_SELECTOR, "div.-vDIg span")
                bio = bio_section.text
            except:
                try:
                    meta_desc = driver.find_element(By.XPATH, '//meta[@name="description"]').get_attribute('content')
                    bio = meta_desc
                except:
                    bio = ""
        except:
            bio = ""

    # Find phone numbers with regex
    numbers = re.findall(r'\+?\d[\d\s\-]{7,}', bio + " " + caption)

    return {
        "Username": username,
        "Phone Numbers": ", ".join(numbers) if numbers else "None",
        "Bio": bio.strip()
    }

# Main scraping logic
def scrape(hashtags, limit=2000):
    driver = get_driver()
    try:
        login_instagram(driver, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        data = []
        seen_usernames = set()  # Avoid duplicate usernames

        for tag in hashtags:
            search_hashtag(driver, tag)
            links = get_post_links(driver, limit)

            print(f"🔍 Jumla ya links zilizopatikana kwa #{tag}: {len(links)}")

            for i, url in enumerate(links, start=1):
                info = extract_info(driver, url)

                # Avoid duplicates
                if info["Username"] not in seen_usernames and info["Username"] != "Unknown":
                    seen_usernames.add(info["Username"])
                    data.append(info)
                    print(f"✅ {i}/{len(links)} -- {info}")

        return data
    finally:
        driver.quit()

# API Endpoint to trigger scraping
@app.route('/scrape', methods=['POST'])
def scrape_endpoint():
    try:
        req_data = request.get_json()
        if not req_data:
            return jsonify({"error": "Invalid JSON"}), 400

        hashtags = req_data.get('hashtags', ["viatukariakoo"])
        limit = req_data.get('limit', 50)  # Reduced default limit

        if not isinstance(hashtags, list) or not hashtags:
            return jsonify({"error": "hashtags must be a non-empty list"}), 400

        print(f"🚀 Starting scrape for hashtags: {hashtags}, limit: {limit}")
        
        data = scrape(hashtags, limit)
        
        print(f"✅ Scraping completed. Found {len(data)} unique users")
        
        return jsonify({
            "success": True,
            "data": data,
            "total_users": len(data),
            "hashtags_searched": hashtags
        })
        
    except Exception as e:
        print(f"❌ Error in scrape_endpoint: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Home route for testing
@app.route('/')
def home():
    return jsonify({"message": "Instagram Scraper API. POST to /scrape with {'hashtags': ['tag1'], 'limit': 2000}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)