from pathlib import Path
import sqlite3

from flask import Flask, abort, redirect, render_template, request, send_from_directory, url_for

# Використовуємо шаблони та статичні файли з папки addition
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "DBs" / "points.db"


def fetch_all(query: str, params: tuple = ()) -> list[sqlite3.Row]:
    """Виконує запит та повертає всі результати як словники."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(query, params)
        return cursor.fetchall()


def fetch_one(query: str, params: tuple = ()) -> sqlite3.Row | None:
    rows = fetch_all(query, params)
    return rows[0] if rows else None


def execute(query: str, params: tuple = ()) -> None:
    """Виконує змінюючий запит (INSERT/UPDATE/DELETE)."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(query, params)
        conn.commit()


app = Flask(
    __name__,
    template_folder='addition/templates',
    static_folder='addition/static'
)


@app.after_request
def apply_csp(response):
    """
    Додає CSP-заголовок, який дозволяє завантаження та виконання скриптів
    з поточного домену та inline-скрипти (необхідно для функціональності index.html).
    Зовнішні скрипти з інших доменів заборонені.
    """
    response.headers["Content-Security-Policy"] = "script-src 'self' 'unsafe-inline'"
    return response


@app.route('/')
def root_index():
    # Віддаємо існуючий статичний index.html з кореня проєкту
    return send_from_directory('.', 'index.html')


@app.route('/style.css')
def root_style():
    return send_from_directory('.', 'style.css')


@app.route('/script.js')
def root_script():
    return send_from_directory('.', 'script.js')


@app.route('/images/<path:filename>')
def images(filename: str):
    return send_from_directory('images', filename)


@app.route("/hello/<name>")
def hello(name):
    return render_template("hello.html.j2", name=name)

@app.route("/hello2")
def hello2():
    name = request.args.get("name") or "Гість"
    return render_template("hello.html.j2", name=name)


