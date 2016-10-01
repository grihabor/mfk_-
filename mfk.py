import urllib.request
from html.parser import HTMLParser
from collections import namedtuple

Course = namedtuple('Course', ['name', 'data_key', 'faculty', 'online_course', 'status'])
Student = namedtuple('Student', ['name', 'faculty', 'study_mode', 'degree', 'year'])

url = 'http://new.mfk.msu.ru'
courses = []
courses_counter = 1
faculty_students = []
current_course_students = []
max_students = -1

class Parser(HTMLParser):

    def __init__(self):
        super(Parser, self).__init__()
        self.counter = 0
        self.stop = False
        self.mute = True

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if not 'class' in attrs:
            return

        save_class = True
        if attrs['class'] == 'summary':
            self.counter = 4
        elif attrs['class'] == 'pointer':
            self.counter = 4
            self.data_key = attrs['data-key']
        elif attrs['class'] == 'grid-view':
            self.counter = 5
            self.skip = 9
        elif attrs['class'] == 'empty':
            self.skip = 0
            self.counter = 0
        elif attrs['class'] == 'well':
            self.counter = 2
        else:
            save_class = False

        if save_class:
            self.attrs_class = attrs['class']
            
        if not self.mute:
            print("START\t:", tag)
            print('attrs : {}'.format(dict(attrs)))


    def handle_endtag(self, tag):
        if not self.mute:
            print("END\t:", tag)

    def handle_data(self, data):
        if not self.mute:
            print("DATA\t:", data)
        if self.counter == 0:
            return

        if self.attrs_class == 'pointer':
            if self.counter == 4:
                self.name = data
            elif self.counter == 3:
                self.faculty = data
            elif self.counter == 2:
                self.online_course = data
            elif self.counter == 1:
                self.status = data
                courses.append(Course(self.name, 
                                self.data_key,
                                self.faculty, 
                                self.online_course, 
                                self.status))
        elif self.attrs_class == 'well':
            if data.strip() == '':
                return
            if self.counter == 2:   
                if data.split()[0].strip() == 'Записалось':
                    self.counter -= 1
                    return    
                return
            elif self.counter == 1: 
                global max_students
                max_students = data.split('/')[1].strip()   
        elif self.attrs_class == 'summary':
            if self.counter == 4:
                pass
            elif self.counter == 3:
                self.course_from, self.course_to = data.strip().split('-')
            elif self.counter == 2:
                pass
            elif self.counter == 1:
                global courses_counter
                courses_counter = int(data.strip())
        elif self.attrs_class == 'grid-view':
            if self.skip > 0:
                self.skip -= 1
                return
            if self.counter == 5:
                if data.strip() == '':
                    self.counter = 0
                    self.skip = 0
                    return
                self.name = data
            elif self.counter == 4:
                self.faculty = data
            elif self.counter == 3:
                self.study_mode = data
            elif self.counter == 2:
                self.degree = data
            elif self.counter == 1:
                self.year = data
                current_course_students.append(Student(self.name,
                                                self.faculty,
                                                self.study_mode,
                                                self.degree,
                                                self.year))
                self.counter = 5
                self.skip = 1
                return
        self.counter -= 1

#load data about the courses
page = 1
parser = Parser()
while len(courses) < courses_counter:

    with urllib.request.urlopen('{}/course/list?page={}'.format(url, page)) as response:
        html = str(response.read().decode('utf-8'))

    parser.feed(html)
    '''
    for course in courses:
        print(course)

    print(len(courses), courses_counter)    
    '''
    page += 1

#load data about people
parser.stop = True
for course in courses:
    with urllib.request.urlopen('{}/course/view?id={}'.format(url, course.data_key)) as response:
        html = str(response.read().decode('utf-8'))

    parser.feed(html)

    '''
    for student in current_course_students:
        print(student) 
    '''
    
    #print('{}\n{}\n'.format(len(current_course_students), course))
    
    faculty_students_item = {}

    faculty_students_item['max_students'] = max_students
    for student in current_course_students:
        if student.faculty in faculty_students_item:
            faculty_students_item[student.faculty].append(student)
        else:
            faculty_students_item[student.faculty] = [student]
    faculty_students.append(faculty_students_item)
    current_course_students = []

data_for_output = []

persons_to_find = ['Бобрик', 'Алиева']
print('Searching for:', persons_to_find)

for course, faculty_students_item in zip(courses, faculty_students):
    num_students = sum([len(value) for key, value in faculty_students_item.items() if key != 'max_students'])
    line = [course.name, 
            str(num_students),
            str(faculty_students_item['max_students']),
            course.online_course,
            '{}/course/view?id={}'.format(url, course.data_key)]
    data_for_output.append(line)
    '''
    for faculty, students in sorted(faculty_students_item.items()):
        print('\t', faculty, len(students))
    '''

    #find persons    
    for faculty, students in faculty_students_item.items():
        if faculty == 'max_students':
            continue
        for student in students:
            if student.name.split()[0] in persons_to_find:
                print(student)
                print(course)
                print()
    

data_for_output = sorted(data_for_output, key = lambda data: int(data[1]), reverse = True)
with open('mfk.csv', 'w') as ofile:
    ofile.write(';'.join(['Курс', 'Записалось', 'Всего мест', 'Онлайн', 'Ссылка']) + '\n')
    for line in data_for_output:
        ofile.write(';'.join(line) + '\n')




















