from flask import Flask, request, render_template, jsonify
from helium import *
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_browser():
    browser = start_chrome("https://www.mauribac.com/bac-2023-pFrFwkSfV/", headless=False)
    return browser

def scrape_student_details(html):
    soup = BeautifulSoup(html, 'html.parser')
    student_details = {}

    name_tag = soup.select_one('h1.text-2xl.font-bold.text-center.mb-1')
    if name_tag:
        student_details['name'] = name_tag.text.strip()

    id_tag = soup.select_one('h3.font-mono')
    if id_tag:
        student_details['id'] = id_tag.text.strip()

    decision_tag = soup.select_one('div.px-2')
    if decision_tag:
        student_details['decision'] = decision_tag.text.strip()

    average_tag = soup.select_one('div.font-bold.text-xs')
    if average_tag:
        student_details['average'] = average_tag.text.strip()

    details_link_tag = soup.select_one('a[href^="http://dec.education.gov.mr/bac-21/"]')
    if details_link_tag:
        student_details['detailed_results_link'] = details_link_tag['href']

    school_tag = soup.select_one('a[href*="/ecole/"]')
    if school_tag:
        student_details['school'] = school_tag.text.strip()

    region_tag = soup.select_one('a[href*="/wilaya/"]')
    if region_tag:
        student_details['region'] = region_tag.text.strip()

    center_tag = soup.select('a[href*="/centre/"]')
    if center_tag:
        student_details['center'] = center_tag[-1].text.strip()

    return student_details

def get_student_info(student_id):
    browser = start_browser()
    
    wait_until(Text("نتائج الباكلوريا 2023").exists, timeout_secs=20)
    
    try:
        student_id_input = S("input#search-by-unique-number-input")
        if student_id_input.exists():
            logger.info(f"Writing student ID {student_id} into input field")
            write(student_id, into=student_id_input)
        else:
            logger.error("Student ID input field not found.")
            raise LookupError("Student ID input field not found.")
        
        search_button = S("input[type='submit'][value='ابحث']")
        if search_button.exists():
            logger.info("Clicking the search button")
            click(search_button)
        else:
            logger.error("Search button not found.")
            raise LookupError("Search button not found.")
        
        wait_until(Text("القرار").exists, timeout_secs=20)
        
        html = browser.page_source
        if "الصفحة المطلوبة غير موجودة" in html:
            logger.info("404 Page Not Found for student ID: %s", student_id)
            raise LookupError("404 Page Not Found")
        
        student_details = scrape_student_details(html)
        logger.info(f"Scraped student details: {student_details}")
        
    except LookupError as e:
        logger.error(f"Lookup error occurred: {e}")
        student_details = {}
    
    except Exception as e:
        logger.exception("An unexpected error occurred")
        student_details = {}
    
    finally:
        kill_browser()
    
    return student_details

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    student_id = request.form['student_id']
    try:
        student_info = get_student_info(student_id)
        
        if student_info:
            return render_template('student_info.html', student=student_info)
        else:
            return render_template('404.html'), 404
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == "__main__":
    app.run(debug=True)
