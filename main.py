import os
import form
import random
import json
import lib.common_functions as utils

from mlwdb import databs
from flask_session import Session
from flask import request, Flask, session, redirect, render_template, send_from_directory, flash

SESSION_TYPE = 'filesystem'
app=Flask(__name__)
app.secret_key = 'Df4:Vj Mm`L"iLV#|{"I!RY<2F+)L-wz.sm("&H_,\(1FpG{HJ^lH"E$qsDpz`$Omu,bwi#J\OB7:F:HR*~?Z*9U} Dr]5bHeZ~VrDm7Ro(TQGZaYbNsoT."[&/>>5%Q'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['WTF_CSRF_ENABLED'] = False

sess = Session()
sess.init_app(app)

@app.route("/", methods=["GET"])
def main():
    if 'id' in session:
        return redirect("/index")
    return utils.my_render_template("homepage.html")

@app.route("/login", methods=["POST"])
def login():
    if 'id' in session:
        return redirect("/index")
    worker_id = request.form.get("worker_id", None)
    password = request.form.get("password", None)
    if worker_id is None or password is None:
        return redirect("/")
    password = utils.password_hash(password)
    print(password)
    result = databs().fetch("""
            select student_id as id, name, "students" as type from students where password=%s and student_id=%s and verified=1
            union
            select teacher_id as id, name, "teachers" as type from teachers where password=%s and teacher_id=%s and verified=1
            union
            select worker_id as id, name as name, "administrators" as type from administrators where password=%s and worker_id=%s
            """, [password, worker_id, password, worker_id, password, worker_id])
    if len(result) != 1:
        return redirect("/?error_msg=login failed")

    session['username'] = result[0][1]
    session['id'] = result[0][0]
    session['type'] = result[0][2]

    return redirect("/index")

@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect("/")

@app.route("/index", methods=["GET"])
def index():
    if 'id' not in session:
        return redirect("/")
    return utils.my_render_template("index.html")

url = "127.0.0.1:8080/verify?code=0.501746177926953&worker_id=123456&type=admin"
@app.route("/verify", methods=["GET"])
def verify():
    if 'code' in request.args and 'worker_id' in request.args and 'type' in request.args:
        account=None
        update_sql = None
        if request.args['type'] == "administrators":
            account = databs().fetch('''
                select worker_id as id, vkey as name from administrators where worker_id=%s
            ''', [request.args['worker_id']])
            update_sql = "update administrators set verified=1 where worker_id=%s"
        elif request.args['type'] == "students":
            account = databs().fetch('''
                select student_id as id, vkey from students where student_id=%s
            ''', [request.args['worker_id']])
            update_sql = "update students set verified=1 where student_id=%s"
        elif request.args['type'] == "teachers":
            account = databs().fetch('''
                select teacher_id as id, vkey from teachers where teacher_id=%s
            ''', [request.args['worker_id']])
            update_sql = "update teachers set verified=1 where teacher_id=%s"
        if not len(account) == 0:
            print(account)
            print(account[0][1], request.args['code'])
            if account[0][1] == request.args['code']:
                print("ADASDSAD")
                databs().commit(update_sql, request.args['worker_id'])
    return redirect("/")

@app.route("/profile", methods=["GET"])
def profile_get():
    if 'id' not in session:
        return redirect("/index")
    if session['type'] == 'students':
        profile = databs().fetch("SELECT student_id, name, gender, email, grade FROM students WHERE student_id=%s", session["id"])
        return utils.my_render_template("studentsprofile.html", profile = profile[0])
    elif session['type'] == 'teachers':
        profile = databs().fetch("SELECT teacher_id, name, email FROM teachers WHERE teacher_id=%s", session["id"])
        return utils.my_render_template("teachersprofile.html", profile = profile[0])
    elif session['type'] == 'administrators':
        profile = databs().fetch("SELECT worker_id, name, email FROM administrators WHERE worker_id=%s", session["id"])
        return utils.my_render_template("adminsprofile.html", profile = profile[0])

@app.route("/updatestudentsprofile", methods=["POST"])
def updatestudentsprofile_post():
    if 'id' not in session:
        return redirect("/index")
    submit_form = form.updatestudentsprofile()
    if submit_form.validate_on_submit():
        flash("Profile Updated Successfully")
        student_id = submit_form.student_id.data
        name = submit_form.name.data
        grade = submit_form.grade.data
        gender = submit_form.gender.data
        email = submit_form.email.data
        sql = ('''UPDATE students SET name=%s, grade=%s, gender=%s, email=%s WHERE student_id=%s''')
        val = (name, grade, gender, email, student_id)
        databs().commit(sql, val)
        return redirect("/profile")
    else:
        print(submit_form.name.errors)
        print(submit_form.gender.errors)
        print(submit_form.email.errors)
        return "Input error"

