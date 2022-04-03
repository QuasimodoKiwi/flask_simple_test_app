from flask import Flask, render_template, request, flash, redirect, session
from sqlalchemy import Column, Integer, String, Numeric, create_engine, text
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = 'super secret key'
conn_str = "mysql://root:iit123@localhost/final"
engine = create_engine(conn_str, echo=True)
conn = engine.connect()


def login_required(next_func):
    def inner_func(*args):
        if "user" in session:
            return next_func(*args)
        # TODO error message
        return redirect("/login")

    return inner_func


@app.route('/')
def hello_world():  # put application's code here
    if 'user' in session:
        print(session['user'])
    return render_template("homepage.html")


@app.route('/register', methods=['GET', 'POST'])
def register():  # put application's code here
    message = ""

    if request.method == 'POST':
        user = conn.execute(
            text('select * from user where username = :username'), request.form).one_or_none()

        if user is not None:
            message = "User already exists!"
        else:
            input_data = request.form.to_dict()
            input_data['password'] = generate_password_hash(input_data['password'])
            conn.execute(
                text('insert into user values(:username, :first_name, :last_name, :password, :account_type)'),
                input_data
            )
            message = "Success"
        return render_template("account/register.html", message=message)
    return render_template("account/register.html")


@app.route('/login', methods=['GET', 'POST'])
def login():  # put application's code here
    message = ""

    if request.method == 'POST':
        user = conn.execute(
            text('select * from user where username = :username'), request.form).one_or_none()

        if user is None:
            message = "User does not exist!"
        else:
            if check_password_hash(user['password'], request.form['password']):
                message = "Success!"
                session['user'] = {
                    "username": user['username'],
                    "name": user['first_name'] + " " + user['last_name'],
                    "account_type": user['account_type']
                }
            else:
                message = "Wrong password!"
        return render_template("account/login.html", message=message)
    return render_template("account/login.html")


@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")


@app.route('/accounts', methods=['GET'])
def get_accounts():  # put application's code here
    account_type = request.args.get('type')
    if account_type:
        accounts = conn.execute(
            text(f'select * from user where account_type = "{account_type}"')
        ).all()
    else:
        accounts = conn.execute(
            text('select * from user')
        ).all()
    return render_template("account/accounts.html", accounts=accounts)


@app.route('/create_tests', methods=['GET', 'POST'])
def create_tests():
    message = ""
    if request.method == 'POST':
        conn.execute(
            text('insert into tests(creator, q1, q2, q3) values(:creator, :q1, :q2, :q3)'),
            request.form
        )
        message = "Success"

    accounts = conn.execute(
        text(f'select * from user where account_type = "teacher"')
    ).all()
    return render_template("tests/create_tests.html", teachers=accounts, message=message)


@app.route('/tests')
def get_tests():
    tests = conn.execute(
        text(f'select * from tests')
    ).all()
    return render_template("tests/test.html", tests=tests)


@app.route('/delete_test/<id>')
def delete_tests(id):
    conn.execute(
        text(f'delete from tests where id = "{id}"')
    )
    return redirect("/tests")


@app.route('/edit_test/<id>', methods=['GET'])
def edit_tests(id):
    message = ""
    accounts = conn.execute(
        text(f'select * from user where account_type = "teacher"')
    ).all()

    test = conn.execute(
        text(f'select * from tests where id = {id}')
    ).one()
    return render_template("tests/edit_test.html", teachers=accounts, test=test, message=message)


@app.route('/edit_test/<id>', methods=['POST'])
def edit_tests_post(id):
    message = ""
    conn.execute(
        text(f'update tests set creator = :creator, q1 = :q1, q2 = :q2, q3 = :q3 where id = "{id}"'),
        request.form
    )
    message = "Success"

    return redirect("/tests")


@app.route('/take_test', methods=['GET', 'POST'])
@login_required
def select_tests():
    tests = conn.execute(
        text(f'select * from tests')
    ).all()
    return render_template("tests/select_test.html", tests=tests)


@app.route('/take_test/<id>', methods=['GET', 'POST'])
def take_test(id):
    message = ""
    if request.method == 'POST':
        print(request.form)
        data = {
            "test_id": id,
            "student_id": request.form['student_id'],
            "a1": request.form['a1'],
            "a2": request.form['a2'],
            "a3": request.form['a3'],
        }

        try:
            conn.execute(
                text(
                    "insert into answers(test_id, student_id, a1, a2, a3) values(:test_id, :student_id, :a1, :a2, :a3)"),
                data
            )
            message = "Your answer has been recorded"
        except Exception:
            message = "You can't take the test twice"  # sth went wrong

    test = conn.execute(
        text(f'select * from tests where id = "{id}"')
    ).one()

    students = conn.execute(
        text(f'select * from user where account_type = "student"')
    ).all()
    return render_template("tests/take_test.html", test=test, students=students, message=message)


@app.route('/responses/<id>', methods=['GET'])
@app.route('/responses/<id>/<message>', methods=['GET'])
def responses(id, message=""):
    responses = conn.execute(
        text(f'select * from answers join tests on answers.test_id = tests.id  where test_id = "{id}"')
    ).all()

    teachers = conn.execute(
        text(f'select * from user where account_type="teacher"')
    ).all()

    return render_template("misc/responses.html", responses=responses, teachers=teachers, message=message)


@app.route('/mark/<id>/<student_id>', methods=['POST'])
def mark(id, student_id):
    conn.execute(text(
        f"update answers set marks={request.form['marks']}, marked_by='{request.form['marked_by']}' where test_id={id} and student_id='{student_id}'"
    ))
    message = "Mark updated successfully"

    return redirect(f"/responses/{id}/{message}")


if __name__ == '__main__':
    app.run(debug=True)
