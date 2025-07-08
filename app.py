import csv
import sqlite3
import os
from datetime import datetime
import pytz
from flask import Flask, render_template, request, redirect, url_for, session, make_response, send_file, flash, get_flashed_messages
from openpyxl import Workbook
from io import BytesIO


app = Flask(__name__)
app.secret_key = 'supersecretkey'  #used to encrypt session data
# submissions = []

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return "This is the About Page."

@app.route('/students')
def students():
    student_names = ["Alice", "Bob", "Charlie", "David"]
    return render_template('students.html', students = student_names)

@app.route('/greet', methods=['GET', 'POST'])
def greet():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        #get current Nepal time
        nepal_tz = pytz.timezone("Asia/Kathmandu")
        nepal_time = datetime.now(nepal_tz).strftime("%Y-%m-%d %H:%M:%S")

        # input validation
        if not username or not email or '@' not in email:
            error = "Please enter a valid name and email address."
            render_template('form.html', error = error)

        #Save to SQLite
        conn = sqlite3.connect('submissions.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO submissions (name, email, created_at) VALUES (?,?,?)', (username, email, nepal_time))
        conn.commit()
        conn.close()

        #save to CSV File
        with open('submissions.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([username, email])

        #save to memory 
        # submissions.append({'name': username, 'email': email})

        return redirect(url_for('show_submissions'))

        # return render_template('greet.html', name = username, email = email)
    return render_template('form.html')

@app.route('/submissions')
def show_submissions():
    # submissions = []

    # try:
    #     with open('submissions.csv', mode='r') as file:
    #         reader = csv.reader(file)
    #         for row in reader: 
    #             submissions.append({'name': row[0], 'email': row[1]})
    # except FileNotFoundError:
    #     pass

    conn = sqlite3.connect('submissions.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, email, created_at FROM submissions ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()

    submissions = [{'name': row[0], 'email': row[1], 'created_at': row[2]} for row in rows]

    return render_template('submissions.html', submissions=submissions)


@app.route('/feedback', methods = ['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form['name'].strip()
        message = request.form['message'].strip()
        #get current Nepal time
        nepal_tz = pytz.timezone("Asia/Kathmandu")
        nepal_time = datetime.now(nepal_tz).strftime("%Y-%m-%d %H:%M:%S")

        if not name or not message:
            error = "Both name and message are required!"
            return render_template('feedback.html', error = error)
        
        conn = sqlite3.connect('submissions.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO feedback (name, message, created_at) VALUES (?, ?, ?)', (name, message, nepal_time))
        conn.commit()
        conn.close()
        flash("Feedback submitted successfully!", "success")
        return redirect(url_for('feedback_list'))
    return render_template('feedback.html')


@app.route('/feedback_list')
def feedback_list():
    query = request.args.get('q', '').strip()

    conn = sqlite3.connect('submissions.db')
    cursor = conn.cursor()

    if query:
        cursor.execute("""
            SELECT name, message, created_at, id
            FROM feedback
            WHERE name LIKE ? OR message LIKE ?
            ORDER BY id DESC
        """, (f'%{query}%', f'%{query}%'))
    else:
        cursor.execute("""
            SELECT name, message, created_at, id
            FROM feedback
            ORDER BY id DESC
        """)

    feedbacks = cursor.fetchall()
    conn.close()

    return render_template('feedback_list.html', feedbacks=feedbacks, query=query)



@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        if not name or not email or not password:
            return render_template('signup.html', error = "All fields are required.")
        
        try:
            conn = sqlite3.connect('submissions.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('signup.html', error = "Email already exists.")
        
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        conn = sqlite3.connect('submissions.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM users WHERE email = ? AND password = ?', (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            print("User logged in:", user)
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['logged_in'] = True
            flash("Logged in successfully!", "success")
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error = "Invalid email or password.")
        
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session['user_name'] != 'Admin':
        return "Access Denied"
    
    conn = sqlite3.connect('submissions.db')
    cursor = conn.cursor()

    #count submissions
    cursor.execute('SELECT COUNT(*) FROM submissions')
    total_submissions = cursor.fetchone()[0]

    #count feedbacks 
    cursor.execute('SELECT COUNT(*) FROM feedback')
    total_feedbacks = cursor.fetchone()[0]

    #get recent emails
    cursor.execute('SELECT name, email FROM submissions ORDER BY id DESC LIMIT 5')
    recent_submissions = cursor.fetchall()

    conn.close()
    
    return render_template('dashboard.html', 
                           name = session['user_name'],
                           total_submissions = total_submissions,
                           total_feedbacks = total_feedbacks, 
                           recent_submissions = recent_submissions
                        )

@app.route('/export/feedbacks')
def export_feedbacks():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('submissions.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, message FROM feedback')
    feedbacks = cursor.fetchall()
    conn.close()

    #prepare CSV data
    output = "Name,Message\n"
    for f in feedbacks:
        output += f"{f[0]},{f[1]}\n"
    
    #create response
    response = make_response(output)
    response.headers["Content-Disposition"] = "attachment; filename=feedback.csv"
    response.headers["Content-type"] = "text/csv"
    return response


@app.route('/export/submissions')
def export_submissions():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('submissions.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, email FROM submissions')
    subs = cursor.fetchall()
    conn.close()

    #prepare CSV data
    output = "Name,Email\n"
    for s in subs:
        output += f"{s[0]},{s[1]}\n"
    
    #create response
    response = make_response(output)
    response.headers["Content-Disposition"] = "attachment; filename=submissions.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@app.route('/export/filter', methods=['GET', 'POST'])
def export_filter():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        start = request.form['start']
        end = request.form['end']
        email = request.form['email'].strip()

        #SQL query with optional email filter

        query = "SELECT name, email, created_at FROM submissions WHERE date(created_at) BETWEEN ? AND ?"
        params = [start, end]

        if email:
            query += "AND email = ?"
            params.append(email)
        
        #Run QUERY
        conn = sqlite3.connect('submissions.db')
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        #create excel workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Filtered Submissions"

        #add headers
        ws.append(["Name", "Email", "Date"])

        #add data rows with formatting
        for row in rows:
            try: 
                dt = datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S")
                formatted_date = dt.strftime("%d-%m-%Y %I:%M %p")
            except:
                formatted_date = row[2]
            
            ws.append([row[0], row[1], formatted_date])

        #auto size columns
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            ws.column_dimensions[column_letter].width = max_length + 2

        #save to memory buffer
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        return send_file(output, download_name="filtered_submissions.xlsx", as_attachment=True)
    
    return render_template('export_filter.html')


@app.route('/delete-feedback/<int:feedback_id>', methods=['POST'])
def delete_feedback(feedback_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('submissions.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM feedback WHERE id = ?', (feedback_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('feedback_list'))


if __name__ == '__main__':
    app.run(debug=True)