@app.route("/updateteachersprofile", methods=["POST"])
def updateteachersprofile_post():
    if 'id' not in session:
        return redirect("/index")
    submit_form = form.updateteachersprofile()
    if submit_form.validate_on_submit():
        flash("Profile Updated Successfully")
        teacher_id = submit_form.id.data
        name = submit_form.name.data
        email = submit_form.email.data
        sql = ('''UPDATE teachers SET name=%s, email=%s WHERE teacher_id=%s''')
        val = (name, email, teacher_id)
        databs().commit(sql, val)
        return redirect("/profile")
    else:
        print(submit_form.name.errors)
        print(submit_form.email.errors)
        return "Input error"

@app.route("/updateadminsprofile", methods=["POST"])
def updateadminsprofile_post():
    if 'id' not in session:
        return redirect("/index")
    submit_form = form.updateadminsprofile()
    if submit_form.validate_on_submit():
        flash("Profile Updated Successfully")
        worker_id = submit_form.worker_id.data
        name = submit_form.name.data
        email = submit_form.email.data
        sql = ('''UPDATE administrators SET name=%s, email=%s WHERE worker_id=%s''')
        val = (name, email, worker_id)
        databs().commit(sql, val)
        return redirect("/profile")
    else:
        print(submit_form.name.errors)
        print(submit_form.email.errors)
        return "Input error"

@app.route("/studentlist", methods=["GET"])
def studentlist_get():
    if 'id' not in session:
        return redirect("/index")
    students = databs().fetch("SELECT student_id, name, grade, gender, email, reg_time FROM students where state!=1")
    return utils.my_render_template("students.html", students = students)

@app.route("/studentlist", methods=["POST"])
def studentlist_post():
    if 'id' not in session:
        return redirect("/index")
    submit_form = form.studentlist()
    if submit_form.validate_on_submit():
        flash("Student Added Successfully")
        student_id = submit_form.student_id.data
        name = submit_form.name.data
        grade = submit_form.grade.data
        gender = submit_form.gender.data
        email = submit_form.email.data
        reg_time = submit_form.reg_time.data
        sql = ('''INSERT INTO students (student_id, name, grade, gender, email, reg_time) VALUES (%s, %s, %s, %s, %s, %s) ''')
        val = (student_id, name, grade, gender, email, reg_time)
        databs().commit(sql, val)
        return redirect("/studentlist")
    else:
        print(submit_form.student_id.errors)
        print(submit_form.name.errors)
        print(submit_form.grade.errors)
        print(submit_form.gender.errors)
        print(submit_form.email.errors)
        print(submit_form.reg_time.errors)
        return "Input error"

@app.route("/updatestudentlist", methods=["GET"])
def updatestudentlist_get():
    if 'id' not in session:
        return redirect("/index")
    students = databs().fetch("SELECT student_id, name, grade, gender, email, reg_time FROM students where state!=1")
    return utils.my_render_template("students.html", students = students)

@app.route("/updatestudentlist", methods=["POST"])
def updatestudentlist_post():
    if 'id' not in session:
        return redirect("/index")
    submit_form = form.updatestudentlist()
    if submit_form.validate_on_submit():
        flash("Student Updated Successfully")
        student_id = submit_form.student_id.data
        name = submit_form.name.data
        grade = submit_form.grade.data
        gender = submit_form.gender.data
        email = submit_form.email.data
        reg_time = submit_form.reg_time.data
        sql = ('''UPDATE students SET name=%s, grade=%s, gender=%s, email=%s, reg_time=%s WHERE student_id=%s''')
        val = (name, grade, gender, email, reg_time, student_id)
        databs().commit(sql, val)
        return redirect("/studentlist")
    else:
        print(submit_form.student_id.errors)
        print(submit_form.name.errors)
        print(submit_form.grade.errors)
        print(submit_form.gender.errors)
        print(submit_form.email.errors)
        print(submit_form.reg_time.errors)
        return "Input error"

@app.route("/deletestudent/<string:student_id>", methods=["GET", "POST"])
def deletestudent(student_id):
    flash("Student Deleted Successfuly")
    sql = ('''UPDATE students set state=1 WHERE student_id=%s''')
    val = (student_id)
    databs().commit(sql, val)
    return redirect("/studentlist")

