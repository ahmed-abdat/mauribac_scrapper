from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import logging

app = Flask(__name__)

def fetch_student_page(student_id):
    url = f"https://www.mauribac.com/bac-2023-pFrFwkSfV/numero/{student_id}/"
    response = requests.get(url)
    if response.status_code == 404:
        raise requests.HTTPError("404 Not Found")
    response.raise_for_status()  # Ensure we raise an error for bad responses
    response.encoding = 'utf-8'  # Ensure the response is treated as UTF-8
    return response.text

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
        html = fetch_student_page(student_id)
        student_info = scrape_student_details(html)
        if not student_info:
            return render_template('404.html'), 404
        return render_template('student_info.html', student_info=student_info)
    except requests.HTTPError as e:
        if "404" in str(e):
            logging.error("Student ID not found: 404 error")
            return render_template('404.html'), 404
        logging.exception("HTTP error occurred")
        return jsonify({'error': 'HTTP error occurred'}), 500
    except Exception as e:
        logging.exception("An unexpected error occurred")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
    app.run(debug=True)
