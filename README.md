# Frejun API Documentation

## Overview
Frejun is a room booking system API that allows users to sign up, log in, book rooms (conference, shared, private), manage teams, and perform administrative tasks such as managing users, rooms, and timeslots. The API uses JWT authentication and role-based permissions.

---

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

## User Rules
- User can sign in/signup.
- User sees all the available rooms on a specific date.
- User can check all the available slots of a particular room on a specific date.
- User books the room for a specific date and time slot.
- User can create and join teams.
- Only a team lead can book a room for his team.

## Admin Rules
- Admin should see all teams, can update all teams, and add any user to any team.
- Admin can perform CRUD on all users.
- Admin can perform CRUD on rooms and timeslots.

---

## Notes
- All endpoints require JWT authentication except signup and login.
- Admin role is required for admin endpoints.
- Team lead is the user who created the team.
- Shared rooms have a maximum of 4 bookings per time slot.
- Conference rooms require team booking with minimum 3 members aged 10 or older.

---

## Database Schema

### User
- Custom user model with fields:
  - `name` (unique)
  - `email` (unique)
  - `age`
  - `gender`
  - `role` (choices: admin, user)
  - `is_active`
  - `is_staff`

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
- Constraints:
  - Must have either user or team, but not both.

---
