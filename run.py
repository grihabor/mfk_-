import mfk

courses, students = mfk.load_all(True)
print(mfk.get_keys(courses))
print(mfk.get_keys(students))
