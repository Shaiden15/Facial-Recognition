import sqlite3
import cv2
import face_recognition
import numpy as np
from flask import Flask, render_template, request, jsonify
import os
import pickle

app = Flask(__name__)
DB_PATH = 'attendance.db'
IMAGE_FOLDER = 'static/images'

# Initialize database and create tables if they don't exist
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            face_encoding BLOB
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    ''')
    conn.commit()
    conn.close()

# Load known faces from DB
def load_known_faces():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, face_encoding FROM students")
    known_faces = {}
    for row in cursor.fetchall():
        student_id, name, encoding_blob = row
        if encoding_blob:
            encoding = pickle.loads(encoding_blob)
            known_faces[name] = {'id': student_id, 'encoding': encoding}
    conn.close()
    return known_faces

# Initialize DB and load faces
init_db()  # Create tables if they don't exist
known_faces = load_known_faces()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        image_file = request.files['image']
        image_path = os.path.join(IMAGE_FOLDER, f"{name}.jpg")
        image_file.save(image_path)
        
        # Generate face encoding
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        if encodings:
            encoding = encodings[0]
            encoding_blob = pickle.dumps(encoding)
            
            # Update DB
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("UPDATE students SET face_encoding = ? WHERE name = ?", (encoding_blob, name))
            conn.commit()
            conn.close()
            
            # Reload known faces
            global known_faces
            known_faces = load_known_faces()
            return jsonify({'message': 'Registration successful!'})
        return jsonify({'message': 'No face detected!'})
    return render_template('register.html')

@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if request.method == 'POST':
        image_file = request.files['image']
        unknown_image = face_recognition.load_image_file(image_file)
        unknown_encodings = face_recognition.face_encodings(unknown_image)
        
        if unknown_encodings:
            unknown_encoding = unknown_encodings[0]
            for name, data in known_faces.items():
                match = face_recognition.compare_faces([data['encoding']], unknown_encoding)
                if match[0]:
                    # Log attendance
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO attendance (student_id) VALUES (?)", (data['id'],))
                    conn.commit()
                    conn.close()
                    return jsonify({'message': f'Attendance marked for {name}'})
        return jsonify({'message': 'No match found'})
    return render_template('attendance.html')

if __name__ == '__main__':
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)  # Create images folder if it doesn't exist
    app.run(debug=True)