@app.route("/teacherlist", methods=["GET"])
def teacherlist_get():
    if 'id' not in session:
        return redirect("/index")
    teachers = databs().fetch("SELECT teacher_id, name, email, reg_time FROM teachers where state!=1")
    return utils.my_render_template("teachers.html", teachers = teachers)

@app.route("/teacherlist", methods=["POST"])
def teacherlist_post():
    if 'id' not in session:
        return redirect("/index")
    submit_form = form.teacherlist()
    if submit_form.validate_on_submit():
        flash("Teacher Added Successfully")
        teacher_id = submit_form.teacher_id.data
        name = submit_form.name.data
        email = submit_form.email.data
        reg_time = submit_form.reg_time.data
        sql = ('''INSERT INTO students (teacher_id, name, email, reg_time) VALUES (%s, %s, %s, %s) ''')
        val = (teacher_id, name, email, reg_time)
        databs().commit(sql, val)
        return redirect("/teacherlist")
    else:
        print(submit_form.teacher_id.errors)
        print(submit_form.name.errors)
        print(submit_form.email.errors)
        print(submit_form.reg_time.errors)
        return "Input error"

@app.route("/updateteacherlist", methods=["GET"])
def updateteacherlist_get():
    if 'id' not in session:
        return redirect("/index")
    teachers = databs().fetch("SELECT teacher_id, name, email, reg_time FROM teachers where state!=1")
    return utils.my_render_template("teachers.html", teachers = teachers)

@app.route("/updateteacherlist", methods=["POST"])
def updateteacherlist_post():
    if 'id' not in session:
        return redirect("/index")
    submit_form = form.updateteacherlist()
    if submit_form.validate_on_submit():
        flash("Teacher Updated Successfully")
        teacher_id = submit_form.teacher_id.data
        name = submit_form.name.data
        email = submit_form.email.data
        reg_time = submit_form.reg_time.data
        sql = ('''UPDATE teachers SET name=%s, email=%s, reg_time=%s WHERE teacher_id=%s''')
        val = (name, email, reg_time, teacher_id)
        databs().commit(sql, val)
        return redirect("/teacherlist")
    else:
        print(submit_form.teacher_id.errors)
        print(submit_form.name.errors)
        print(submit_form.email.errors)
        print(submit_form.reg_time.errors)
        return "Input error"

@app.route("/deleteteacher/<string:teacher_id>", methods=["GET", "POST"])
def deleteteacher(teacher_id):
    flash("Teacher Deleted Successfuly")
    sql = ('''UPDATE teachers set state=1 WHERE teacher_id=%s''')
    val = (teacher_id)
    databs().commit(sql, val)
    return redirect("/teacherlist")

@app.route("/courses", methods=["GET"])
def courses_get():
    if 'id' not in session:
        return redirect("/index")
    coursesname = databs().fetch("SELECT course_id, course_name, course_code, credit, hours FROM courses_code WHERE state!=1")
    return utils.my_render_template("courses.html", courses = coursesname)

@app.route("/courses", methods=["POST"])
def courses_post():
    if 'id' not in session:
        return redirect("/index")
    submit_form = form.courses()
    if submit_form.validate_on_submit():
        flash("Course Added Successfully")
        course_name = submit_form.course_name.data
        course_code = submit_form.course_code.data
        credit = submit_form.credit.data
        hours = submit_form.hours.data
        sql = ('''INSERT INTO courses_code (course_name, course_code, credit, hours) VALUES (%s, %s, %s, %s) ''')
        val = (course_name, course_code, credit, hours)
        databs().commit(sql, val)
        return redirect("/courses")
    else:
        print(submit_form.course_name.errors)
        print(submit_form.course_code.errors)
        print(submit_form.credit.errors)
        print(submit_form.hours.errors)
        return "Input error"

@app.route("/updatecourses", methods=["GET"])
def updatecourses_get():
    if 'id' not in session:
        return redirect("/index")
    coursesname = databs().fetch("SELECT course_id, course_name, course_code, credit, hours FROM courses_code WHERE state!=1")
    return utils.my_render_template("courses.html", courses = coursesname)

