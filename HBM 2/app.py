from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize database connection
db = None
try:
    from pymongo import MongoClient
    client = MongoClient('mongodb://localhost:27017/')
    db = client['hotel_db']
    print("MongoDB connection successful")
except ImportError:
    print("MongoDB support not available - running in limited mode")
except Exception as e:
    print(f"MongoDB connection error: {e}")

# Dummy user data
users = {"admin": "admin123"}

# Room data structure
rooms = [
    {"number": "101", "type": "AC", "bed_type": "Single", "available": True},
    {"number": "102", "type": "AC", "bed_type": "Double", "available": True},
    {"number": "103", "type": "Non-AC", "bed_type": "Single", "available": True},
    {"number": "104", "type": "Non-AC", "bed_type": "Double", "available": True},
    {"number": "201", "type": "AC", "bed_type": "Single", "available": True},
    {"number": "202", "type": "AC", "bed_type": "Double", "available": True},
    {"number": "203", "type": "Non-AC", "bed_type": "Single", "available": True},
    {"number": "204", "type": "Non-AC", "bed_type": "Double", "available": True},
]

# Dummy booking list
bookings = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        if uname in users and users[uname] == pwd:
            session['username'] = uname  # Store username in session
            return redirect(url_for('dashboard'))
        else:
            return "Login Failed"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    available_rooms = [room for room in rooms if room['available']]
    return render_template('dashboard.html', 
                         bookings=bookings, 
                         available_rooms=available_rooms,
                         all_rooms=rooms)

@app.route('/book', methods=['POST'])
def book():
    name = request.form['name']
    room_number = request.form['room']
    date = request.form['date']
    
    # Update room availability
    for room in rooms:
        if room['number'] == room_number:
            room['available'] = False
            room_type = f"{room['type']} - {room['bed_type']}"
            break
    
    bookings.append({
        'name': name,
        'room': room_number,
        'room_type': room_type,
        'date': date
    })
    
    return redirect(url_for('dashboard'))

def log_activity(user_id, activity_type, description):
    if db is None:
        return  # Skip logging if MongoDB is not available
    try:
        activity = {
            'timestamp': datetime.now(),
            'type': activity_type,
            'description': description
        }
        db.users.update_one(
            {'_id': user_id},
            {'$push': {'activities': activity}}
        )
    except:
        print("Warning: Failed to log activity")

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    activities = []
    if db:
        user = db.users.find_one({'_id': session['username']})
        if user and 'activities' in user:
            activities = user['activities']
    
    return render_template('profile.html', 
                         username=session['username'],
                         datetime=datetime,
                         bookings=bookings,
                         activities=activities)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/logout')
def logout():
    if 'username' in session:
        log_activity(session['username'], 'logout', 'User logged out')
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
