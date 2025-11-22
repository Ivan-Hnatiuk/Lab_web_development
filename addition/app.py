from flask import Flask, render_template, request, redirect, url_for
import re
from datetime import datetime
import os

app = Flask(__name__)

# Директорія для збереження файлів з даними
SUBMISSIONS_DIR = "submissions"

# Створюємо директорію, якщо її немає
if not os.path.exists(SUBMISSIONS_DIR):
    os.makedirs(SUBMISSIONS_DIR)

@app.route("/")
def index():
    return "<h1>Привіт із Flask!</h1>"

@app.route("/hello/<name>")
def hello(name):
    return render_template("hello.html.j2", name=name)

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


def save_submission_to_file(form_data):
    """
    Зберігає дані форми у текстовий файл з динамічною назвою.
    Повертає ім'я створеного файлу.
    """
    # Формуємо назву файлу з поточною датою та часом
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"submission_{timestamp}.txt"
    filepath = os.path.join(SUBMISSIONS_DIR, filename)
    
    # Записуємо дані у форматі ключ: значення
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("Дані форми\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Ім'я: {form_data['name']}\n")
        f.write(f"Електронна адреса: {form_data['email']}\n")
        f.write(f"Вік: {form_data['age']}\n")
        f.write(f"Повідомлення: {form_data['message']}\n")
        f.write("\n" + "=" * 40 + "\n")
        f.write(f"Час надсилання: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return filename


@app.route("/form", methods=["GET", "POST"])
def form():
    errors = {}
    form_data = {
        "name": "",
        "email": "",
        "age": "",
        "message": "",
    }

    if request.method == "POST":
        form_data["name"] = request.form.get("name", "").strip()
        form_data["email"] = request.form.get("email", "").strip()
        form_data["age"] = request.form.get("age", "").strip()
        form_data["message"] = request.form.get("message", "")

        if not form_data["name"]:
            errors["name"] = "Вкажіть ім'я."

        if not form_data["email"]:
            errors["email"] = "Вкажіть електронну адресу."
        elif not EMAIL_REGEX.match(form_data["email"]):
            errors["email"] = "Невірний формат електронної адреси."

        if not form_data["age"]:
            errors["age"] = "Вкажіть вік."
        elif not form_data["age"].isdigit():
            errors["age"] = "Вік може містити лише цифри."

        if not form_data["message"].strip():
            errors["message"] = "Введіть повідомлення."

        # Якщо валідацію пройдено успішно - зберігаємо дані у файл та перенаправляємо
        if not errors:
            # Зберігаємо дані у файл
            filename = save_submission_to_file(form_data)
            
            # Перенаправляємо на сторінку результатів з передачею даних та імені файлу
            return redirect(url_for('result', 
                name=form_data["name"],
                email=form_data["email"],
                age=form_data["age"],
                message=form_data["message"],
                filename=filename))

    return render_template(
        "form.html.j2",
        errors=errors,
        **form_data,
    )


@app.route("/result", methods=["GET"])
def result():
    # Отримуємо параметри з GET-запиту
    result_data = {
        "name": request.args.get("name", ""),
        "email": request.args.get("email", ""),
        "age": request.args.get("age", ""),
        "message": request.args.get("message", ""),
        "filename": request.args.get("filename", ""),
    }
    
    return render_template("result.html.j2", **result_data)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)