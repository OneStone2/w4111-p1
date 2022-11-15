#!/usr/bin/env python3

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from sqlalchemy import exc
from flask import Flask, request, render_template, g, redirect, Response, abort, session
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key="eevee is cool"


# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "jo2708"
DB_PASSWORD = "I won't tell you my password wtf"

DB_SERVER = "w4111project1part2db.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
    id serial,
    name text
    );""")
engine.execute("""INSERT INTO test(name) VALUES ('gracehopper123'), ('alan turing'), ('ada lovelace');""")

@app.before_request
def before_request():
    """
    This function is run at the beginning of every web request 
    (every time you enter an address in the web browser).
    We use it to setup a database connection that can be used throughout the request

    The variable g is globally accessible
    """
    try:
        g.conn = engine.connect()
        user_id = session.get("user_id")

        if user_id is None:
            g.user = None
        else:
            cmd = "SELECT * FROM Account WHERE email = (:email)"
            g.user = g.conn.execute(text(cmd), email=user_id).fetchone()
    except:
        print("uh oh, problem connecting to database")
        import traceback; traceback.print_exc()
        g.conn = None

@app.teardown_request
def teardown_request(exception):
    """
    At the end of the web request, this makes sure to close the database connection.
    If you don't the database could run out of memory!
    """
    try:
        g.conn.close()
    except Exception as e:
        pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
    """
    request is a special object that Flask provides to access web request information:

    request.method:   "GET" or "POST"
    request.form:     if the browser submitted a form, this contains the data in the form
    request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

    See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
    """

    # DEBUG: this is debugging code to see what request looks like
    print(request.args)


    #
    # example of a database query
    #
    cursor = g.conn.execute("SELECT name FROM test")
    names = []
    for result in cursor:
        names.append(result['name'])  # can also be accessed using result[0]
    cursor.close()

    #
    # Flask uses Jinja templates, which is an extension to HTML where you can
    # pass data to a template and dynamically generate HTML based on the data
    # (you can think of it as simple PHP)
    # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
    #
    # You can see an example template in templates/index.html
    #
    # context are the variables that are passed to the template.
    # for example, "data" key in the context variable defined below will be 
    # accessible as a variable in index.html:
    #
    #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
    #     <div>{{data}}</div>
    #     
    #     # creates a <div> tag for each element in data
    #     # will print: 
    #     #
    #     #   <div>grace hopper</div>
    #     #   <div>alan turing</div>
    #     #   <div>ada lovelace</div>
    #     #
    #     {% for n in data %}
    #     <div>{{n}}</div>
    #     {% endfor %}
    #
    context = dict(data = names)


    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/index.html
    #
    return redirect("recipe_list")

#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
@app.route('/another')
def another():
    return render_template("anotherfile.html")

@app.route('/profile', methods=['GET'])
def profile():
    print(request)
    username = request.args.get('name')
    print(username)
    if username is None:
        if g.user is None:
            abort(400)
        username = g.user["username"]
   
    cmd = 'SELECT * FROM Account WHERE username = (:username)'
    user = g.conn.execute(text(cmd), username=username).fetchone()
    if user is None:
        abort(404)
    
    cmd = 'SELECT R.recipe_id, R.name FROM Recipe R, Writes W, Account A WHERE W.email = A.email AND A.username = (:username) AND R.recipe_id = W.recipe_id'
    cursor = g.conn.execute(text(cmd), username=username)    
    recipe_list = []
    for result in cursor:
        recipe_list.append(result)
    cursor.close()
        
    return render_template("profile.html", username=username, recipe_list=recipe_list, authorized=(g.user is not None and username == g.user["username"]))

@app.route('/recipe_list', methods=['GET'])
def recipe_list():
    print(request)
    u_id = request.args.get('name')
    if u_id is None:
        cmd = 'SELECT recipe_id, name FROM Recipe'
        cursor = g.conn.execute(text(cmd))
        recipe_list = []
        for result in cursor:
            recipe_list.append(result)
    else:
        if g.user is None or u_id != g.user['username']:
            abort(403)
        cmd = 'SELECT R.recipe_id, R.name FROM Recipe R WHERE NOT EXISTS ( SELECT U.ingr_id FROM Uses U WHERE U.recipe_id = R.recipe_id AND NOT EXISTS ( SELECT IV.ingr_id FROM Inventory IV WHERE IV.email = (:email) AND IV.amount >= U.amount AND IV.ingr_id = U.ingr_id ) )'
        cursor = g.conn.execute(text(cmd), email=g.user['email'])
        recipe_list = []
        for result in cursor:
            recipe_list.append(result)
        cursor.close()
            
    return render_template("recipe_list.html", recipe_list=recipe_list)

@app.route('/edit_inventory', methods=['POST'])
def edit_inventory():
    print(request)
    if g.user is None:
        abort(401)
    print(request.form)
    for i_id in request.form:
        try:
            value = request.form[i_id]
            if value == "Delete":
                cmd = 'DELETE FROM Inventory WHERE email = (:email) AND ingr_id = (:i_id)'
                cursor = g.conn.execute(text(cmd), i_id=i_id, email=g.user["email"])
            elif value == "Edit":
                cmd = 'UPDATE Inventory SET amount = (:amount) WHERE email = (:email) AND ingr_id = (:i_id)'
                if "amount" in request.form:
                    cursor = g.conn.execute(text(cmd), i_id=i_id, email=g.user["email"], amount=request.form["amount"])
            elif value == "Add":
                cmd = 'SELECT ingr_id FROM Ingredient WHERE name = (:i_id)'
                if "ingr" in request.form:
                    result = g.conn.execute(text(cmd), i_id=request.form["ingr"]).fetchone()
                    if result is not None:
                        cmd = 'INSERT INTO Inventory(email, ingr_id, amount) VALUES ((:email), (:i_id), 1);'
                        cursor = g.conn.execute(text(cmd), i_id=result[0], email=g.user["email"])
        except exc.IntegrityError:
            pass
            
    return redirect("inventory")

@app.route('/edit_recipe_ingr', methods=['POST'])
def edit_recipe_ingr():
    print(request)
    if g.user is None:
        abort(401)
    print(request.form)
    r_id = session["last_recipe"]
    cmd = 'SELECT * FROM Writes WHERE recipe_id = (:r_id) AND email = (:email)'
    result = g.conn.execute(text(cmd), email=g.user["email"], r_id=r_id).fetchone()
    if result is None:
        abort(403)
    for i_id in request.form:
        try:
            value = request.form[i_id]
            if value == "Delete":
                cmd = 'DELETE FROM Uses WHERE recipe_id = (:r_id) AND ingr_id = (:i_id)'
                cursor = g.conn.execute(text(cmd), i_id=i_id, r_id=r_id)
            elif value == "Edit":
                cmd = 'UPDATE Uses SET amount = (:amount), info = (:info) WHERE recipe_id = (:r_id) AND ingr_id = (:i_id)'
                if "amount" in request.form:
                    cursor = g.conn.execute(text(cmd), i_id=i_id, r_id=r_id, amount=request.form["amount"], info=(None if request.form["info"] == "" else request.form["info"]))
            elif value == "Add":
                cmd = 'SELECT ingr_id FROM Ingredient WHERE name = (:i_id)'
                if "ingr" in request.form:
                    result = g.conn.execute(text(cmd), i_id=request.form["ingr"]).fetchone()
                    if result is not None:
                        cmd = 'INSERT INTO Uses(ingr_id, recipe_id, amount, info) VALUES ((:i_id), (:r_id), 1, NULL);'
                        cursor = g.conn.execute(text(cmd), i_id=result[0], r_id=r_id)
        except exc.IntegrityError:
            pass
            
    return redirect("edit_recipe")

@app.route('/edit_recipe_instr', methods=['POST'])
def edit_recipe_instr():
    print(request)
    if g.user is None:
        abort(401)
    print(request.form)
    r_id = session["last_recipe"]
    cmd = 'SELECT * FROM Writes WHERE recipe_id = (:r_id) AND email = (:email)'
    result = g.conn.execute(text(cmd), email=g.user["email"], r_id=r_id).fetchone()
    if result is None:
        abort(403)
    for i_id in request.form:
        try:
            value = request.form[i_id]
            if value == "Edit":
                cmd = 'UPDATE Instruction_Step SET text = (:text) WHERE recipe_id = (:r_id) AND instr_id = (:i_id)'
                if "text" in request.form:
                    cursor = g.conn.execute(text(cmd), i_id=i_id, r_id=r_id, text=request.form["text"])
        except exc.IntegrityError:
            pass
            
    return redirect("edit_recipe")

@app.route('/edit_recipe_attr', methods=['POST'])
def edit_recipe_attr():
    print(request)
    if g.user is None:
        abort(401)
    print(request.form)
    r_id = session["last_recipe"]
    cmd = 'SELECT * FROM Writes WHERE recipe_id = (:r_id) AND email = (:email)'
    result = g.conn.execute(text(cmd), email=g.user["email"], r_id=r_id).fetchone()
    if result is None:
        abort(403)
    
    if "name" in request.form:
        try:
            cmd = 'UPDATE Recipe SET name = (:name) WHERE recipe_id = (:r_id)'
            cursor = g.conn.execute(text(cmd), r_id=r_id, name=request.form["name"])
        except exc.IntegrityError:
            pass
    
    if "servings" in request.form:
        try:
            cmd = 'UPDATE Recipe SET servings = (:servings) WHERE recipe_id = (:r_id)'
            cursor = g.conn.execute(text(cmd), r_id=r_id, servings=request.form["servings"])
        except exc.IntegrityError:
            pass
    
    if "time" in request.form:
        try:
            cmd = 'UPDATE Recipe SET time = (:time) WHERE recipe_id = (:r_id)'
            cursor = g.conn.execute(text(cmd), r_id=r_id, time=request.form["time"])
        except exc.IntegrityError:
            pass
            
    return redirect("edit_recipe")

@app.route('/add_step', methods=['POST'])
def add_step():
    print(request)
    if g.user is None:
        abort(401)
    print(request.form)
    r_id = session["last_recipe"]
    cmd = "SELECT MAX(position)+1 FROM Instruction_Step WHERE recipe_id = (:r_id)";
    result = g.conn.execute(text(cmd), r_id=r_id).fetchone()
    cmd = "INSERT INTO Instruction_Step(recipe_id, text, position) VALUES ((:r_id), '', (:num));"
    g.conn.execute(text(cmd), r_id=r_id, num=1 if result[0] is None else result[0])
    return redirect("edit_recipe")

@app.route('/remove_step', methods=['POST'])
def remove_step():
    print(request)
    if g.user is None:
        abort(401)
    print(request.form)
    r_id = session["last_recipe"]
    cmd = 'SELECT * FROM Writes WHERE recipe_id = (:r_id) AND email = (:email)'
    result = g.conn.execute(text(cmd), email=g.user["email"], r_id=r_id).fetchone()
    if result is None:
        abort(403)
    r_id = session["last_recipe"]
    cmd = "DELETE FROM Instruction_Step WHERE position = (SELECT MAX(position) FROM Instruction_Step WHERE recipe_id = (:r_id)) AND recipe_id = (:r_id);"
    g.conn.execute(text(cmd), r_id=r_id)
    return redirect("edit_recipe")

@app.route('/delete_recipe', methods=['POST'])
def delete_recipe():
    print(request)
    if g.user is None:
        abort(401)
    print(request.form)
    r_id = session["last_recipe"]
    cmd = 'SELECT * FROM Writes WHERE recipe_id = (:r_id) AND email = (:email)'
    result = g.conn.execute(text(cmd), email=g.user["email"], r_id=r_id).fetchone()
    if result is None:
        abort(403)
    r_id = session["last_recipe"]
    cmd = "DELETE FROM Uses WHERE recipe_id = (:r_id)"
    g.conn.execute(text(cmd), r_id=r_id)
    cmd = "DELETE FROM Writes WHERE recipe_id = (:r_id)"
    g.conn.execute(text(cmd), r_id=r_id)
    cmd = "DELETE FROM Recipe WHERE recipe_id = (:r_id)"
    g.conn.execute(text(cmd), r_id=r_id)
    return redirect("profile")

@app.route('/create_recipe', methods=['POST'])
def create_recipe():
    if g.user is None:
        abort(401)
    u_id = g.user["email"]
    cmd = "INSERT INTO Recipe(name, servings, time) VALUES ('Untitled recipe', 1, 30);"
    g.conn.execute(text(cmd))
    cmd = "SELECT R.recipe_id FROM Recipe R WHERE R.recipe_id NOT IN (SELECT W.recipe_id FROM Writes W)";
    r_id = g.conn.execute(text(cmd)).fetchone()[0]
    cmd = 'INSERT INTO Writes(email, recipe_id) VALUES ((:email), (:r_id));'
    g.conn.execute(text(cmd), email=g.user["email"], r_id=r_id)
    return redirect("profile")

@app.route('/inventory', methods=['GET'])
def inventory():
    print(request)
    u_id = g.user['email']
    if u_id is None:
        abort(401)
    else:
        cmd = 'SELECT V.amount, G.unit, G.name, G.ingr_id FROM Inventory V, Ingredient G WHERE V.email = (:u_id) AND V.ingr_id = G.ingr_id'
        cursor = g.conn.execute(text(cmd), u_id=u_id)
        ingr_list = []
        for result in cursor:
            ingr_list.append([result[0], '' if result[1] is None else result[1], result[2], result[3]])
        cursor.close()
        ingr_list.sort(key=lambda x:x[2])
        
        cmd = 'SELECT G.name FROM Ingredient G WHERE G.name NOT IN (SELECT G2.name FROM Inventory V, Ingredient G2 WHERE V.ingr_id = G2.ingr_id AND V.email = (:u_id))'
        cursor = g.conn.execute(text(cmd), u_id=u_id)
        ingr_types = []
        for result in cursor:
            ingr_types.append(result[0])
        cursor.close()
            
    return render_template("inventory.html", ingr_list=ingr_list, ingr_types=ingr_types)

@app.route('/recipe', methods=['GET'])
def recipe():
    print(request)
    r_id = request.args.get('id')
    if r_id is None or not r_id.isdigit():
        abort(400)
    r_id = int(r_id)
    cmd = 'SELECT R.name, R.servings, R.time, A.username, R.recipe_id FROM Recipe R, Account A, Writes W WHERE R.recipe_id = (:r_id) AND R.recipe_id = W.recipe_id AND A.email = W.email'
    recipe = g.conn.execute(text(cmd), r_id = r_id).fetchone()
    print(recipe)
    
    if recipe is None:
        abort(404)
    
    cmd = 'SELECT I.name, U.amount, I.unit, U.info FROM Uses U, Ingredient I WHERE U.recipe_id = (:r_id) AND U.ingr_id = I.ingr_id'
    cursor = g.conn.execute(text(cmd), r_id = r_id)
    ingr_list = []
    for result in cursor:
        ingr_list.append([result[0], result[1], '' if result[2] is None else result[2], '' if result[3] is None else result[3]])
    cursor.close()
    print(ingr_list)
    ingr_list.sort(key=lambda x:x[0])
    
    cmd = 'SELECT * FROM Instruction_Step WHERE recipe_id = (:r_id)'
    cursor = g.conn.execute(text(cmd), r_id = r_id)
    instr_list = []
    for result in cursor:
        instr_list.append([result['position'], result['text']])
    cursor.close()
    print(instr_list)
      
    instr_list.sort()
    
    return render_template('recipe.html', recipe=recipe, ingr_list=ingr_list, instr_list=instr_list, authorized=(g.user is not None and recipe[3]==g.user["username"]))

@app.route('/edit_recipe', methods=['GET'])
def edit_recipe():
    print(request)
    r_id = ([x for x in request.args]+[None])[0]
    u_id = g.user['email']
    if r_id is None:
        if "last_recipe" not in session:
            abort(400)
        r_id = session["last_recipe"]
            
    if not r_id.isdigit():
        abort(400)
    r_id = int(r_id)
    
    if g.user is None:
        abort(403)
    
    cmd = 'SELECT R.name, R.servings, R.time, A.username FROM Recipe R, Account A, Writes W WHERE R.recipe_id = (:r_id) AND R.recipe_id = W.recipe_id AND A.email = W.email'
    recipe = g.conn.execute(text(cmd), r_id = r_id).fetchone()
    print(recipe)
    
    if recipe is None:
        abort(404)
    
    cmd = 'SELECT * FROM Writes W WHERE W.email = (:email) AND W.recipe_id = (:r_id)'
    result = g.conn.execute(text(cmd), r_id=r_id, email=g.user["email"]).fetchone()
    if result is None:
        abort(403)
    
    session["last_recipe"] = str(r_id)
    
    cmd = 'SELECT U.amount, G.unit, G.name, U.info, G.ingr_id FROM Uses U, Ingredient G WHERE U.recipe_id = (:r_id) AND U.ingr_id = G.ingr_id'
    cursor = g.conn.execute(text(cmd), r_id=r_id)
    ingr_list = []
    for result in cursor:
        ingr_list.append([result[0], '' if result[1] is None else result[1], result[2], '' if result[3] is None else result[3], result[4]])
    cursor.close()
    ingr_list.sort(key=lambda x:x[2])
    
    cmd = 'SELECT * FROM Instruction_Step WHERE recipe_id = (:r_id)'
    cursor = g.conn.execute(text(cmd), r_id = r_id)
    instr_list = []
    for result in cursor:
        instr_list.append([result['position'], result['text'], result['instr_id']])
    cursor.close()
    print(instr_list)
      
    instr_list.sort()
    
    cmd = 'SELECT G.name FROM Ingredient G WHERE G.name NOT IN (SELECT G2.name FROM Uses U, Ingredient G2 WHERE U.ingr_id = G2.ingr_id AND U.recipe_id = (:r_id))'
    cursor = g.conn.execute(text(cmd), r_id=r_id)
    ingr_types = []
    for result in cursor:
        ingr_types.append(result[0])
    cursor.close()
    
    return render_template('edit_recipe.html', recipe=recipe, ingr_list=ingr_list, instr_list=instr_list, ingr_types=ingr_types)

# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
    print(request)
    name = request.form['name']
    print(name)
    cmd = 'INSERT INTO test(name) VALUES (:name1), (:name2)';
    g.conn.execute(text(cmd), name1 = name, name2 = name);
    return redirect('/')

@app.route('/delete', methods=['POST'])
def delete():
    print(request)
    name = request.form['name']
    print(name)
    cmd = 'DELETE FROM test WHERE name = (:name1);';
    g.conn.execute(text(cmd), name1 = name);
    return redirect('/')

@app.route("/register", methods=("GET", "POST"))
def register():
    """Register a new user.

    Validates that the username is not already taken. Hashes the
    password for security.
    """
    if request.method == "POST":
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]
        error = None

        if not email:
            error = "Email is required."
        elif not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."

        if error is None:
            try:
                cmd = "INSERT INTO Account(email, username, password) VALUES ((:email), (:username), (:password))"
                g.conn.execute(text(cmd), email=email, username=username, password=password)
            except exc.IntegrityError:
                # The username was already taken, which caused the
                # commit to fail. Show a validation error.
                error = "Invalid email or username."
            else:
                # Success, go to the login page.
                return redirect('log_in')

    return render_template("register.html")


@app.route("/log_in", methods=("GET", "POST"))
def login():
    """Log in a registered user by adding the user id to the session."""
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        error = None
        cmd = "SELECT * FROM Account WHERE email = (:email)"
        user = g.conn.execute(text(cmd), email=email).fetchone()

        if user is None:
            error = "Incorrect username."
        elif not check_password_hash(user["password"], password):
            error = "Incorrect password."

        if error is None:
            # store the user id in a new session and return to the index
            session.clear()
            session["user_id"] = user["email"]
            return redirect('recipe_list')

    return render_template("login.html")


@app.route("/log_out")
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect('recipe_list')


if __name__ == "__main__":
    import click

    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):
        """
        This function handles command line parameters.
        Run the server using

            python server.py

        Show the help text using

            python server.py --help

        """

        HOST, PORT = host, port
        print("running on %s:%d" % (HOST, PORT))
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


    run()
