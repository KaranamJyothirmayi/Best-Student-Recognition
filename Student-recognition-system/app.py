from flask import Flask, request, jsonify, render_template
import sqlite3
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Database initialization function
def init_db():
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()

    # Create students table with GPA
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        batch_year TEXT NOT NULL,
        department TEXT NOT NULL,
        gpa REAL NOT NULL
    )
    ''')

    # Create achievements table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        level TEXT NOT NULL,
        achievement_date TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
    ''')

    conn.commit()
    conn.close()

# Call the database initialization function
init_db()

# Function to connect to the database
def connect_db():
    return sqlite3.connect('students.db')

@app.route('/')
def home():
    return render_template('index.html')

# Route to add a student
@app.route('/add_student', methods=['POST'])
def add_student():
    data = request.get_json()
    name = data.get('name', '')
    batch_year = data.get('batch_year', '')
    department = data.get('department', '')
    gpa = data.get('gpa', 0.0)

    if not name or not batch_year or not department or not gpa:
        logging.error("Failed to add student: Missing required fields.")
        return jsonify({'message': 'All fields are required!'}), 400

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO students (name, batch_year, department, gpa) VALUES (?, ?, ?, ?)',
                       (name, batch_year, department, float(gpa)))
        conn.commit()
        logging.info(f"Student added: {name}, {batch_year}, {department}, {gpa}")
        return jsonify({'message': 'Student added successfully!'})
    except sqlite3.Error as e:
        logging.error(f"Failed to add student: {e}")
        return jsonify({'message': 'Failed to add student', 'error': str(e)}), 500
    finally:
        conn.close()

# Route to add an achievement
@app.route('/add_achievement', methods=['POST'])
def add_achievement():
    data = request.get_json()
    student_id = data.get('student_id')
    category = data.get('category', '')
    description = data.get('description', '')
    level = data.get('level', '')
    achievement_date = data.get('achievement_date', '')

    if not student_id or not category or not description or not level or not achievement_date:
        logging.error("Failed to add achievement: Missing required fields.")
        return jsonify({'message': 'All fields are required!'}), 400

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO achievements (student_id, category, description, level, achievement_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (student_id, category, description, level, achievement_date))
        conn.commit()
        logging.info(f"Achievement added for student ID {student_id}: {category}, {description}, {level}, {achievement_date}")
        return jsonify({'message': 'Achievement added successfully!'})
    except sqlite3.Error as e:
        logging.error(f"Failed to add achievement: {e}")
        return jsonify({'message': 'Failed to add achievement', 'error': str(e)}), 500
    finally:
        conn.close()

# Route to fetch the top 3 students based on achievements and GPA
@app.route('/rank_students', methods=['GET'])
def rank_students():
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Query to count achievements per student and rank them by achievements and GPA
        cursor.execute('''
            SELECT s.id, s.name, s.batch_year, s.department, s.gpa, COUNT(a.id) as achievement_count
            FROM students s
            LEFT JOIN achievements a ON s.id = a.student_id
            GROUP BY s.id
            ORDER BY achievement_count DESC, s.gpa DESC
            LIMIT 3
        ''')

        top_students = cursor.fetchall()
        result = []
        for student in top_students:
            result.append({
                'student_id': student[0],
                'name': student[1],
                'batch_year': student[2],
                'department': student[3],
                'gpa': student[4],
                'achievement_count': student[5]
            })

        return jsonify({'top_students': result})
    except sqlite3.Error as e:
        logging.error(f"Failed to fetch top students: {e}")
        return jsonify({'message': 'Failed to fetch top students', 'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