@app.route("/updatecourses", methods=["POST"])
def updatecourses_post():
    if 'id' not in session:
        return redirect("/index")
    submit_form = form.updatecourses()
    if submit_form.validate_on_submit():
        flash("Course Updated Successfuly")
        course_id = submit_form.course_id.data
        course_name = submit_form.course_name.data
        course_code = submit_form.course_code.data
        credit = submit_form.credit.data
        hours = submit_form.hours.data
        sql = ('''UPDATE courses_code SET course_name=%s, course_code=%s, credit=%s, hours=%s WHERE course_id=%s''')
        val = (course_name, course_code, credit, hours, course_id)
        databs().commit(sql, val)
        return redirect("/courses")
    else:
        print(submit_form.course_name.errors)
        print(submit_form.course_code.errors)
        print(submit_form.credit.errors)
        print(submit_form.hours.errors)
        return "Input error"

@app.route("/delete/<string:course_id>", methods=["GET", "POST"])
def delete(course_id):
    flash("Course Deleted Successfuly")
    sql = ('''update courses_code set state=1 WHERE course_id=%s''')
    val = (course_id)
    databs().commit(sql, val)
    return redirect("/courses")

@app.route("/courseslist", methods=["GET"])
def courseslist_get():
    if 'id' not in session:
        return redirect("/index")
    courses = databs().fetch("""SELECT serial,
        courses_code.course_id, course_code, course_name, day, time_start, time_end
    FROM
        courses_code
        INNER JOIN
    courses_list ON courses_code.course_id = courses_list.course_id WHERE courses_code.state != 1""")

    return utils.my_render_template("courseslist.html", courses=courses)

@app.route("/courseslist", methods=["POST"])
def courseslist_post():
    if 'id' not in session:
        return redirect("/index")
    submit_form = form.courses_list()
    if submit_form.validate_on_submit():
        flash("Course Inserted Successfuly")
        course_id = submit_form.course_id.data
        teacher_id = submit_form.teacher_id.data
        day = submit_form.day.data
        time_start = submit_form.time_start.data
        time_end = submit_form.time_end.data
        sql = ('''INSERT INTO courses_list (course_id, teacher_id, day, time_start, time_end) VALUES (%s, %s, %s, %s, %s)''')
        val = (course_id, teacher_id, day, time_start, time_end)
        databs().commit(sql, val)
        return redirect("/courseslist")
    else:
        print(submit_form.course_id.errors)
        print(submit_form.teacher_id.errors)
        print(submit_form.day.errors)
        print(submit_form.time_start.errors)
        print(submit_form.time_end.errors)
        return "input error"

@app.route("/updatecourseslist", methods=["GET"])
def updatecourseslist_get():
    if 'id' not in session:
        return redirect("/index")
    courses = databs().fetch("""SELECT 
        serial, courses_code.course_id, teachers.teacher_id, course_code, course_name, teachers.name, day, time_start, time_end
    FROM
        courses_code
        INNER JOIN
    courses_list ON courses_code.course_id = courses_list.course_id
        INNER JOIN
    teachers ON teachers.teacher_id = courses_list.teacher_id where courses_code.state != 1""")
    print(courses)
    teacher = databs().fetch("SELECT teacher_id, name FROM teachers")
    return utils.my_render_template("courseslist.html", courses=courses, teachers=teacher)

@app.route("/updatecourseslist", methods=["POST"])
def updatecourseslist_post():
    if 'id' not in session:
        return redirect("/index")
    submit_form = form.updatecourseslist()
    if submit_form.validate_on_submit():
        flash("Course Information Updated Successfuly!")
        serial = submit_form.serial.data
        course_id = submit_form.course_id.data
        teacher_id = submit_form.teacher_id.data
        day = submit_form.day.data
        time_start = submit_form.time_start.data
        time_end = submit_form.time_end.data
        sql = ('''UPDATE courses_list SET course_id=%s, teacher_id=%s, day=%s, time_start=%s, time_end=%s WHERE serial=%s''')
        val = (course_id, teacher_id, day, time_start, time_end, serial)
        databs().commit(sql, val)
        return redirect("/courseslist")
    else:
        print(submit_form.course_id.errors)
        print(submit_form.teacher_id.errors)
        print(submit_form.day.errors)
        print(submit_form.time_start.errors)
        print(submit_form.time_end.errors)

        return "Input error"

@app.route("/deletecourseslist/<string:serial>", methods=["GET", "POST"])
def deletecourseslist(serial):
    flash("Course Information Deleted Successfuly")
    sql = ('''DELETE FROM courses_list WHERE serial=%s''')
    val = (serial) 
    databs().commit(sql, val)
    return redirect("/courseslist")

