from flask import Flask, render_template, request, send_from_directory

# Використовуємо шаблони та статичні файли з папки addition
app = Flask(
    __name__,
    template_folder='addition/templates',
    static_folder='addition/static'
)


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


@app.route("/form", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        name = request.form.get("name", "")
        email = request.form.get("email", "")
        message = request.form.get("message", "")
        return render_template("form.html.j2", submitted=True, name=name, email=email, message=message)
    return render_template("form.html.j2", submitted=False)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)


