from urllib import request
from bs4 import BeautifulSoup

BASE_URL = 'http://new.mfk.msu.ru/course/'
student_keys = ['name', 'faculty', 'study_mode', 'degree', 'year']
course_keys = ['name', 'faculty', 'online', 'status']

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

        course = {name : item.string for name, item in zip(course_keys, line.contents)}
        course['id'] = int(line['id'])
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
    return {course['id']: course for course in courses}

def parse_course_details_and_students(course):
    """
    Search for course page using course['id'], add extra information
    and list of enrolled students to course dictionary in place

    :param course: dictionary
    :return: students -- dictionary
    """
    with request.urlopen(course_url(course['id'])) as response:
        page = BeautifulSoup(response.read(), 'lxml')
        detailed_info = page.find('div', {'class': 'well'})
        # skip epty rows
        detailed_info = [item for item in detailed_info.contents if item.string is None]

        '''
            Here you can add any detailed information to course dictionary
            I just need number total and left places
        '''

        taken_places, total_places = [x.strip() for x in
                                     detailed_info[-1].contents[-1].split('/')]
        course['taken_places'] = taken_places
        course['total_places'] = total_places

        # parse students
        students = {}
        table = page.find('table', {'class': 'table'})
        for row in table.find('tbody').contents:
            # skip empty rows
            if row.string is not None:
                continue

            student = {key : value.text for key, value in zip(student_keys, row.contents)}
            student['name'] = student['name'].split()
            student['data-key'] = int(row['data-key'])
            students[student['data-key']] = student

        course['students'] = {int(student_id) for student_id in students.keys()}

    return students

courses = get_courses()
students = {}
for course_id, course in courses.items():
    print('Parsing course {}: {}'.format(course_id, course['name']))
    course_students = parse_course_details_and_students(course)

    # insert course_students into students
    for id, student in course_students.items():
        if id in students:
            students[id]['courses'].insert(course_id)
        else:
            student['courses'] = {course_id}
            students[id] = student

print('Done')

course_number = {}
for id, student in students.items():
    try:
        course_number[len(student['courses'])] += 1
    except KeyError:
        course_number[len(student['courses'])] = 0

print(course_number)