@app.route("/studentscourses", methods=["GET"])
def studentscourses_get():
    if 'id' not in session:
        return redirect("/index")
    courses = databs().fetch("""SELECT serial, students.student_id, students.name,
        courses_code.course_id, course_code, course_name,  credit, hours
    FROM
        courses_code
        INNER JOIN
    students_courses ON courses_code.course_id = students_courses.course_id  
        INNER JOIN
    students ON students.student_id = students_courses.student_id WHERE courses_code.state != 1""")
    print(courses)
    students = databs().fetch("SELECT student_id, name FROM students")
    return utils.my_render_template("studentscourses.html", courses=courses, students=students)

@app.route("/studentscourses", methods=["POST"])
def studentscourses_post():
    if 'id' not in session:
        return redirect("/index")
    submit_form = form.studentscourses()
    if submit_form.validate_on_submit():
        flash("Data Added Successfuly")
        student_id = submit_form.student_id.data
        course_id = submit_form.course_id.data
        sql = ('''INSERT INTO students_courses (student_id, course_id) VALUES (%s, %s)''')
        val = (student_id, course_id)
        databs().commit(sql, val)
        return redirect("/studentscourses")
    else:
        print(submit_form.student_id.errors)
        print(submit_form.course_id.errors)
        return "input error"

@app.route("/updatestudentscourses", methods=["GET"])
def updatestudentscourses_get():
    if 'id' not in session:
        return redirect("/index")
    courses = databs().fetch("""SELECT serial, students.student_id, students.name,
        courses_code.course_id, course_code, course_name,  credit, hours
    FROM
        courses_code
        INNER JOIN
    students_courses ON courses_code.course_id = students_courses.course_id  
        INNER JOIN
    students ON students.student_id = students_courses.student_id WHERE courses_code.state != 1""")
    print(courses)
    students = databs().fetch("SELECT student_id, name FROM students")
    return utils.my_render_template("studentscourses.html", courses=courses, students=students)

@app.route("/updatestudentscourses", methods=["POST"])
def updatestudentscourses_post():
    if 'id' not in session:
        return redirect("/index")
    submit_form = form.updatestudentscourses()
    if submit_form.validate_on_submit():
        flash("Data Added Successfuly")
        serial = submit_form.serial.data
        student_id = submit_form.student_id.data
        course_id = submit_form.course_id.data
        sql = ('''UPDATE students_courses SET student_id=%s, course_id=%s WHERE serial=%s''')
        val = (student_id, course_id, serial)
        databs().commit(sql, val)
        return redirect("/studentscourses")
    else:
        print(submit_form.student_id.errors)
        print(submit_form.course_id.errors)
        return "input error"

@app.route("/deletestudentscourses/<string:serial>", methods=["GET", "POST"])
def deletestudentscourses(serial):
    flash("Student's Course Information Deleted Successfuly")
    sql = ('''DELETE FROM students_courses WHERE serial=%s''')
    val = (serial) 
    databs().commit(sql, val)
    return redirect("/studentscourses")

@app.route("/teacherscourses", methods=["GET"])
def teacherscourses_get():
    if 'id' not in session:
        return redirect("/index")
    courses = databs().fetch("""SELECT serial, teachers.teacher_id, teachers.name,
        courses_code.course_id, course_code, course_name,  credit, hours
    FROM
        courses_code
        INNER JOIN
    teachers_courses ON courses_code.course_id = teachers_courses.course_id  
        INNER JOIN
    teachers ON teachers.teacher_id = teachers_courses.teacher_id WHERE courses_code.state != 1""")
    print(courses)
    teachers = databs().fetch("SELECT teacher_id, name FROM teachers")
    return utils.my_render_template("teacherscourses.html", courses=courses, teachers=teachers)

@app.route("/teacherscourses", methods=["POST"])
def teacherscourses_post():
    if 'id' not in session:
        return redirect("/index")
    submit_form = form.teacherscourses()
    if submit_form.validate_on_submit():
        flash("Data Added Successfuly")
        teacher_id = submit_form.teacher_id.data
        course_id = submit_form.course_id.data
        sql = ('''INSERT INTO teachers_courses (teacher_id, course_id) VALUES (%s, %s)''')
        val = (teacher_id, course_id)
        databs().commit(sql, val)
        return redirect("/teacherscourses")
    else:
        print(submit_form.teacher_id.errors)
        print(submit_form.course_id.errors)
        return "input error"

