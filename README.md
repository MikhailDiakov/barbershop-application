# 💈 FastAPI Barbershop Backend

This is the backend for a modern **Barbershop Management System**, providing a full set of API endpoints for managing users, barbers, appointments, reviews, admin functions, and more.

Built with **FastAPI** and powered by modern technologies, the backend handles everything from user registration and authentication to AI-powered assistant support, performance monitoring, and logging.

---

## 🎯 What This Backend Can Do

### 👤 Users

- Register and log in
- Manage personal profile and password
- Reset password via SMS
- View their own appointments and reviews
- **Anonymous users can also browse barbers and available slots and book appointments without logging in**

### ✂️ Barbers

- Manage personal schedules
- Edit profile and upload avatar
- View appointments and availability

### 📅 Appointments

- Browse available barbers and slots
- Book an appointment
- View your booking history
- Browse available barbers and slots (with ratings and reviews)

### ⭐ Reviews

- Leave a review for a barber
- View your submitted reviews

### 🤖 AI Assistant

- Ask AI barber-related questions using `/ai-assistant/ask`

### 🛠 Admin Panel

Admins can:

- Manage users and promote them to barbers
- Manage barbers and their schedules
- Handle appointments and moderate reviews
- Upload/delete barber avatars

### 🧑‍💼 Superadmin Panel

Superadmins can:

- View and manage all admins
- Promote/demote users to/from admins
- Access a debug error route

---

## 🚀 Features

- ⚙️ **FastAPI** – Fast and async-ready web framework
- 🐘 **PostgreSQL** – Reliable and powerful relational database
- 🧵 **Celery** – Background task queue (used for sending SMS)
- 🧠 **OpenAI Assistant** – AI-powered assistant for barbershop-related queries
- 📲 **Twilio** – SMS service integration for password recovery and notifications
- 📦 **Redis** – Caching and task broker for Celery
- 🔒 **JWT Authentication** – Secure and stateless user login
- ☁️ **AWS S3** – Image upload and storage for barber profiles
- 📊 **Prometheus + Grafana** – Monitoring and visualization
- 🔍 **Elasticsearch + Kibana** – Logging and searching through logs
- 🧪 **Unit Testing** – Built with `pytest` and `unittest.mock`
- 📈 **Sentry** – Error tracking and alerting
- 📜 **Alembic** – Database migrations

---

## 📦 Requirements

- [Docker](https://www.docker.com/)

---

## ⚙️ Setup & Run

### 1. Clone the repository

```bash
git clone https://github.com/MikhailDiakov/barbershop-application.git
cd barbershop-application
```

### 2. Configure environment variables

Fill in your secrets in `.env.example`, then rename it:

```bash
cp .env.example .env
```

### 3. Build and run the application

```bash
docker-compose up --build
```

---

## 🧪 Running Tests

To run the test suite inside a Docker container:

```bash
docker-compose -f docker-compose.test.yml run --rm app_test
```

---

## 📍 Useful URLs

| Service            | URL                                                            | Description                          |
| ------------------ | -------------------------------------------------------------- | ------------------------------------ |
| FastAPI Backend    | [http://localhost:8000](http://localhost:8000)                 | Main API entry point                 |
| API Docs (Swagger) | [http://localhost:8000/docs](http://localhost:8000/docs/)      | Interactive API documentation        |
| Prometheus Metrics | [http://localhost:8000/metrics](http://localhost:8000/metrics) | Application metrics for Prometheus   |
| Prometheus UI      | [http://localhost:9090](http://localhost:9090/)                | Prometheus dashboard                 |
| Grafana            | [http://localhost:3000/login](http://localhost:3000/login)     | Metrics visualization and dashboards |
| Kibana             | [http://localhost:5601](http://localhost:5601)                 | Log visualization via Elasticsearch  |

---
