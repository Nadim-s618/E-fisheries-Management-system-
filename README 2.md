# 🐟 E-Fisheries Management System

A modern web-based fisheries management platform designed to help fish farmers efficiently manage ponds, fish stocks, and fish growth records. The system aims to digitize fisheries operations by providing an organized, secure, and scalable solution built with **React**, **Django REST Framework**, and **PostgreSQL**.

---

# 📋 Table of Contents

- Overview
- Features
- Technology Stack
- Project Structure
- Installation
- Backend Setup
- Frontend Setup
- Environment Variables
- API Modules
- Current Progress
- Future Features
- Contributors
- License

---

# 🌊 Overview

The **E-Fisheries Management System** is being developed as an academic software engineering project to simplify fisheries management.

The system enables users to:

- Manage fish ponds
- Record fish stocking information
- Monitor fish growth
- Store fisheries data securely
- Provide a scalable foundation for future fisheries management modules

---

# ✨ Current Features

## 🔐 Authentication & Core

- User Registration
- User Login
- JWT Authentication
- Protected API Endpoints
- User Management

---

## 🏞 Pond Management

- Create Pond
- View Pond Details
- Update Pond Information
- Delete Pond
- Manage Pond Status

Each pond belongs to an authenticated user.

---

## 🐠 Stock Management

- Add Fish Stock
- View Fish Stock
- Update Stock Information
- Delete Stock
- Assign Stock to a Pond

Each stock record belongs to a specific pond.

---

## 📈 Growth Management

- Record Growth Entries
- Track Fish Weight
- Track Fish Length
- View Growth History
- Update Growth Records

Each growth record belongs to a specific stock.

---

# 🚧 Planned Features

- Feeding Management
- Water Quality Monitoring
- Fish Health Management
- Harvest Management
- Financial Management
- Weather Integration
- Notification System
- Reports & Analytics
- Dashboard
- AI-Based Growth Prediction

---

# 💻 Technology Stack

## Frontend

- React
- React Router
- Axios
- CSS

## Backend

- Python
- Django
- Django REST Framework

## Database

- PostgreSQL

## Authentication

- JWT Authentication

## Version Control

- Git
- GitHub

---

# 📁 Project Structure

```
E-FISHERIES/
│
├── .venv/
│
├── backend/
│   │
│   ├── backend/              # Django project configuration
│   │
│   ├── core/                 # Authentication & shared components
│   │
│   ├── ponds/                # Pond Management Module
│   │
│   ├── stocks/               # Stock Management Module
│   │
│   ├── growth/               # Growth Management Module
│   │
│   ├── .env
│   ├── .env.example
│   ├── manage.py
│   ├── requirements.txt
│   └── db.sqlite3
│
├── frontend/                 # React Application
│
├── .gitignore
│
└── README.md
```

---

# ⚙ Installation

Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/E-Fisheries.git
```

Navigate into the project

```bash
cd E-Fisheries
```

---

# 🔧 Backend Setup

Navigate to the backend

```bash
cd backend
```

Create a virtual environment

```bash
python -m venv .venv
```

Activate the virtual environment

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows

```bash
.venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Apply migrations

```bash
python manage.py migrate
```

Create a superuser

```bash
python manage.py createsuperuser
```

Start the backend server

```bash
python manage.py runserver
```

---

# ⚛ Frontend Setup

Navigate to the frontend

```bash
cd frontend
```

Install dependencies

```bash
npm install
```

Run the React application

```bash
npm start
```

---

# 🔐 Environment Variables

Create a `.env` file inside the `backend` directory.

Example:

```env
SECRET_KEY=your_secret_key

DEBUG=True

DB_NAME=efisheries_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

---

# 📡 API Modules

## Core

Authentication and shared services.

## Ponds

```
GET     /api/ponds/
POST    /api/ponds/
PUT     /api/ponds/{id}/
DELETE  /api/ponds/{id}/
```

---

## Stocks

```
GET     /api/stocks/
POST    /api/stocks/
PUT     /api/stocks/{id}/
DELETE  /api/stocks/{id}/
```

---

## Growth

```
GET     /api/growth/
POST    /api/growth/
PUT     /api/growth/{id}/
DELETE  /api/growth/{id}/
```

---

# 📊 Entity Relationships

```
User
 │
 └── Pond
       │
       └── Stock
              │
              └── Growth
```

- One User can own multiple Ponds.
- One Pond can contain multiple Stock records.
- One Stock can contain multiple Growth records.

---

# 🚀 Current Progress

✅ Project Setup

✅ Authentication

✅ Pond Management Module

✅ Stock Management Module

✅ Growth Management Module

🚧 Feeding Module

🚧 Water Quality Module

🚧 Financial Module

🚧 Dashboard

🚧 Notifications

---

# 📈 Future Improvements

- Interactive Dashboard
- Charts & Analytics
- Weather API Integration
- SMS Notifications
- AI-Based Fish Growth Prediction
- Harvest Forecasting
- Water Quality Monitoring
- Mobile Responsive UI
- Role-Based Access Control
- Export Reports (PDF/Excel)

---

# 👥 Contributors

- **Shahoriyer Nadim**
- Project Team Members

---

# 📄 License

This project is developed for academic and educational purposes.

---

# 🙏 Acknowledgements

Developed as part of a Software Engineering academic project. Special thanks to our supervisor, teammates, and everyone who contributed to the development of this system.
