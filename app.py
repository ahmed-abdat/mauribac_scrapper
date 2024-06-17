from flask import Flask, render_template, request, jsonify
from helium import start_chrome, Text, S, write, click, wait_until, kill_browser
from bs4 import BeautifulSoup
import json
import logging

app = Flask(__name__)

def start_browser():
    return start_chrome("https://www.mauribac.com/bac-2023-pFrFwkSfV/", headless=True)

def scrape_student_details(html):
    soup = BeautifulSoup(html, 'html.parser')
    student_details = {}

    # Extracting student's name
    name_tag = soup.select_one('h1.text-2xl.font-bold.text-center.mb-1')
    if name_tag:
        student_details['name'] = name_tag.text.strip()

    # Extracting student ID
    id_tag = soup.select_one('h3.font-mono')
    if id_tag:
        student_details['id'] = id_tag.text.strip()

    # Extracting student decision
    decision_tag = soup.select_one('div.px-2')
    if decision_tag:
        student_details['decision'] = decision_tag.text.strip()

    # Extracting student average
    average_tag = soup.select_one('div.font-bold.text-xs')
    if average_tag:
        student_details['average'] = average_tag.text.strip()

    # Extracting detailed results link
    details_link_tag = soup.select_one('a[href^="http://dec.education.gov.mr/bac-21/"]')
    if details_link_tag:
        student_details['detailed_results_link'] = details_link_tag['href']

    # Extracting student school
    school_tag = soup.select_one('a[href*="/ecole/"]')
    if school_tag:
        student_details['school'] = school_tag.text.strip()

    # Extracting student region
    region_tag = soup.select_one('a[href*="/wilaya/"]')
    if region_tag:
        student_details['region'] = region_tag.text.strip()

    # Extracting student center
    center_tag = soup.select('a[href*="/centre/"]')
    if center_tag:
        student_details['center'] = center_tag[-1].text.strip()  # The center is the last matching element

    return student_details

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    student_id = request.form['student_id']
    try:
        student_info = get_student_info(student_id)
        if not student_info:
            return render_template('404.html'), 404
        return jsonify(student_info)
    except Exception as e:
        logging.exception("An unexpected error occurred")
        return jsonify({'error': 'An unexpected error occurred'}), 500

def get_student_info(student_id):
    browser = start_browser()

    try:
        wait_until(Text("نتائج الباكلوريا 2023").exists, timeout_secs=20)

        student_id_input = S("input#search-by-unique-number-input")
        if student_id_input.exists():
            write(student_id, into=student_id_input)
        else:
            raise LookupError("Student ID input field not found.")

        search_button = S("input[type='submit'][value='ابحث']")
        if search_button.exists():
            click(search_button)
        else:
            raise LookupError("Search button not found.")

        wait_until(Text("القرار").exists, timeout_secs=20)

        html = browser.page_source
        student_details = scrape_student_details(html)

    except LookupError as e:
        logging.error(f"An error occurred: {e}")
        student_details = {}

    finally:
        kill_browser()

    return student_details

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
    app.run(debug=True)
