import csv
import pandas as pd
import requests
import re
import sys
from datetime import datetime

# specialization=1.117 - testing
# area - country

headers = {"User-Agent": "api-test-agent"}

at_languages = {"Python": {"pattern": re.compile(r"(?i)python"), "count": 0},
                "Java": {"pattern": re.compile(r"(?i)java(?!Script)\b"), "count": 0},
                "JavaScript": {"pattern": re.compile(r"(?i)js(?!json)\b|javascript"), "count": 0},
                "C#": {"pattern": re.compile(r"(?i)C#|с#"), "count": 0},
                "Scala": {"pattern": re.compile(r"(?i)scala\b"), "count": 0},
                "C++": {"pattern": re.compile(r"(?i)C\+\+|c\+\+"), "count": 0},
                "TypeScript": {"pattern": re.compile(r"(?i)typescript\b"), "count": 0},
                "Kotlin": {"pattern": re.compile(r"(?i)kotlin\b"), "count": 0},
                "Swift": {"pattern": re.compile(r"(?i)swift\b"), "count": 0}
                }


def getAreaCode(country_name="Россия"):
    """ Return area id """
    countries_url = "https://api.hh.ru/areas/countries"
    response = requests.get(countries_url, headers).json()
    for country in response:
        if country["name"] == country_name:
            return country["id"]
    print("Country {} is not found".format(country_name))
    sys.exit(0)


def writeCSVFile(data, field_name, file_name):
    """Write csv file"""
    with open(file_name, 'w', newline='') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=field_name)
        if output_file.tell() == 0:  # check cursor position before write header.
            writer.writeheader()
        writer.writerows(data)


def composeFileName(filename_pattern):
    """compose csv file name based on provided filename_pattern without its extension."""
    current_date = datetime.now().strftime("%d%m%Y")
    return filename_pattern + "_" + current_date + ".csv"

# check if country provided in CLI. If not, the Russia by default
if len(sys.argv) > 1:
    area_id = getAreaCode(str(sys.argv[1]))
else:
    area_id = getAreaCode()

page = 0
area_url = "https://api.hh.ru/vacancies?specialization=1.117&area={}&page={}".format(area_id, page)
vacancies_list = requests.get(area_url, headers).json() # get first 20 vacancies and total number of vacancies in area
pages = vacancies_list["pages"] # as per hh api it can return up to 100 pages only no matter how many total vacancies
vacancy_details = []
# exclude vacancy for programmers.
exclude_programmers = re.compile("(?i)программист|разработчик|developer|programmer|devops")

for page in range(pages):
    for vacancy in vacancies_list["items"]:
        vacancy_id = vacancy["id"]
        vacancy_details_url = "https://api.hh.ru/vacancies/{}".format(vacancy_id)
        response = requests.get(vacancy_details_url).json() # get vacancy details
        vacancy_description = response["description"]
        name = response['name']
        employer = response['employer']['name']
        url = response['alternate_url']
        salary_from = 'NA'
        salary_to = 'NA'
        if response["salary"]:
            if "from" in response["salary"]:
                salary_from = response["salary"]["from"]
            if "to" in response["salary"]:
                salary_to = response["salary"]["to"]

        for lang in at_languages:
            if exclude_programmers.search(response["name"]):
                print("This is vacancy for programmers, skip it")
                print("URL: {}".format(response["alternate_url"]),"\n")
                break
            if at_languages[lang]["pattern"].search(vacancy_description):
                at_languages[lang]["count"] += 1
                vacancy_details.append({"Name": name,
                                       "Employer": employer,
                                       "Language": lang,
                                       "Frequency": at_languages[lang]["count"],
                                       "Salary From": salary_from,
                                       "Salary To": salary_to,
                                       "URL": url})

    next_page_url = "https://api.hh.ru/vacancies?specialization=1.117&area={}&page={}".format(area_id, page+1)
    vacancies_list = requests.get(next_page_url, headers).json()

fields = ["Name", "Employer", "Language", "Frequency", "Salary From", "Salary To", "URL"]
filename = composeFileName("vacancy_details")
writeCSVFile(vacancy_details, fields, filename)

# gather how many times each language is mentioned in vacancy description.
languages_score = {}
for at_lan in at_languages:
    languages_score[at_lan] = at_languages[at_lan]["count"]

# sort language statistic and save in csv file
df_lang = pd.DataFrame(languages_score.items(), columns=["Language", "Count"])
df_lang.sort_values(by=["Count"], ascending=False).to_csv(composeFileName("language_statistic"), index=False)

print(df_lang.sort_values(by=["Count"], ascending=False, ignore_index=True))