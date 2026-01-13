# Backend Project Setup Guide

This document explains how to set up the backend project on your local environment.

---

## Requirements

Before starting, make sure you have the following installed:

- Git  
- Python 3.10 or higher  
- Docker Desktop (for Redis)  

---

## 1. Install Git

If Git is not installed, download it from:  
https://git-scm.com/downloads

Verify installation:

```bash
git --version
```

## 2. Clone the Repository
Choose a directory and clone the repository

```bash
git clone <repository_url>
cd <repository_name>
```

## 3. Install Docker Desktop
Redis runs inside Docker. Install Docker Desktop from: https://www.docker.com/products/docker-desktop/

After installation, restart your computer.

Verify Docker with:
```
docker --version
```

## 4. Run Redis with Docker
Pull and start Redis:
```
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

and Verify that is running:
```
docker ps
```

You should see a container named redis.

## 5. Verify Redis is working
Check connectivity:
```
docker exec -it redis redis-cli ping
```

You should see a PONG output.

## 6. Install Python
Download Python from: https://www.python.org/downloads/

Verify installation:
```bash
python --version
```

## 7. Create a Virtual Environment
Create a virtual environment (venv)
```bash
python -m venv venv
```

## 8. Activate the Virtual Environment
### Windows
```
venv\Scripts\activate
```

### macOS / Linux
```
source venv/bin/activate
```

## 9. Install Project Dependencies
With the venv active:
```
pip install -r requirements.txt
```

## 10. Environmnet Variables
Create a .env file in the root of the backend project, for example:
```
FLASK_ENV=development
SECRET_KEY=your_secret_key_here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Mail
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_password
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_DEFAULT_SENDER=your_email@gmail.com

# Redis (password recovery)
REDIS_URL=redis://localhost:6379/0
PASSWORD_RESET_TTL_SECONDS=900
```

## 11. Run the Backend
Start the Flask Server with the venv active
```
py app.py
```


