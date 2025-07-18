from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'moon_talk_secret_2025')

# Database connection function
def get_db_connection():
    return psycopg2.connect(
        database_url=os.environ.get('DATABASE_URL'),
        sslmode='require'
    )

# Initialize database tables
def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Create users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            )
        """)
        
        # Create tasks table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                task TEXT NOT NULL,
                status BOOLEAN DEFAULT FALSE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")

# Initialize database on startup
init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect('/login')
     
    if request.method == 'POST':
        task = request.form['task']
        if task:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO tasks (task, user_id) VALUES (%s, %s)", (task, session['user_id']))
            conn.commit()
            cur.close()
            conn.close()
        return redirect('/')
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE user_id = %s ORDER BY id DESC", (session['user_id'],))
    todos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('show.html', todos=todos)

@app.route('/edit/<int:id>', methods=['GET','POST'])
def edit(id):
    if 'user_id' not in session:
        return redirect('/login')
        
    if request.method == 'POST':
        new_task = request.form['task']
        if new_task:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE tasks SET task = %s WHERE id = %s AND user_id = %s", (new_task, id, session['user_id']))
            conn.commit()
            cur.close()
            conn.close()
            return redirect('/')
    else:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM tasks WHERE id = %s AND user_id = %s", (id, session['user_id']))
        task = cur.fetchone()
        cur.close()
        conn.close()
        return render_template('edit.html', task=task)

@app.route('/delete/<int:id>', methods=['GET'])
def delete(id):
    if 'user_id' not in session:
        return redirect('/login')
        
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = %s AND user_id = %s", (id, session['user_id']))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect('/')
        else:
            return 'Invalid username or password'
    
    return render_template('login.html')
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        hashed_pw = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_pw))
            conn.commit()
            cur.close()
            conn.close()
            return redirect('/login')
        except psycopg2.IntegrityError:
            return 'Username already exists!'
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    name = session.get('username','User')
    session.clear()
    return render_template('logout.html', name=name)

@app.route('/toggle/<int:id>')
def toggle(id):
    if 'user_id' not in session:
        return redirect('/login')
        
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT status FROM tasks WHERE id = %s AND user_id = %s", (id, session['user_id']))
    result = cur.fetchone()
    
    if result:
        current_status = result[0]
        new_status = not current_status
        cur.execute("UPDATE tasks SET status = %s WHERE id = %s AND user_id = %s", (new_status, id, session['user_id']))
        conn.commit()
    
    cur.close()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)