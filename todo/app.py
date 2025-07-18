from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'moon_talk_secret_2025'

# In-memory data
users = {}
tasks = []
task_id_counter = 1

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect('/login')
    
    global task_id_counter
    if request.method == 'POST':
        task = request.form['task']
        if task:
            tasks.append({'id': task_id_counter, 'task': task, 'status': False})
            task_id_counter += 1
        return redirect('/')
    
    return render_template('show.html', todos=tasks)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    task = next((t for t in tasks if t['id'] == id), None)
    if not task:
        return "Task not found"

    if request.method == 'POST':
        new_task = request.form['task']
        if new_task:
            task['task'] = new_task
            return redirect('/')
    return render_template('edit.html', task=(id, task['task']))

@app.route('/delete/<int:id>')
def delete(id):
    global tasks
    tasks = [t for t in tasks if t['id'] != id]
    return redirect('/')

@app.route('/toggle/<int:id>')
def toggle(id):
    for task in tasks:
        if task['id'] == id:
            task['status'] = not task['status']
            break
    return redirect('/')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = users.get(username)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = username
            return redirect('/')
        else:
            return 'Invalid username or password'
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users:
            return "User already exists!"

        users[username] = {
            'password': generate_password_hash(password)
        }
        return redirect('/login')
    return render_template('register.html')

@app.route('/logout')
def logout():
    name = session.get('user_id', 'User')
    session.clear()
    return render_template('logout.html', name=name)

if __name__ == '__main__':
    app.run(debug=True)
