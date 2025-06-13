  # Workspace Management System

  ## Overview
  This is a room booking system API that allows users to sign up, log in, book rooms (conference, shared, or private), manage teams, and perform administrative tasks such as managing users, rooms, and time slots. The API uses JWT authentication and role-based access control.

  ---

  ## Setup Instructions

  ### Prerequisites
  - Python 3.8+
  - pip
  - virtualenv (optional but recommended)
  - Docker and Docker Compose (optional for containerized setup)

  ### Installation

  1. Clone the repository:
  ```bash
  git clone <repository_url>
  cd <repo folder>
  ```

  2. Create and activate a virtual environment:
  ```bash
  python -m venv venv
  # On Windows
  venv\Scripts\activate
  # On Unix or MacOS
  source venv/bin/activate
  ```

  3. Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

  4. Apply migrations:
  ```bash
  python manage.py migrate
  ```

  5. Run scripts to generate initial data (if needed)(Rooms and Timeslots)
  15 rooms(8 Private Rooms ,4 Conference Rooms, 3 Shared Desks) ,
  9 time slots from 9:00AM to 6:00PM:
  ```bash
  python manage.py create_timeslots
  python manage.py create_rooms
  ```

  6. Run the development server:
  ```bash
  python manage.py runserver
  ```

  ### Using Docker (Optional)

  1. Build and start containers:
  ```bash
  docker-compose up --build
  ```

  2. The API will be available at `http://localhost:8000/`

  ---
  ## Database Schema

  ### User
  - Custom user model with fields:
    - `name` (unique)
    - `email` (unique)
    - `age`
    - `gender`
    - `role` (choices: admin, user)

  ### Team
  - Fields:
    - `name`
    - `created_by` (ForeignKey to User)
    - `members` (ManyToMany to User)

  ### Room
  - Fields:
    - `name`
    - `room_type` (choices: private, conference, shared)
    - `capacity`

  ### Timeslot
  - Fields:
    - `id` (UUID primary key)
    - `start_time`
    - `end_time`
    - `name` (auto-generated if blank)

  ### Booking
  - Fields:
    - `id` (UUID primary key)
    - `room` (ForeignKey to Room)
    - `date`
    - `time_slot` (ForeignKey to Timeslot)
    - `user` (ForeignKey to User, nullable, for private/shared bookings)
    - `team` (ForeignKey to Team, nullable, for conference bookings)
    - `timestamp` (auto-added)
    - `is_active`

  ---
  ### Design Rationale
  The schema is designed to be modular, scalable, and normalized. By separating TimeSlot, Room, Team, and Booking into distinct models, avoided data duplication and enable flexibility across room types and booking patterns. Nullable fields in Booking allow the same model to support both individual and team bookings with strict constraints at the application level. UUIDs are used for keys where global uniqueness is beneficial (e.g., booking and timeslot IDs). This structure ensures future extensibility while supporting clean role-based access control, efficient querying, and enforcement of business rules like team size limits and slot availability.


  ### User Flow

  * Users can **sign in/sign up** using the authentication endpoints.

  * Users can **create or join a team** using:

    * `POST /teams/` to create a team
    * `POST /teams/<int:team_id>/join/` to join a team

  * Users can **view available rooms** on a specific date using:

    * `GET /api/v1/rooms/available/?date=YYYY-MM-DD&room_type=TYPE&page=1`
      (Filter by date and room type)

  * Users can **book a room** for themselves or their team using:

    * `POST /api/v1/bookings/`
      Required parameters: room ID, date, time slot ID, and team ID (if team booking)
      **Note:** Only the **team leader** can book rooms for a team.

  * Users can **view their bookings**, including bookings made by teams they are part of, via:

    * `GET /api/v1/bookings/`

  * Users can **cancel bookings** using:

    * `POST /api/v1/bookings/{booking_id}/cancel/`
      **Note:** Only the **creator of the team** can cancel team bookings.

  ---

  ### Admin Flow

  * Admins can **view all bookings** using:

    * `GET /api/v1/bookings/`

  * Admins can perform full **CRUD operations on users**, rooms, and time slots.
  ---
  
  ##API Documentation

  ## Authentication

  ### Signup
  - **URL:** `/signup/`
  - **Method:** POST
  - **Description:** Register a new user and receive JWT tokens.
  - **Request Body:**
  ```json
  {
    "name": "demo_user",
    "email": "demouser@gm.com",
    "password": "admin123",
    "age": 23,
    "gender": "male",
    "role": "admin"
  }
  ```
  - **Response:**
  ```json
  {
    "refresh": "<refresh_token>",
    "access": "<access_token>"
  }
  ```
  - **Permissions:** AllowAny

  ---

  ### Login
  - **URL:** `/login/`
  - **Method:** POST
  - **Description:** Obtain JWT tokens for an existing user.
  - **Request Body:**
  ```json
  {
    "name": "demo_user",
    "password": "admin123"
  }
  ```
  - **Response:**
  ```json
  {
    "refresh": "<refresh_token>",
    "access": "<access_token>"
  }
  ```
  - **Permissions:** AllowAny

  ---

  ## Booking APIs

  ### Create Booking
  - **URL:** `/bookings/`
  - **Method:** POST
  - **Description:** Create a new booking for rooms.
  - **Request Body Examples:**

  For conference room (team required):
  ```json
  {
    "room": "Conference Room 1",
    "date": "2025-06-15",
    "time_slot": "9am time slot",
    "team": "1"
  }
  ```

  For private/shared room:
  ```json
  {
    "room": "Private Room 1",
    "date": "2025-06-15",
    "time_slot": "9am time slot"
  }
  ```
  - **Response:**
  ```json
  {
    "booking_id": "<booking_id>"
  }
  ```
  - **Permissions:** Authenticated users
  - **Notes:**
    - Team booking only allowed for conference rooms.
    - Team must have at least 3 members aged 10 or older.
    - Only team lead can book conference rooms.
    - Shared rooms have a max of 4 bookings per slot.
    - Private rooms can be booked if available.

  ---

  ### Cancel Booking
  - **URL:** `/cancel/<booking_id>/`
  - **Method:** POST
  - **Description:** Cancel an active booking.
  - **Response:**
  ```json
  {
    "success": "Booking cancelled."
  }
  ```
  - **Permissions:** Authenticated users
  - **Notes:**
    - Only booking user or team lead can cancel.

  ---

  ### List Bookings
  - **URL:** `/bookings/list/`
  - **Method:** GET
  - **Description:** List active bookings.
  - **Response Example:**
  ```json
  {
    "count": 1,
    "results": [
      {
        "id": "<booking_id>",
        "user": {
          "id": 5,
          "email": "demouser@gm.com",
          "name": "demo_user",
          "age": 23,
          "gender": "male",
          "role": "admin"
        },
        "team": null,
        "room": {
          "id": 46,
          "name": "Private Room 1",
          "room_type": "private",
          "capacity": 1
        },
        "date": "2025-06-15",
        "timestamp": "2025-06-13T06:07:41.308873Z",
        "is_active": true,
        "time_slot": "<time_slot_id>"
      }
    ]
  }
  ```
  - **Permissions:** Authenticated users
  - **Notes:**
    - Admins see all active bookings.
    - Users see their own bookings or bookings of teams they belong to.

  ---

  ## Room APIs

  ### Available Rooms and Slots
  - **URL:** `/rooms/available/`
  - **Method:** GET
  - **Description:** List available rooms and their available time slots for a given date.
  - **Query Parameters:**
    - `date` (optional, default today): Date to check availability.
    - `room_type` (optional): Filter by room type (`conference`, `shared`, `private`).
  - **Response Example:**
  ```json
  {
    "count": 8,
    "results": [
      {
        "room": {
          "id": 46,
          "name": "Private Room 1",
          "room_type": "private",
          "capacity": 1
        },
        "available_slots": [
          {
            "id": "<timeslot_id>",
            "name": "9am time slot",
            "start_time": "09:00:00",
            "end_time": "10:00:00"
          },
          ...
        ]
      },
      ...
    ]
  }
  ```
  - **Permissions:** Authenticated users

  ---

  ## Team APIs

  ### List and Create Teams
  - **URL:** `/teams/`
  - **Method:** GET, POST
  - **Description:** List teams or create a new team.
  - **Response Example:**
  ```json
  {
    "count": 1,
    "results": [
      {
        "id": 1,
        "name": "team_01",
        "created_by": 1,
        "members": [1, 2, 3]
      }
    ]
  }
  ```
  - **Permissions:** Authenticated users
  - **Notes:**
    - Admins see all teams.
    - Users see teams they created or belong to.

  ---

  ### Retrieve, Update, Delete Team
  - **URL:** `/teams/<id>/`
  - **Method:** GET, PUT, PATCH, DELETE
  - **Description:** Retrieve, update, or delete a team.
  - **Permissions:** Authenticated users
  - **Notes:**
    - Admins can access all teams.
    - Users can only update/delete teams they created.

  ---

  ### Join Team
  - **URL:** `/teams/<team_id>/join/`
  - **Method:** POST
  - **Description:** Add authenticated user to a team.
  - **Response:**
  ```json
  {
    "message": "User added to the team."
  }
  ```
  - **Permissions:** Authenticated users

  ---

  ### Admin Add User to Team
  - **URL:** `/admin/add-user-to-team/`
  - **Method:** POST
  - **Description:** Admin adds any user to any team.
  - **Request Body:**
  ```json
  {
    "team_id": 1,
    "user_id": 2
  }
  ```
  - **Response:**
  ```json
  {
    "message": "User added to the team by admin."
  }
  ```
  - **Permissions:** Admin only

  ---

  ## Admin APIs

  ### User Management
  - **List and Create Users**
    - **URL:** `/admin/users/`
    - **Method:** GET, POST
  - **Retrieve, Update, Delete User**
    - **URL:** `/admin/users/<id>/`
    - **Method:** GET, PUT, PATCH, DELETE
  - **Permissions:** Admin only

  ### Room Management
  - **List and Create Rooms**
    - **URL:** `/admin/rooms/`
    - **Method:** GET, POST
  - **Retrieve, Update, Delete Room**
    - **URL:** `/admin/rooms/<id>/`
    - **Method:** GET, PUT, PATCH, DELETE
  - **Permissions:** Admin only

  ### Timeslot Management
  - **List and Create Timeslots**
    - **URL:** `/admin/timeslots/`
    - **Method:** GET, POST
  - **Retrieve, Update, Delete Timeslot**
    - **URL:** `/admin/timeslots/<id>/`
    - **Method:** GET, PUT, PATCH, DELETE
  - **Permissions:** Admin only

  ---

  ## Notes
  - All endpoints require JWT authentication except signup and login.
  - Admin role is required for admin endpoints.
  - Team lead is the user who created the team.
  - Shared rooms have a maximum of 4 bookings per time slot.
  - Conference rooms require team booking with minimum 3 members aged 10 or older.

  

  ---
