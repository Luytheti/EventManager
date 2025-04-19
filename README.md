# Campus Event Management System

A full-stack web application for managing and registering for campus events, built using HTML, CSS, Flask (Python), and MySQL. This system allows students to view and register for events, submit feedback, and manage their participation history, while organizers can create and manage events efficiently.

## Features

### User Interface & Functionality (Option A: Working Prototype)

- **Home Page**
  - Displays a list of upcoming events.
  - Includes a search bar to filter events based on keywords (search functionality powered by SQL queries).

- **Event Details Page**
  - Shows detailed information for each event (e.g., title, description, date, time, venue).
  - Allows users to register for the event.
  - Provides a feedback section for post-event reviews.
  - Event and feedback data are dynamically fetched from the MySQL database.

- **Event Management Page (Organizer Access)**
  - Organizers can create new events and update or delete existing ones.
  - Real-time updates ensure smooth management of the event database.

- **User Profile Page**
  - Displays registered events and submitted feedback.
  - Allows users to view their participation history and modify their registrations if needed.

### Backend Integration

- All frontend pages interact with the MySQL database via Flask.
- Core functionalities include:
  - Fetching events using SQL SELECT and JOIN queries.
  - Inserting registrations and feedback using SQL INSERT statements.
  - Ensuring capacity constraints using SQL triggers.

---

## Database Design

The application uses a relational MySQL database with the following schema:

### Tables

1. **Events**
   - Columns: event_id (PK), title, date, time, location, capacity, organizer_id (FK)
2. **Organizers**
   - Columns: organizer_id (PK), club_name, contact_email
3. **Students**
   - Columns: student_id (PK), name, roll_number, email
4. **Registrations**
   - Columns: registration_id (PK), event_id (FK), student_id (FK), timestamp
5. **Feedback**
   - Columns: feedback_id (PK), event_id (FK), student_id (FK), rating, comment

### SQL Components

- **CREATE TABLE Scripts**  
  SQL scripts define schema with data types, primary keys, foreign keys, and constraints.

- **JOIN Query Example**  
  Retrieve event details along with organizer club name:
  ```sql
  SELECT Events.title, Events.date, Organizers.club_name
  FROM Events
  JOIN Organizers ON Events.organizer_id = Organizers.organizer_id;
