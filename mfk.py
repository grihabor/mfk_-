from urllib import request
from bs4 import BeautifulSoup

BASE_URL = 'http://new.mfk.msu.ru/course/'


def courses_list_url(page = 1):
    return '{}list?page={}'.format(BASE_URL, page + 1)


def course_url(course_id):
    return '{}view?id={}'.format(BASE_URL, course_id)


def get_num_pages(html):
    page = BeautifulSoup(html, 'lxml')
    numPages = page.find('ul', {'class': 'pagination'}).find_all('li')[-2].text
    return int(numPages)


def parse_list_page(html):
    page = BeautifulSoup(html, 'lxml')
    courses_table = page.find('table', {'class': 'table'})

    courses = []

    for line in courses_table.find('tbody').children:
        # skip empty rows
        if line.string is not None:
            continue

        course = {name : item.string for name, item in
            zip(['name', 'faculty', 'online', 'status'], line.contents)}
        course['id'] = line['id']
        courses.append(course)

    return courses


def get_courses():

    courses = []

    html = request.urlopen(BASE_URL + 'list').read()
    num_pages = get_num_pages(html)
    for page in range(num_pages):
        with request.urlopen(courses_list_url(page)) as response:
            html = response.read()
            courses += parse_list_page(html)
    return courses

# Changes course in place!
def parse_course_details_and_people(course):
    with request.urlopen(course_url(course['id'])) as response:
        page = BeautifulSoup(response.read(), 'lxml')
        detailed_info = page.find('div', {'class': 'well'})
        # skip epty rows
        detailed_info = [item for item in detailed_info.contents if item.string is None]

        '''
            Here you can add any detailed information to course dictionary
            I just need number total and left places
        '''

        left_places, total_places = [x.strip() for x in
                                     detailed_info[-1].contents[-1].split('/')]
        print(left_places, total_places)
        course['left_places'] = left_places
        course['total_places'] = total_places



courses = get_courses()
for course in courses:
    parse_course_details_and_people(course)
print(courses)