@app.route("/updateteacherscourses", methods=["GET"])
def updateteacherscourses_get():
    if 'id' not in session:
        return redirect("/index")
    courses = databs().fetch("""SELECT serial, teachers.teacher_id, teachers.name,
        courses_code.course_id, course_code, course_name,  credit, hours
    FROM
        courses_code
        INNER JOIN
    teachers_courses ON courses_code.course_id = teachers_courses.course_id  
        INNER JOIN
    teachers ON teachers.teacher_id = teachers_courses.teacher_id WHERE courses_code.state != 1""")
    print(courses)
    teachers = databs().fetch("SELECT teacher_id, name FROM teachers")
    return utils.my_render_template("teacherscourses.html", courses=courses, teachers=teachers)

@app.route("/updateteacherscourses", methods=["POST"])
def updateteacherscourses_post():
    if 'id' not in session:
        return redirect("/index")
    submit_form = form.updateteacherscourses()
    if submit_form.validate_on_submit():
        flash("Data Added Successfuly")
        serial = submit_form.serial.data
        teacher_id = submit_form.teacher_id.data
        course_id = submit_form.course_id.data
        sql = ('''UPDATE teachers_courses SET teacher_id=%s, course_id=%s WHERE serial=%s''')
        val = (teacher_id, course_id, serial)
        databs().commit(sql, val)
        return redirect("/teacherscourses")
    else:
        print(submit_form.teacher_id.errors)
        print(submit_form.course_id.errors)
        return "input error"

@app.route("/deleteteacherscourses/<string:serial>", methods=["GET", "POST"])
def deleteteacherscourses(serial):
    flash("Teachers's Course Information Deleted Successfuly")
    sql = ('''DELETE FROM teachers_courses WHERE serial=%s''')
    val = (serial) 
    databs().commit(sql, val)
    return redirect("/teacherscourses")

@app.route("/monitoringpage", methods=["GET"])
def monitoringpage_get():
    if 'id' not in session:
        return redirect("/index")
    monitoring = databs().fetch("SELECT student_id, course_code,time_arrive FROM students_monitoring where id")
    return utils.my_render_template("monitoringpage.html", monitoring = monitoring)

@app.route("/register", methods=["GET"])
def register_get():
    if 'id' in session:
        return redirect("/index")
    return utils.my_render_template("register.html")

@app.route("/register", methods=["POST"])
def register_post():
    if 'id' in session:
        return redirect("/index")
    submit_form = form.regist_page()
    if submit_form.validate_on_submit():
        flash("Account is successfuly registered, please check your email to verify your account!")
        name = submit_form.name.data
        worker_id = submit_form.worker_id.data
        email = submit_form.email.data
        password = submit_form.password.data
        account_type = submit_form.account_type.data
        if account_type == "students":
            field = "(`name`, `student_id`, `email`, `password`, `vkey`, `gender`, `reg_time`, `grade`, `file`, `verified`)"
            value = "(%s, %s, %s, %s, %s, 'Unknown', NOW(), 'Not Specified', 'Not Uploaded Yet', '0')"
        elif account_type == "teachers":
            field = "(`name`, `teacher_id`, `email`, `password`, `vkey`, `dept`, `reg_time`, `activated`)"
            value = "(%s, %s, %s, %s, %s, 'Unknown', NOW(), '0')"
        elif account_type == "administrators":
            field="(`name`, `worker_id`, `email`, `password`, `vkey`, `verified`)"
            value = "(%s, %s, %s, %s, %s, '0')"
        vkey = utils.password_hash(str(random.random()))
        utils.send_email(email, "verify your account",
                "127.0.0.1:8080/verify?code=%s&worker_id=%s&type=%s" % (vkey, worker_id, account_type))
        sql = "INSERT INTO `%s` %s VALUES %s;" % (account_type, field, value)
        print(sql)
        databs().commit(sql, [name, worker_id, email, utils.password_hash(password), vkey])
        return redirect('/')
    else:
        print(submit_form.name.errors)
        print(submit_form.worker_id.errors)
        print(submit_form.email.errors)
        print(submit_form.password.errors)
        print(submit_form.errors.items())
        return "input error"

@app.route("/assets/img/<path:path>", methods=["GET"])
def send_img(path):
    return send_from_directory("./assets/img", path)

@app.route("/assets/js/<path:path>", methods=["GET"])
def send_js(path):
    return send_from_directory("./assets/js", path)

@app.route("/assets/css/<path:path>", methods=["GET"])
def send_css(path):
    return send_from_directory("./assets/css", path)

app.run(port=8080, debug=True)
