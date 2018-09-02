from msu.mfk import MFKManager

mfkman = MFKManager(fall_year=2016, semester_number=2)

courses, students = mfkman.load_all(True)
print(mfkman.get_keys(courses))
print(mfkman.get_keys(students))
