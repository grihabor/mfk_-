import csv
from urllib import request
from collections import OrderedDict

from .mfk_parser import MFKParser, BASE_URL

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

        self.parser = MFKParser(**dict(
            name_ru=name_ru, msu_faculty_id=msu_faculty_id,
            is_online=is_online, course_status_id=course_status_id,
            fall_year=fall_year, semester_number=semester_number
        ))

    def get_courses(self):
        courses = []

        html = request.urlopen(BASE_URL + 'list').read()
        num_pages = self.parser.get_num_pages(html)
        for page in range(num_pages):
            with request.urlopen(self.parser.courses_list_url(page)) as response:
                html = response.read()
                courses += self.parser.parse_list_page(html)
        return {course['id']: course for course in courses}

    def students_course_count(self, students):
        course_count = {}
        for id, student in students.items():
            try:
                course_count[len(student['courses'])] += 1
            except KeyError:
                course_count[len(student['courses'])] = 1

        return course_count

    def save_to_scv(self, courses, students, course_labels=[], student_labels=[]):

        with open('students.csv', 'w') as f:
            writer = csv.writer(f, delimiter=';')
            for i, student in enumerate(students.values()):
                # header
                if i == 0:
                    writer.writerow(student_columns.values())
                row = [str(student[key])for key in student_columns if key != 'courses']
                row.append(', '.join([str(course_id) for course_id in student['courses']]))
                writer.writerow(row)

        with open('courses.csv', 'w') as f:
            writer = csv.writer(f, delimiter=';')
            for i, course in enumerate(courses.values()):
                # header
                if i == 0:
                    writer.writerow(course_columns.values())
                writer.writerow([str(course[key]) for key in course_columns])

    def load_from_csv(self):
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

    def load_all(self, only_from_server=False):
        if not only_from_server:
            try:
                print('Start loading from csv')
                data = self.load_from_csv()
                print('Done')
                return data
            except FileNotFoundError as e:
                print(e)

        print('Start loading from server')
        courses = self.get_courses()
        students_dup = []
        for course_id, course in courses.items():
            '''
            if course_id > 520:
                break
            '''
            print('Parsing course {}: {}'.format(course_id, course['name']))
            students_dup.append(self.parser.parse_course_details_and_students(course))

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
            self.save_to_scv(courses, students)
            print('Cached to csv')
        except Exception as e:
            print('Failed to save to csv')

        print('Done')
        return courses, students

    def get_keys(self, d):
        return next(iter(d.values())).keys()
