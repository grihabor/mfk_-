from collections import OrderedDict
from urllib import request
from bs4 import BeautifulSoup
import csv

BASE_URL = 'http://new.mfk.msu.ru/course/'
URL_PARAMS_TEMPLATE = ['CourseSearch[name_ru]={name_ru}',
                       'CourseSearch[msu_faculty_id]={msu_faculty_id}',
                       'CourseSearch[is_online]={is_online}',
                       'CourseSearch[course_status_id]={course_status_id}',
                       'CourseSearch[fall_year]={fall_year}',
                       'CourseSearch[semester_number]={semester_number}']

student_keys = ['name', 'faculty', 'study_mode', 'degree', 'year']
course_keys = ['name', 'faculty', 'online', 'status']

student_columns = OrderedDict()
student_columns['name'] = 'Имя'
student_columns['faculty'] = 'Факультет'
student_columns['degree'] = 'Вид подготовки'
student_columns['year'] = 'Курс'
student_columns['study_mode'] = 'Форма обучения'
student_columns['courses'] = 'Записался на курсы'

course_columns = OrderedDict()
course_columns['id'] = 'Id'
course_columns['name'] = 'Название курса'
course_columns['faculty'] = 'Факультет'
course_columns['taken_places'] = 'Записалось'
course_columns['total_places'] = 'Всего мест'
course_columns['online'] = 'Online'
course_columns['status'] = 'Статус'

class MFKManager:

    def __init__(self, name_ru='', msu_faculty_id='', is_online='',
                 course_status_id='', fall_year='', semester_number=''):
        self.url_params = '&'.join(URL_PARAMS_TEMPLATE).format(
            name_ru=name_ru, msu_faculty_id=msu_faculty_id,
            is_online=is_online, course_status_id=course_status_id,
            fall_year=fall_year, semester_number=semester_number
        )

    def courses_list_url(self, page=1):
        return '{}list?{}'.format(BASE_URL, self.url_params + '&page={}'.format(page + 1))

    def course_url(self, course_id):
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
        to course dictionary in place

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
            students = []
            table = page.find('table', {'class': 'table'})
            for row in table.find('tbody').contents:
                # skip empty rows
                if row.string is not None:
                    continue

                student = {key : value.text for key, value in zip(student_keys, row.contents)}
                #student['name'] = student['name'].split()
                student['courses'] = {course['id']}
                students.append(student)

        return students

    def students_course_count(students):
        course_count = {}
        for id, student in students.items():
            try:
                course_count[len(student['courses'])] += 1
            except KeyError:
                course_count[len(student['courses'])] = 1

        return course_count


    def save_to_scv(courses, students, course_labels=[], student_labels=[]):

        with open('students.csv', 'w') as f:
            writer = csv.writer(f, delimiter=';')
            for i, student in enumerate(students.values()):
                # header
                if i == 0:
                    writer.writerow(student_columns.values())
                row = [str(student[key])for key in student_columns if key != 'courses']
                row.append(':'.join([str(course_id) for course_id in student['courses']]))
                writer.writerow(row)

        with open('courses.csv', 'w') as f:
            writer = csv.writer(f, delimiter=';')
            for i, course in enumerate(courses.values()):
                # header
                if i == 0:
                    writer.writerow(course_columns.values())
                writer.writerow([str(course[key]) for key in course_columns])

    def load_from_csv():
        courses = {}
        students = {}
        with open('courses.csv') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader)
            for row in reader:
                course = {key: value for key, value in zip(course_columns.keys(), row)}
                course['id'] = int(course['id'])
                courses[course['id']] = course

        with open('students.csv') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader)
            for row in reader:
                student = {key: value for key, value in zip(student_columns.keys(), row)}
                student['courses'] = set([int(course_id) for course_id in student['courses'].split(':')])
                students[student['name']] = student

        return courses, students

    def load_all(only_from_server=False):
        if not only_from_server:
            try:
                print('Start loading from csv')
                data = load_from_csv()
                print('Done')
                return data
            except FileNotFoundError as e:
                print(e)

        print('Start loading from server')
        courses = get_courses()
        students_dup = []
        for course_id, course in courses.items():
            '''
            if course_id > 520:
                break
            '''
            print('Parsing course {}: {}'.format(course_id, course['name']))
            students_dup.append(parse_course_details_and_students(course))

        # Merge students_dup in one list
        students_dup = [student for course_students in students_dup for student in course_students]

        students = {}
        print('Removing student duplicates')
        # We have to do this shit because we don't have actual student id
        for student in students_dup:
            if student['name'] in students:
                s = students[student['name']]
                s['courses'].add(next(iter(student['courses'])))
            else:
                students[student['name']] = student

        try:
            save_to_scv(courses, students)
            print('Cached to csv')
        except Exception as e:
            print('Failed to save to csv')

        print('Done')
        return courses, students

    def get_keys(d):
        return(next(iter(d.values())).keys())
