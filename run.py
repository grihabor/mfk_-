from mfk import MFKManager

mfkman = MFKManager()

courses, students = mfkman.load_all(True)
print(mfkman.get_keys(courses))
print(mfkman.get_keys(students))
