# 🐟 E-Fisheries Management System

> A modern web-based fisheries management platform built with **React**, **Django REST Framework**, and **PostgreSQL** to streamline aquaculture operations through digital management, monitoring, and analytics.

---

## 📖 Project Overview

The **E-Fisheries Management System** is a full-stack web application designed to assist fish farmers, fisheries managers, and administrators in managing fish farming activities efficiently.

The system centralizes important farming operations such as pond management, fish stock monitoring, water quality tracking, feeding schedules, disease management, inventory control, sales management, reporting, and user administration.

By replacing manual record keeping with a digital platform, the system improves productivity, data accuracy, and decision-making.

---

# 🎯 Project Objectives

- Digitize fisheries management processes
- Improve farm monitoring and record keeping
- Track water quality and fish health
- Manage inventory and feeding schedules
- Generate analytical reports
- Provide secure authentication and authorization
- Create an intuitive and responsive user interface

---

# 👨‍💻 Tech Stack

## Frontend

- React
- Vite
- React Router
- Axios
- Tailwind CSS (or your chosen CSS framework)

## Backend

- Django
- Django REST Framework
- JWT Authentication
- Python

## Database

- PostgreSQL

## Version Control

- Git
- GitHub

---

# 📂 Project Structure

```text
e-fisheries/
│
├── backend/
│   ├── accounts/
│   ├── pond/
│   ├── fish_stock/
│   ├── feeding/
│   ├── water_quality/
│   ├── disease/
│   ├── inventory/
│   ├── reports/
│   ├── notifications/
│   ├── dashboard/
│   ├── config/
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   ├── src/
│   │
│   ├── assets/
│   ├── components/
│   ├── pages/
│   ├── layouts/
│   ├── services/
│   ├── hooks/
│   ├── context/
│   ├── routes/
│   └── App.jsx
│
├── docs/
├── README.md
├── .gitignore
└── LICENSE
```

---

# ✨ Features

## 🔐 User Authentication

- User Registration
- Secure Login
- JWT Authentication
- Password Encryption
- Role-Based Access Control
- Profile Management

---

## 🐠 Fish Stock Management

- Add Fish Stock
- Update Fish Information
- Stock Monitoring
- Fish Growth Records
- Harvest Records

---

## 🌊 Pond Management

- Create Pond
- Pond Information
- Pond Capacity
- Pond Status
- Pond History

---

## 💧 Water Quality Monitoring

- Temperature Tracking
- pH Monitoring
- Dissolved Oxygen
- Ammonia Level
- Water Quality History
- Alerts for Unsafe Values

---

## 🍽 Feeding Management

- Feeding Schedule
- Feed Type
- Feed Quantity
- Feeding History
- Automated Reminders

---

## 🦠 Disease Management

- Disease Records
- Symptom Tracking
- Treatment Information
- Health Monitoring
- Disease History

---

## 📦 Inventory Management

- Feed Inventory
- Medicine Inventory
- Equipment Records
- Stock Alerts
- Inventory Transactions

---

## 💰 Sales Management

- Customer Information
- Sales Records
- Invoice Tracking
- Revenue Reports

---

## 📊 Dashboard

- Farm Overview
- Recent Activities
- Water Quality Summary
- Fish Population Statistics
- Inventory Summary
- Quick Access Cards

---

## 📈 Reports & Analytics

- Harvest Reports
- Inventory Reports
- Water Quality Reports
- Sales Reports
- Growth Analysis
- Export to PDF
- Export to Excel

---

## 🔔 Notifications

- Feeding Reminder
- Low Inventory Alert
- Water Quality Alert
- Disease Alert
- Harvest Reminder

---

# 🔒 User Roles

## Administrator

- Manage Users
- Manage Entire System
- Generate Reports
- Configure System

## Fisheries Manager

- Manage Ponds
- Manage Fish Stock
- Monitor Water Quality
- Manage Feeding
- Generate Reports

## Staff

- Update Daily Records
- Feed Fish
- Record Water Quality
- Record Diseases

---

# 🛠 Installation

## Clone Repository

```bash
git clone https://github.com/yourusername/e-fisheries.git
```

```bash
cd e-fisheries
```

---

# Backend Setup

Create virtual environment

```bash
python -m venv .venv
```

Activate virtual environment

### Windows

```bash
.venv\Scripts\activate
```

### macOS/Linux

```bash
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run migrations

```bash
python manage.py migrate
```

Start Django server

```bash
python manage.py runserver
```

---

# Frontend Setup

Navigate to frontend

```bash
cd frontend
```

Install dependencies

```bash
npm install
```

Run development server

```bash
npm run dev
```

---

# Database

The project uses PostgreSQL.

Update your `.env` file:

```env
DB_NAME=e_fisheries
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

SECRET_KEY=your_secret_key
DEBUG=True
```

---

# API Architecture

```text
React
   │
Axios Requests
   │
Django REST API
   │
Business Logic
   │
PostgreSQL Database
```

---

# Development Roadmap

### Phase 1

- Project Setup
- Authentication
- Homepage
- Dashboard

### Phase 2

- Pond Management
- Fish Stock Management
- User Management

### Phase 3

- Water Quality Module
- Feeding Module
- Disease Module

### Phase 4

- Inventory Module
- Sales Module
- Reports

### Phase 5

- Notifications
- Testing
- Bug Fixes
- Deployment

---

# Testing

Backend

```bash
python manage.py test
```

Frontend

```bash
npm test
```

---

# Future Improvements

- Mobile Application
- AI Disease Detection
- IoT Water Quality Sensors
- SMS Notifications
- Email Notifications
- Weather Integration
- Predictive Analytics
- Cloud Deployment

---

# Screenshots

> Screenshots will be added as the project progresses.

---

# Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push your branch
5. Open a Pull Request

---

# License

This project is developed for academic purposes.

---

# Authors

**Shahoriyer Nadim**

Department of Computer Science & Engineering

---

# Acknowledgements

- Django
- Django REST Framework
- React
- PostgreSQL
- Vite
- GitHub

---

## ⭐ Project Status

🚧 **Currently Under Active Development**

Sprint Progress:

- ✅ Project Planning
- ✅ Frontend Structure
- ✅ Backend Structure
- ✅ PostgreSQL Integration
- 🔄 User Authentication
- 🔄 Homepage Integration
- ⏳ Pond Management
- ⏳ Water Quality Module
- ⏳ Fish Stock Module
- ⏳ Reporting System
- ⏳ Testing
- ⏳ Deployment

---

> Built with ❤️ using React, Django REST Framework, and PostgreSQL.