@app.route("/form", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        name = request.form.get("name", "")
        email = request.form.get("email", "")
        message = request.form.get("message", "")
        return render_template("form.html.j2", submitted=True, name=name, email=email, message=message)
    return render_template("form.html.j2", submitted=False)


@app.route("/grades")
def grades():
    marks = fetch_all(
        """
        SELECT points.id,
               student.name AS student_name,
               course.title AS course_title,
               course.semester,
               points.value
        FROM points
        JOIN student ON student.id = points.id_student
        JOIN course ON course.id = points.id_course
        ORDER BY student.name ASC, course.title ASC
        """
    )
    return render_template("grades.html.j2", grades=marks)


def ects_letter(value: float) -> str:
    """Перетворення числової оцінки у літерну шкалу ECTS."""
    if value >= 90:
        return "A"
    if value >= 82:
        return "B"
    if value >= 74:
        return "C"
    if value >= 64:
        return "D"
    if value >= 60:
        return "E"
    return "FX"


@app.route("/students")
def students():
    students_list = fetch_all(
        "SELECT id, name FROM student ORDER BY name ASC"
    )
    return render_template("students.html.j2", students=students_list)


@app.route("/students/<int:student_id>")
def student_detail(student_id: int):
    student = fetch_one(
        "SELECT id, name FROM student WHERE id = ?",
        (student_id,),
    )
    if student is None:
        abort(404, description="Студента не знайдено")

    grades = fetch_all(
        """
        SELECT course.title AS course_title,
               course.semester,
               points.value
        FROM points
        JOIN course ON course.id = points.id_course
        WHERE points.id_student = ?
        ORDER BY course.title ASC
        """,
        (student_id,),
    )
    return render_template(
        "student_detail.html.j2",
        student=student,
        grades=grades,
    )


@app.route("/subjects")
def subjects():
    subject_list = fetch_all(
        "SELECT id, title, semester FROM course ORDER BY title ASC"
    )
    return render_template("subjects.html.j2", subjects=subject_list)


@app.route("/ratings")
def ratings():
    course_id = request.args.get("course_id", type=int)
    courses = fetch_all("SELECT id, title FROM course ORDER BY title ASC")

    selected_course = None
    rating_rows: list[sqlite3.Row] = []
    if course_id is not None:
        selected_course = fetch_one(
            "SELECT id, title FROM course WHERE id = ?",
            (course_id,),
        )
        if selected_course:
            rating_rows = fetch_all(
                """
                SELECT student.name AS student_name,
                       points.value
                FROM points
                JOIN student ON student.id = points.id_student
                WHERE points.id_course = ?
                ORDER BY points.value DESC, student.name ASC
                """,
                (course_id,),
            )

    return render_template(
        "ratings.html.j2",
        courses=courses,
        selected_course=selected_course,
        ratings=rating_rows,
    )


@app.route("/add-grade", methods=["GET", "POST"])
def add_grade():
    # Отримуємо списки студентів та дисциплін для випадних списків
    students = fetch_all(
        "SELECT id, name FROM student ORDER BY name ASC"
    )
    courses = fetch_all(
        "SELECT id, title FROM course ORDER BY title ASC"
    )

    error: str | None = None

    if request.method == "POST":
        student_id = request.form.get("student_id")
        course_id = request.form.get("course_id")
        value_raw = request.form.get("value")

        # Перевірка заповненості полів
        if not student_id or not course_id or not value_raw:
            error = "Усі поля форми є обов'язковими."
        else:
            try:
                student_id_int = int(student_id)
                course_id_int = int(course_id)
            except ValueError:
                error = "Некоректні ідентифікатори студента або дисципліни."
            else:
                try:
                    value = float(value_raw)
                except ValueError:
                    error = "Значення оцінки має бути числом."
                else:
                    # Додаткова елементарна валідація діапазону
                    if not (0 <= value <= 100):
                        error = "Оцінка повинна бути в діапазоні від 0 до 100."
                    else:
                        value_int = round(value)
                        execute(
                            """
                            INSERT INTO points (id_student, id_course, value)
                            VALUES (?, ?, ?)
                            """,
                            (student_id_int, course_id_int, int(value_int)),
                        )
                        return redirect(url_for("grades"))

    return render_template(
        "add_grade.html.j2",
        students=students,
        courses=courses,
        error=error,
    )


@app.route("/avg-by-subject")
def avg_by_subject():
    """Середній бал по кожній дисципліні."""
    rows = fetch_all(
        """
        SELECT
            course.id AS course_id,
            course.title AS course_title,
            course.semester,
            ROUND(AVG(points.value), 2) AS avg_value,
            COUNT(points.id) AS cnt
        FROM course
        LEFT JOIN points ON points.id_course = course.id
        GROUP BY course.id, course.title, course.semester
        ORDER BY course.title ASC
        """
    )
    return render_template("avg_by_subject.html.j2", rows=rows)


@app.route("/ects-by-subject")
def ects_by_subject():
    """Кількість оцінок за шкалою ECTS по кожній дисципліні."""
    rows = fetch_all(
        """
        SELECT
            course.id AS course_id,
            course.title AS course_title,
            course.semester,
            SUM(CASE WHEN points.value >= 90 THEN 1 ELSE 0 END) AS A_cnt,
            SUM(CASE WHEN points.value >= 82 AND points.value < 90 THEN 1 ELSE 0 END) AS B_cnt,
            SUM(CASE WHEN points.value >= 74 AND points.value < 82 THEN 1 ELSE 0 END) AS C_cnt,
            SUM(CASE WHEN points.value >= 64 AND points.value < 74 THEN 1 ELSE 0 END) AS D_cnt,
            SUM(CASE WHEN points.value >= 60 AND points.value < 64 THEN 1 ELSE 0 END) AS E_cnt,
            SUM(CASE WHEN points.value < 60 THEN 1 ELSE 0 END) AS FX_cnt
        FROM course
        LEFT JOIN points ON points.id_course = course.id
        GROUP BY course.id, course.title, course.semester
        ORDER BY course.title ASC
        """
    )
    return render_template("ects_by_subject.html.j2", rows=rows)


@app.route("/ects-by-student-sem")
def ects_by_student_sem():
    """
    Кількість оцінок за шкалою ECTS по кожному студенту
    для кожного семестру.
    """
    rows = fetch_all(
        """
        SELECT
            student.id AS student_id,
            student.name AS student_name,
            course.semester,
            SUM(CASE WHEN points.value >= 90 THEN 1 ELSE 0 END) AS A_cnt,
            SUM(CASE WHEN points.value >= 82 AND points.value < 90 THEN 1 ELSE 0 END) AS B_cnt,
            SUM(CASE WHEN points.value >= 74 AND points.value < 82 THEN 1 ELSE 0 END) AS C_cnt,
            SUM(CASE WHEN points.value >= 64 AND points.value < 74 THEN 1 ELSE 0 END) AS D_cnt,
            SUM(CASE WHEN points.value >= 60 AND points.value < 64 THEN 1 ELSE 0 END) AS E_cnt,
            SUM(CASE WHEN points.value < 60 THEN 1 ELSE 0 END) AS FX_cnt
        FROM points
        JOIN student ON student.id = points.id_student
        JOIN course ON course.id = points.id_course
        GROUP BY student.id, student.name, course.semester
        ORDER BY student.name ASC, course.semester ASC
        """
    )
    return render_template("ects_by_student_sem.html.j2", rows=rows)


@app.route("/edit-grades", methods=["GET"])
def edit_grades_list():
    """Список усіх оцінок з посиланнями на редагування та видалення."""
    marks = fetch_all(
        """
        SELECT points.id,
               student.name AS student_name,
               course.title AS course_title,
               course.semester,
               points.value
        FROM points
        JOIN student ON student.id = points.id_student
        JOIN course ON course.id = points.id_course
        ORDER BY student.name ASC, course.title ASC
        """
    )
    return render_template("edit_grades_list.html.j2", grades=marks)


@app.route("/edit-grade/<int:grade_id>", methods=["GET", "POST"])
def edit_grade(grade_id: int):
    """Форма редагування існуючої оцінки."""
    grade = fetch_one(
        """
        SELECT points.id,
               points.id_student,
               points.id_course,
               points.value
        FROM points
        WHERE points.id = ?
        """,
        (grade_id,),
    )
    if grade is None:
        abort(404, description="Оцінку не знайдено")

    students = fetch_all(
        "SELECT id, name FROM student ORDER BY name ASC"
    )
    courses = fetch_all(
        "SELECT id, title FROM course ORDER BY title ASC"
    )

    error: str | None = None

    if request.method == "POST":
        student_id = request.form.get("student_id")
        course_id = request.form.get("course_id")
        value_raw = request.form.get("value")

        if not student_id or not course_id or not value_raw:
            error = "Усі поля форми є обов'язковими."
        else:
            try:
                student_id_int = int(student_id)
                course_id_int = int(course_id)
            except ValueError:
                error = "Некоректні ідентифікатори студента або дисципліни."
            else:
                try:
                    value = float(value_raw)
                except ValueError:
                    error = "Значення оцінки має бути числом."
                else:
                    if not (0 <= value <= 100):
                        error = "Оцінка повинна бути в діапазоні від 0 до 100."
                    else:
                        value_int = round(value)
                        execute(
                            """
                            UPDATE points
                            SET id_student = ?, id_course = ?, value = ?
                            WHERE id = ?
                            """,
                            (student_id_int, course_id_int, int(value_int), grade_id),
                        )
                        return redirect(url_for("edit_grades_list"))

    return render_template(
        "edit_grade.html.j2",
        grade=grade,
        students=students,
        courses=courses,
        error=error,
    )


@app.route("/delete-grade/<int:grade_id>", methods=["GET", "POST"])
def delete_grade(grade_id: int):
    """
    Сторінка видалення оцінки з підтвердженням.
    GET — показує підтвердження, POST — виконує видалення.
    """
    grade = fetch_one(
        """
        SELECT points.id,
               points.value,
               student.name AS student_name,
               course.title AS course_title,
               course.semester
        FROM points
        JOIN student ON student.id = points.id_student
        JOIN course ON course.id = points.id_course
        WHERE points.id = ?
        """,
        (grade_id,),
    )
    if grade is None:
        abort(404, description="Оцінку не знайдено")

    if request.method == "POST":
        execute("DELETE FROM points WHERE id = ?", (grade_id,))
        return redirect(url_for("edit_grades_list"))

    return render_template("delete_grade.html.j2", grade=grade)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)


