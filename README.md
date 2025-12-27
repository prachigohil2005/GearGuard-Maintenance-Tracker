📌 Problem Statement

Organizations often face challenges such as:

Untracked maintenance requests

Poor coordination between teams

Lack of centralized equipment data

No visibility on request status

GearGuard solves this by providing a centralized maintenance tracker with dashboards, team management, and request workflows.

💡 Solution Overview

GearGuard provides:

Authentication system

Dashboard overview

Equipment management

Maintenance request tracking

Team management

Clean UI using Tailwind CSS

Scalable Flask backend using Blueprints

✨ Key Features

🔐 User Authentication (Login / Register)

📊 Dashboard for quick insights

🛠️ Equipment Management

📨 Maintenance Requests Tracking

👥 Team Management

🎨 Tailwind CSS based UI

🧩 Modular Flask Blueprints

🧱 Tech Stack
Layer Technology
Backend Python (Flask)
Frontend HTML, Tailwind CSS, JavaScript
Database SQLite
ORM SQLAlchemy
Styling Tailwind CSS
Tools Git, GitHub
Config Next.js & Tailwind Config (UI tooling)
📁 Project Structure
gearguard-maintenance-tracker1222/
│
├── app.py # Main Flask app
├── models.py # Database models
├── seed_data.py # Initial database data
├── requirements.txt # Python dependencies
├── README.md
│
├── routes/ # Flask Blueprints
│ ├── auth.py
│ ├── dashboard.py
│ ├── equipment.py
│ ├── requests.py
│ └── teams.py
│
├── templates/ # Jinja2 templates
│ ├── auth/
│ ├── dashboard/
│ ├── equipment/
│ ├── requests/
│ ├── teams/
│ └── base.html
│
├── static/
│ ├── css/
│ └── js/
│
├── app/ # UI related configs
│ ├── globals.css
│ └── layout.tsx
│
├── instance/ # Flask instance folder
├── venv/ # Virtual environment (ignored)
│
├── tailwind.config.js
├── next.config.js
└── tsconfig.json

