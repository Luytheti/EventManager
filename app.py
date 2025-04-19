from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure secret key

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Rajas@1231',  # Add your MySQL password here
    'database': 'event_management'
}

# Hardcoded user credentials
HARDCODED_USERS = {
    'student': {
        'email': 'student@example.com',
        'password': 'student123',
        'name': 'John Student',
        'id': 1
    },
    'organizer': {
        'email': 'organizer@example.com',
        'password': 'organizer123',
        'name': 'Jane Organizer',
        'id': 1
    }
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def home():
    # Get search parameters
    search_query = request.args.get('search', '')
    date_filter = request.args.get('date', '')
    organizer_filter = request.args.get('organizer', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Base query
        query = '''
            SELECT e.*, o.club_name,
                   (SELECT COUNT(*) FROM Registrations r WHERE r.event_id = e.event_id) as registered_count,
                   (e.capacity - (SELECT COUNT(*) FROM Registrations r WHERE r.event_id = e.event_id)) as available_seats
            FROM Events e 
            JOIN Organizers o ON e.organizer_id = o.organizer_id 
            WHERE 1=1
        '''
        params = []
        
        # Add search conditions
        if search_query:
            query += ''' AND (
                e.title LIKE %s OR 
                e.location LIKE %s OR 
                o.club_name LIKE %s
            )'''
            search_param = f'%{search_query}%'
            params.extend([search_param, search_param, search_param])
        
        if date_filter:
            query += ' AND e.event_date = %s'
            params.append(date_filter)
        
        if organizer_filter:
            query += ' AND e.organizer_id = %s'
            params.append(organizer_filter)
        
        # Add ordering
        query += ' ORDER BY e.event_date'
        
        # Execute query
        cursor.execute(query, params)
        events = cursor.fetchall()
        
        # Get all organizers for the filter dropdown
        cursor.execute('SELECT organizer_id, club_name FROM Organizers ORDER BY club_name')
        organizers = cursor.fetchall()
        
        return render_template('home.html', 
                             events=events, 
                             organizers=organizers,
                             search_query=search_query,
                             date_filter=date_filter,
                             organizer_filter=organizer_filter)
                             
    except Exception as e:
        print(f"Error in home route: {str(e)}")
        flash('An error occurred while loading events')
        return render_template('home.html', events=[], organizers=[])
    finally:
        cursor.close()
        conn.close()

@app.route('/event/<int:event_id>')
def event_details(event_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get event details with seat availability
    cursor.execute('''
        SELECT e.*, o.club_name, o.contact_email,
               (SELECT COUNT(*) FROM Registrations r WHERE r.event_id = e.event_id) as registered_count,
               (e.capacity - (SELECT COUNT(*) FROM Registrations r WHERE r.event_id = e.event_id)) as available_seats
        FROM Events e 
        JOIN Organizers o ON e.organizer_id = o.organizer_id 
        WHERE e.event_id = %s
    ''', (event_id,))
    event = cursor.fetchone()
    
    # Check if the student is registered for this event
    is_registered = False
    if 'user_type' in session and session['user_type'] == 'student':
        cursor.execute('''
            SELECT * FROM Registrations 
            WHERE event_id = %s AND student_id = %s
        ''', (event_id, session['user_id']))
        registration = cursor.fetchone()
        is_registered = registration is not None
    
    # Get feedback
    cursor.execute('''
        SELECT f.*, s.name 
        FROM Feedback f 
        JOIN Students s ON f.student_id = s.student_id 
        WHERE f.event_id = %s
    ''', (event_id,))
    feedback = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('event_details.html', event=event, feedback=feedback, is_registered=is_registered)

@app.route('/register_event', methods=['POST'])
def register_event():
    if 'user_type' not in session or session['user_type'] != 'student':
        flash('Please login as a student to register for events')
        return redirect(url_for('login'))
    
    event_id = request.form['event_id']
    student_id = session['user_id']
    
    print(f"Registering student {student_id} for event {event_id}")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check for conflicts first
        cursor.execute('''
            SELECT COUNT(*) as conflict_count
            FROM Registrations R
            JOIN Events E1 ON R.event_id = E1.event_id
            JOIN Events E2 ON E2.event_id = %s
            WHERE R.student_id = %s
              AND E1.event_date = E2.event_date
              AND E1.event_time < E2.event_time + INTERVAL 2 HOUR
              AND E1.event_time + INTERVAL 2 HOUR > E2.event_time
        ''', (event_id, student_id))
        conflict = cursor.fetchone()
        
        if conflict['conflict_count'] > 0:
            flash('Warning: You have another event scheduled at the same time!')
            return redirect(url_for('event_details', event_id=event_id))
        
        # Register the student (triggers will handle capacity check)
        cursor.execute('''
            INSERT INTO Registrations (event_id, student_id, registration_date)
            VALUES (%s, %s, NOW())
        ''', (event_id, student_id))
        conn.commit()
        
        print(f"Registration successful for student {student_id} for event {event_id}")
        flash('Registration successful!')
        
    except mysql.connector.Error as err:
        print(f"Error registering for event: {str(err)}")
        if err.errno == 1644:  # Custom error from trigger
            flash(str(err.msg))
        else:
            flash('Registration failed. Please try again.')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('event_details', event_id=event_id))

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if 'user_type' not in session or session['user_type'] != 'student':
        flash('Please login as a student to submit feedback')
        return redirect(url_for('login'))
    
    event_id = request.form['event_id']
    student_id = session['user_id']  # Use session ID instead of form value for security
    rating = request.form['rating']
    comment = request.form['comment']
    
    print(f"Submitting feedback - Event ID: {event_id}, Student ID: {student_id}, Rating: {rating}")  # Debug print
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if student is registered for this event
        cursor.execute('''
            SELECT * FROM Registrations 
            WHERE event_id = %s AND student_id = %s
        ''', (event_id, student_id))
        registration = cursor.fetchone()
        
        if not registration:
            flash('You must be registered for this event to submit feedback')
            return redirect(url_for('event_details', event_id=event_id))
        
        # Check if feedback already exists
        cursor.execute('''
            SELECT * FROM Feedback 
            WHERE event_id = %s AND student_id = %s
        ''', (event_id, student_id))
        existing_feedback = cursor.fetchone()
        
        if existing_feedback:
            flash('You have already submitted feedback for this event')
            return redirect(url_for('event_details', event_id=event_id))
        
        # Insert feedback
        cursor.execute('''
            INSERT INTO Feedback (event_id, student_id, rating, comment)
            VALUES (%s, %s, %s, %s)
        ''', (event_id, student_id, rating, comment))
        conn.commit()
        
        print(f"Feedback submitted successfully")  # Debug print
        flash('Feedback submitted successfully!')
    except Exception as e:
        print(f"Error submitting feedback: {str(e)}")  # Debug print
        flash(f'Error submitting feedback: {str(e)}')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('event_details', event_id=event_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type']
        
        print(f"Login attempt - Email: {email}, User Type: {user_type}")  # Debug print
        
        # First check hardcoded credentials
        if user_type in HARDCODED_USERS:
            hardcoded_user = HARDCODED_USERS[user_type]
            if email == hardcoded_user['email'] and password == hardcoded_user['password']:
                session['user_id'] = hardcoded_user['id']
                session['user_type'] = user_type
                session['user_name'] = hardcoded_user['name']
                
                flash(f'Welcome back, {hardcoded_user["name"]}!')
                if user_type == 'student':
                    return redirect(url_for('student_dashboard'))
                else:
                    return redirect(url_for('organizer_dashboard'))
        
        # If hardcoded credentials don't match, try database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            if user_type == 'student':
                cursor.execute('SELECT * FROM Students WHERE email = %s AND password = %s', (email, password))
            else:
                cursor.execute('SELECT * FROM Organizers WHERE email = %s AND password = %s', (email, password))
            
            user = cursor.fetchone()
            
            if user:
                session['user_id'] = user['student_id' if user_type == 'student' else 'organizer_id']
                session['user_type'] = user_type
                session['user_name'] = user['name']
                
                flash(f'Welcome back, {user["name"]}!')
                if user_type == 'student':
                    return redirect(url_for('student_dashboard'))
                else:
                    return redirect(url_for('organizer_dashboard'))
            
            flash('Invalid email or password')
        except Exception as e:
            print(f"Login error: {str(e)}")  # Debug print
            flash('An error occurred during login')
        finally:
            cursor.close()
            conn.close()
        
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/student/dashboard')
def student_dashboard():
    if 'user_type' not in session or session['user_type'] != 'student':
        flash('Please login as a student to access this page')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get upcoming events
        cursor.execute('''
            SELECT e.*, o.club_name,
                   (SELECT COUNT(*) FROM Registrations r WHERE r.event_id = e.event_id) as registered_count,
                   (e.capacity - (SELECT COUNT(*) FROM Registrations r WHERE r.event_id = e.event_id)) as available_seats
            FROM Events e 
            JOIN Organizers o ON e.organizer_id = o.organizer_id 
            WHERE e.event_date >= CURDATE() 
            ORDER BY e.event_date
            LIMIT 6
        ''')
        upcoming_events = cursor.fetchall()
        
        # Get student's registrations
        cursor.execute('''
            SELECT e.*, o.club_name, r.registration_date
            FROM Events e 
            JOIN Organizers o ON e.organizer_id = o.organizer_id 
            JOIN Registrations r ON e.event_id = r.event_id
            WHERE r.student_id = %s
            ORDER BY e.event_date DESC
        ''', (session['user_id'],))
        registrations = cursor.fetchall()
        
        return render_template('student_dashboard.html', 
                             upcoming_events=upcoming_events,
                             registrations=registrations,
                             today_date=datetime.now().date())
                             
    except Exception as e:
        print(f"Error in student_dashboard: {str(e)}")
        flash('An error occurred while loading the dashboard')
        return redirect(url_for('login'))
    finally:
        cursor.close()
        conn.close()

@app.route('/student/registrations')
def my_registrations():
    if 'user_type' not in session or session['user_type'] != 'student':
        flash('Please login as a student to access this page')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if registration_date column exists
        cursor.execute("SHOW COLUMNS FROM Registrations LIKE 'registration_date'")
        column_exists = cursor.fetchone()
        
        if not column_exists:
            print("Registration date column not found, adding it to the Registrations table")
            cursor.execute("ALTER TABLE Registrations ADD COLUMN registration_date DATETIME DEFAULT CURRENT_TIMESTAMP")
            conn.commit()
        
        # Get today's date for comparison
        today_date = datetime.now().date()
        
        # Get student's registrations with feedback status
        cursor.execute('''
            SELECT e.*, o.club_name, r.registration_date,
                   CASE WHEN f.feedback_id IS NOT NULL THEN 1 ELSE 0 END as has_feedback
            FROM Events e 
            JOIN Organizers o ON e.organizer_id = o.organizer_id 
            JOIN Registrations r ON e.event_id = r.event_id
            LEFT JOIN Feedback f ON e.event_id = f.event_id AND f.student_id = %s
            WHERE r.student_id = %s
            ORDER BY e.event_date DESC
        ''', (session['user_id'], session['user_id']))
        registrations = cursor.fetchall()
        
        return render_template('my_registrations.html', registrations=registrations, today_date=today_date)
    
    except Exception as e:
        print(f"Error in my_registrations: {str(e)}")
        flash('An error occurred while loading your registrations')
        return redirect(url_for('student_dashboard'))
    
    finally:
        cursor.close()
        conn.close()

@app.route('/organizer/dashboard')
def organizer_dashboard():
    if 'user_type' not in session or session['user_type'] != 'organizer':
        flash('Please login as an organizer to access this page')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get recent events created by the organizer
    cursor.execute('''
        SELECT e.*, 
               (SELECT COUNT(*) FROM Registrations r WHERE r.event_id = e.event_id) as registered_count
        FROM Events e 
        WHERE e.organizer_id = %s
        ORDER BY e.event_date DESC
        LIMIT 6
    ''', (session['user_id'],))
    recent_events = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('organizer_dashboard.html', recent_events=recent_events)

@app.route('/organizer/create_event', methods=['GET', 'POST'])
def create_event():
    if 'user_id' not in session or session.get('user_type') != 'organizer':
        flash('Please log in as an organizer to create events.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        event_date = request.form.get('event_date')
        event_time = request.form.get('event_time')
        location = request.form.get('location')
        capacity = request.form.get('capacity')
        confirm = request.form.get('confirm')
        
        if not all([title, description, event_date, event_time, location, capacity]):
            flash('All fields are required.', 'error')
            return redirect(url_for('create_event'))
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check for date conflicts
            cursor.execute('''
                SELECT title, event_time 
                FROM Events 
                WHERE event_date = %s AND organizer_id != %s
            ''', (event_date, session['user_id']))
            conflicts = cursor.fetchall()
            
            if conflicts and not confirm:
                event_data = {
                    'title': title,
                    'description': description,
                    'event_date': event_date,
                    'event_time': event_time,
                    'location': location,
                    'capacity': capacity
                }
                return render_template('confirm_event.html', 
                                    event_data=event_data,
                                    conflicts=conflicts)
            
            # Create the event
            cursor.execute('''
                INSERT INTO Events (title, description, event_date, event_time, 
                                  location, capacity, organizer_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (title, description, event_date, event_time, 
                  location, capacity, session['user_id']))
            
            conn.commit()
            flash('Event created successfully!', 'success')
            return redirect(url_for('organizer_dashboard'))
            
        except Exception as e:
            print(f"Error creating event: {str(e)}")
            flash('An error occurred while creating the event.', 'error')
            return redirect(url_for('create_event'))
        finally:
            if conn:
                conn.close()
    
    return render_template('create_event.html')

@app.route('/organizer/events')
def organizer_events():
    if 'user_type' not in session or session['user_type'] != 'organizer':
        flash('Please login as an organizer to access this page')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute('''
        SELECT e.*, 
               (SELECT COUNT(*) FROM Registrations r WHERE r.event_id = e.event_id) as registered_count
        FROM Events e 
        WHERE e.organizer_id = %s
        ORDER BY e.event_date DESC
    ''', (session['user_id'],))
    events = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('organizer_events.html', events=events)

@app.route('/organizer/event/<int:event_id>/registrations')
def event_registrations(event_id):
    if 'user_type' not in session or session['user_type'] != 'organizer':
        flash('Please login as an organizer to access this page')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get event details
    cursor.execute('''
        SELECT * FROM Events WHERE event_id = %s AND organizer_id = %s
    ''', (event_id, session['user_id']))
    event = cursor.fetchone()
    
    if not event:
        flash('Event not found or you do not have permission to view it')
        return redirect(url_for('organizer_events'))
    
    # Get registrations for this event
    cursor.execute('''
        SELECT s.name, s.email, r.registration_date
        FROM Registrations r
        JOIN Students s ON r.student_id = s.student_id
        WHERE r.event_id = %s
        ORDER BY r.registration_date DESC
    ''', (event_id,))
    registrations = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('event_registrations.html', event=event, registrations=registrations)

@app.route('/organizer/event/<int:event_id>/view_registrations')
def view_registrations(event_id):
    if 'user_type' not in session or session['user_type'] != 'organizer':
        flash('Please login as an organizer to access this page')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get event details
        cursor.execute('''
            SELECT * FROM Events WHERE event_id = %s AND organizer_id = %s
        ''', (event_id, session['user_id']))
        event = cursor.fetchone()
        
        if not event:
            flash('Event not found or you do not have permission to view it')
            return redirect(url_for('organizer_events'))
        
        # Get registrations for this event with student details
        cursor.execute('''
            SELECT s.name, s.email, r.registration_date
            FROM Registrations r
            JOIN Students s ON r.student_id = s.student_id
            WHERE r.event_id = %s
            ORDER BY r.registration_date DESC
        ''', (event_id,))
        registrations = cursor.fetchall()
        
        return render_template('view_registrations.html', event=event, registrations=registrations)
    
    except Exception as e:
        print(f"Error in view_registrations: {str(e)}")
        flash('An error occurred while loading registrations')
        return redirect(url_for('organizer_events'))
    
    finally:
        cursor.close()
        conn.close()

@app.route('/organizer/event/<int:event_id>/cancel', methods=['POST'])
def cancel_event(event_id):
    if 'user_type' not in session or session['user_type'] != 'organizer':
        flash('Please login as an organizer to cancel events')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update event status to canceled (feedback deletion trigger will fire)
        cursor.execute('''
            UPDATE Events 
            SET status = 'canceled' 
            WHERE event_id = %s AND organizer_id = %s
        ''', (event_id, session['user_id']))
        conn.commit()
        
        flash('Event canceled successfully. All feedback has been removed.')
    except Exception as e:
        print(f"Error canceling event: {str(e)}")
        flash('Error canceling event. Please try again.')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('organizer_events'))

@app.route('/student/unregister/<int:event_id>', methods=['POST'])
def unregister_event(event_id):
    if 'user_type' not in session or session['user_type'] != 'student':
        flash('Please login as a student to unregister from events')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Delete registration (feedback deletion trigger will fire)
        cursor.execute('''
            DELETE FROM Registrations 
            WHERE event_id = %s AND student_id = %s
        ''', (event_id, session['user_id']))
        conn.commit()
        
        flash('Successfully unregistered from the event.')
    except Exception as e:
        print(f"Error unregistering from event: {str(e)}")
        flash('Error unregistering from event. Please try again.')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('my_registrations'))

@app.route('/organizer/event/<int:event_id>/delete', methods=['POST'])
def delete_event(event_id):
    if 'user_type' not in session or session['user_type'] != 'organizer':
        flash('Please login as an organizer to delete events')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First verify the organizer owns this event
        cursor.execute('''
            SELECT title FROM Events 
            WHERE event_id = %s AND organizer_id = %s
        ''', (event_id, session['user_id']))
        event = cursor.fetchone()
        
        if not event:
            flash('Event not found or you do not have permission to delete it')
            return redirect(url_for('organizer_events'))
        
        # Delete the event (cleanup trigger will handle related records)
        cursor.execute('DELETE FROM Events WHERE event_id = %s', (event_id,))
        conn.commit()
        
        flash(f'Event "{event[0]}" has been deleted. All registrations and feedback have been removed.')
    except Exception as e:
        print(f"Error deleting event: {str(e)}")
        flash('Error deleting event. Please try again.')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('organizer_events'))

@app.route('/organizer/event/<int:event_id>/feedback')
def view_feedback(event_id):
    if 'user_type' not in session or session['user_type'] != 'organizer':
        flash('Please log in as an organizer to view feedback.', 'error')
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get event details and verify ownership
        cursor.execute('''
            SELECT * FROM Events 
            WHERE event_id = %s AND organizer_id = %s
        ''', (event_id, session['user_id']))
        event = cursor.fetchone()
        
        if not event:
            flash('Event not found or you do not have permission to view its feedback.', 'error')
            return redirect(url_for('organizer_events'))
        
        # Check if feedback_date column exists
        cursor.execute("SHOW COLUMNS FROM Feedback LIKE 'feedback_date'")
        column_exists = cursor.fetchone()
        
        if not column_exists:
            print("Feedback date column not found, adding it to the Feedback table")
            cursor.execute("ALTER TABLE Feedback ADD COLUMN feedback_date DATETIME DEFAULT CURRENT_TIMESTAMP")
            conn.commit()
        
        # Get all registrations with feedback
        cursor.execute('''
            SELECT r.*, s.name as student_name, s.email as student_email,
                   f.rating, f.comment, f.feedback_date
            FROM Registrations r
            JOIN Students s ON r.student_id = s.student_id
            LEFT JOIN Feedback f ON r.event_id = f.event_id AND r.student_id = f.student_id
            WHERE r.event_id = %s
            ORDER BY f.feedback_date DESC NULLS LAST, r.registration_date DESC
        ''', (event_id,))
        registrations = cursor.fetchall()
        
        # Calculate feedback statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_feedback,
                COALESCE(AVG(rating), 0) as avg_rating,
                COUNT(CASE WHEN rating >= 4 THEN 1 END) as positive_feedback
            FROM Feedback
            WHERE event_id = %s
        ''', (event_id,))
        stats = cursor.fetchone()
        
        # Ensure stats has default values if no feedback exists
        if not stats:
            stats = {
                'total_feedback': 0,
                'avg_rating': 0,
                'positive_feedback': 0
            }
        
        print(f"Found {len(registrations)} registrations with feedback for event {event_id}")
        
        return render_template('view_feedback.html',
                             event=event,
                             registrations=registrations,
                             stats=stats)
                             
    except Exception as e:
        print(f"Error in view_feedback: {str(e)}")
        flash('An error occurred while loading feedback.', 'error')
        return redirect(url_for('organizer_events'))
        
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/organizer/delete_account', methods=['POST'])
def delete_organizer_account():
    if 'user_id' not in session or session.get('user_type') != 'organizer':
        flash('Please log in as an organizer to delete your account.', 'error')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First delete all events created by the organizer
        cursor.execute('DELETE FROM Events WHERE organizer_id = %s', (session['user_id'],))
        
        # Then delete the organizer account
        cursor.execute('DELETE FROM Organizers WHERE organizer_id = %s', (session['user_id'],))
        
        conn.commit()
        
        # Clear session
        session.clear()
        flash('Your account and all associated events have been deleted.', 'success')
        return redirect(url_for('login'))
        
    except Exception as e:
        print(f"Error deleting organizer account: {str(e)}")
        flash('An error occurred while deleting your account.', 'error')
        return redirect(url_for('organizer_dashboard'))
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=True) 