# Procure-to-Pay System

A Django-based purchase request and approval system with multi-level workflows and AI document processing.

## 🚀 Live Demo

**Frontend & Backend:** https://procure-to-pay-2hum.onrender.com/

**Admin Panel:** https://procure-to-pay-2hum.onrender.com/admin/

**Test Credentials:**
- Username: `admin`
- Password: `AdminPass2024!`

## 📋 Features

- ✅ Multi-level approval workflow (Level 1 & Level 2)
- ✅ Role-based access control (Staff, Approver L1/L2, Finance)
- ✅ Document processing (Proforma upload & extraction)
- ✅ Automatic Purchase Order generation
- ✅ Receipt validation against PO
- ✅ JWT authentication
- ✅ Responsive web interface

## 🏗️ Tech Stack

- **Backend:** Django 4.2, Django REST Framework
- **Frontend:** Vanilla JavaScript (ES6+)
- **Database:** PostgreSQL (production), SQLite (local dev)
- **Document Processing:** pdfplumber, pytesseract
- **Deployment:** Render
- **Containerization:** Docker, Docker Compose

## 🐳 Quick Start with Docker
```bash
# Clone repository
git clone https://github.com/christophembarushimana/procure-to-pay.git
cd procure-to-pay

# Build and run with Docker Compose
docker-compose up --build

# Create superuser (in new terminal)
docker-compose exec backend python manage.py createsuperuser

# Access application
# Frontend: http://localhost:8000
# Admin: http://localhost:8000/admin
# API: http://localhost:8000/api
```

## 📦 Manual Installation
```bash
# Backend setup
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# Access at http://localhost:8000
```

## 🔑 API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login (returns JWT token)
- `GET /api/auth/me/` - Get current user

### Purchase Requests
- `GET /api/requests/` - List requests (filtered by role)
- `POST /api/requests/` - Create request (Staff only)
- `GET /api/requests/{id}/` - View request details
- `PATCH /api/requests/{id}/approve/` - Approve request (Approvers)
- `PATCH /api/requests/{id}/reject/` - Reject request (Approvers)
- `POST /api/requests/{id}/submit_receipt/` - Submit receipt (Staff)

### Authentication
All API requests (except register/login) require JWT token:
```
Authorization: Bearer <your-token>
```

## 👥 User Roles

1. **Staff** - Create requests, upload proforma, submit receipts
2. **Approver Level 1** - First approval level
3. **Approver Level 2** - Final approval (triggers PO generation)
4. **Finance** - View all approved requests

## 📊 Approval Workflow

1. Staff creates request with proforma → Status: **PENDING**
2. Level 1 Approver reviews → Approve/Reject
3. Level 2 Approver reviews → Approve/Reject
4. On final approval → System generates **Purchase Order** automatically
5. Staff submits receipt → System validates against PO

## 🤖 AI Features

- **Proforma Processing:** Extracts vendor info, items, prices from PDF
- **PO Generation:** Auto-creates structured PO on final approval
- **Receipt Validation:** Compares receipt to PO, flags discrepancies

## 🗂️ Project Structure
```
procure-to-pay/
├── backend/
│   ├── api/                    # Main Django app
│   │   ├── models.py          # User, PurchaseRequest models
│   │   ├── views.py           # API endpoints
│   │   ├── serializers.py     # DRF serializers
│   │   └── document_processor.py  # PDF/AI processing
│   ├── procure_to_pay/        # Django project settings
│   ├── templates/             # Frontend HTML
│   ├── Dockerfile
│   ├── requirements.txt
│   └── manage.py
├── docker-compose.yml
└── README.md
```

## 🔒 Security Features

- JWT token authentication
- Role-based access control
- CSRF protection
- Password hashing
- File upload validation

## 🚀 Deployment

Deployed on Render with:
- Gunicorn WSGI server
- WhiteNoise for static files
- PostgreSQL database
- Automatic deployments from GitHub

## 📝 Environment Variables
```
SECRET_KEY=<django-secret-key>
DEBUG=False
ALLOWED_HOSTS=procure-to-pay-2hum.onrender.com
DATABASE_URL=postgresql://user:pass@host:port/db
```

## 🧪 Testing

Register test users with different roles to test the full workflow:

1. Register as **Staff** → Create request
2. Register as **Approver Level 1** → Approve request
3. Register as **Approver Level 2** → Final approval (generates PO)
4. Login as **Staff** → Submit receipt

## 📧 Contact

For issues or questions, contact the development team.

---

**Built for IST Africa Technical Assessment**