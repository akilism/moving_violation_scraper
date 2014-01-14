__author__ = 'akilharris'

import httplib
from bs4 import BeautifulSoup
import os

#Load http://www.nyc.gov/html/nypd/html/traffic_reports/traffic_summons_reports.shtml
#grab all pdfs and save to a folder
path = "raw_data/pdf/"


def scrape(url):
    conn = httplib.HTTPConnection("www.nyc.gov")
    conn.request("GET", url)
    response = conn.getresponse()
    if response.status == 200:
        temp_data = response.read()
        conn.close()
        return temp_data


def parse(extension, raw_data):
    links = []
    soup = BeautifulSoup(raw_data)
    for link in soup.find_all("a"):
        href = link.get("href")
        if href.find(extension) != -1:
            links.append(href)
    return links


def save_links(links):
    if not os.path.exists(path):
        parts = path.split("/")
        for part in parts:
            if len(part) > 0:
                os.mkdir(part)
                os.chdir(part)
    else:
        os.chdir(path)

    # print(os.getcwd())
    for link in links:
        link = str(link).replace("../..", "/html/nypd")
        file_name = link.split("/")[-1]
        precinct = file_name.strip("sum.pdf")
        print("Saving: " + precinct + " - " + os.getcwd() + "/" + file_name)
        file_data = scrape(link, False)
        with open(file_name, "wb") as f:
            f.write(file_data)


def getPDFs():
    raw_data = scrape("/html/nypd/html/traffic_reports/traffic_summons_reports.shtml")
    links = parse(".pdf", raw_data)
    save_links(links)


getPDFs()