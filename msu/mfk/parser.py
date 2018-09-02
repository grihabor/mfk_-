from urllib import request
from bs4 import BeautifulSoup

BASE_URL = 'http://lk.msu.ru/course/'
URL_PARAMS_TEMPLATE = ['CourseSearch[name_ru]={name_ru}',
                       'CourseSearch[msu_faculty_id]={msu_faculty_id}',
                       'CourseSearch[is_online]={is_online}',
                       'CourseSearch[course_status_id]={course_status_id}',
                       'CourseSearch[fall_year]={fall_year}',
                       'CourseSearch[semester_number]={semester_number}']

student_keys = ['name', 'faculty', 'study_mode', 'degree', 'year']
course_keys = ['name', 'faculty', 'online', 'status']


class MFKParser:

    def __init__(self, **kwargs):
        self.url_params = '&'.join(URL_PARAMS_TEMPLATE).format(**kwargs)

    def get_num_pages(self, html):
        page = BeautifulSoup(html, 'lxml')
        numPages = page.find('ul', {'class': 'pagination'}).find_all('li')[-2].text
        return int(numPages)

    def parse_list_page(self, html):
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

    def parse_course_details_and_students(self, course):
        """
        Search for course page using course['id'], add extra information
        to course dictionary in place

        :param course: dictionary
        :return: students -- dictionary
        """
        with request.urlopen(self.course_url(course['id'])) as response:
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

    def courses_list_url(self, page=1):
        return '{}list?{}'.format(BASE_URL, self.url_params + '&page={}'.format(page + 1))

    def course_url(self, course_id):
        return '{}view?id={}'.format(BASE_URL, course_id)
