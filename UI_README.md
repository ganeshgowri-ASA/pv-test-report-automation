# PV Test Lab - Streamlit UI Application

World-class Photovoltaic (PV) test lab report automation system with production-ready Streamlit interface.

## 🚀 Features

### Authentication & Security
- ✅ JWT-based authentication with secure token management
- ✅ Role-based access control (RBAC)
- ✅ "Remember me" functionality
- ✅ Password reset workflow
- ✅ Session management with timeout
- ✅ ISO 17025 compliant audit trail

### User Roles
- **Admin**: Full system access, user management, system configuration
- **Engineer**: Test management, report generation, equipment calibration
- **Reviewer**: Review workflow, approve reports, audit trail access
- **Operator**: Test execution, data entry, equipment operation
- **Viewer**: Read-only access to reports and test results

### Navigation & UI
- 🎨 Custom branded theme
- 📱 Responsive design
- 🔍 Search functionality in sidebar
- 📊 Real-time dashboard with statistics
- 🔔 Notification system
- 👤 User profile menu
- 🍞 Breadcrumb navigation

### Main Dashboard
- Quick stats (active tests, pending reviews, reports generated)
- Recent activity feed
- Test statistics charts
- Upcoming tasks and deadlines
- System status indicators
- Standards compliance overview
- Quick action buttons

### Standards Coverage
- IEC 61215 (PV Module Design Qualification)
- IEC 61730 (PV Module Safety Qualification)
- IEC 61853 (PV Module Performance Testing)
- IEC 62716 (Ammonia Corrosion Testing)
- IEC 61701 (Salt Mist Corrosion Testing)
- IEC 62804 (Potential Induced Degradation)
- IEC 60904 (PV Device Performance)
- IEC 62759 (Transportation Testing)
- ISO 17025 (Laboratory Accreditation)
- ISO 9001 (Quality Management)

### Compliance Features
- ✅ Full audit trail for all user actions
- ✅ Equipment calibration tracking
- ✅ Traceability for test results
- ✅ Electronic signatures
- ✅ Data integrity validation
- ✅ NABL/ILAC compliance
- ✅ BIS certification support

## 📁 Project Structure

```
pv-test-report-automation/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── .streamlit/
│   └── config.toml                # Streamlit configuration & theme
├── src/
│   ├── __init__.py
│   └── ui/
│       ├── __init__.py
│       ├── components/             # Reusable UI components
│       │   ├── __init__.py
│       │   ├── navbar.py          # Top navigation bar
│       │   └── sidebar.py         # Sidebar navigation
│       └── pages/                  # Application pages
│           ├── __init__.py
│           ├── login.py           # Login & authentication
│           └── home.py            # Dashboard/home page
└── logs/                           # Application logs (auto-generated)
```

## 🛠️ Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager
- Virtual environment (recommended)

### Setup Steps

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/pv-test-report-automation.git
cd pv-test-report-automation
```

2. **Create virtual environment**
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run the application**
```bash
streamlit run app.py
```

6. **Access the application**
Open your browser and navigate to: `http://localhost:8501`

## 🔐 Demo Credentials

For testing purposes, use these demo accounts:

| Username   | Password  | Role     | Access Level                              |
|------------|-----------|----------|-------------------------------------------|
| admin      | admin123  | Admin    | Full system access                        |
| engineer   | eng123    | Engineer | Test management, report generation        |
| reviewer   | rev123    | Reviewer | Review workflow, approvals                |
| operator   | op123     | Operator | Test execution, data entry                |
| viewer     | view123   | Viewer   | Read-only access                          |

**⚠️ IMPORTANT**: Change these credentials in production!

## 🎨 Customization

### Theme Configuration
Edit `.streamlit/config.toml` to customize colors and appearance:

```toml
[theme]
primaryColor = "#007bff"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f8f9fa"
textColor = "#212529"
```

### Environment Variables
Configure application behavior in `.env`:

```bash
# JWT Secret (use strong random string in production)
JWT_SECRET=your-secret-key-change-in-production

# Database connection
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pvlab_db
```

## 📊 Key Components

### app.py
Main application entry point with:
- Page configuration
- Session state management
- Authentication flow
- Role-based page routing
- Error handling

### login.py
Authentication system with:
- JWT token generation
- Password hashing (bcrypt)
- Login/logout functionality
- Remember me feature
- Audit trail logging

### home.py
Dashboard page with:
- Quick statistics
- Recent activity feed
- Test statistics charts
- Upcoming tasks
- System status
- Standards compliance overview

### navbar.py
Top navigation with:
- User information display
- Notification bell with badge
- User menu dropdown
- Breadcrumb navigation

### sidebar.py
Collapsible sidebar with:
- Hierarchical menu structure
- Role-based visibility
- Search functionality
- System status indicator

## 🔒 Security Features

1. **Authentication**
   - JWT-based token authentication
   - Bcrypt password hashing
   - Session timeout
   - Secure cookie handling

2. **Authorization**
   - Role-based access control (RBAC)
   - Page-level permissions
   - Feature-level restrictions

3. **Audit Trail**
   - All user actions logged
   - Login/logout tracking
   - Data modification history
   - ISO 17025 compliance

4. **Data Protection**
   - Input validation
   - XSS protection
   - CSRF protection
   - SQL injection prevention

## 📈 Performance Optimizations

- `@st.cache_data` for expensive computations
- Lazy loading of components
- Optimized database queries
- Efficient session state management
- Minimal re-renders

## 🧪 Testing

Run tests with pytest:

```bash
pytest tests/ -v --cov=src
```

## 📝 Development Guidelines

### Adding New Pages

1. Create page file in `src/ui/pages/`:
```python
# src/ui/pages/my_page.py
def render_my_page():
    st.title("My Page")
    # Page content here
```

2. Import in `app.py`:
```python
from src.ui.pages.my_page import render_my_page
```

3. Add route in `render_page()`:
```python
elif page == 'my_page':
    render_my_page()
```

4. Add to sidebar menu in `sidebar.py`:
```python
{
    'name': 'My Page',
    'icon': '📄',
    'page': 'my_page',
    'roles': ['admin', 'engineer']
}
```

### Adding Components

Create reusable components in `src/ui/components/`:

```python
# src/ui/components/my_component.py
def render_my_component(param1, param2):
    # Component logic here
    pass
```

## 🚀 Deployment

### Production Checklist

- [ ] Change JWT secret in `.env`
- [ ] Update demo credentials
- [ ] Configure production database
- [ ] Set up HTTPS/SSL
- [ ] Configure email service
- [ ] Enable audit logging
- [ ] Set up backups
- [ ] Configure CORS
- [ ] Update environment to `production`
- [ ] Set `DEBUG=False`

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
```

Build and run:
```bash
docker build -t pvlab-ui .
docker run -p 8501:8501 pvlab-ui
```

## 📞 Support

- **Documentation**: [https://docs.pvlab.com](https://docs.pvlab.com)
- **Email**: support@pvlab.com
- **Issues**: [GitHub Issues](https://github.com/yourusername/pv-test-report-automation/issues)

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Icons from [Unicode Emoji](https://unicode.org/emoji/)
- Charts powered by [Plotly](https://plotly.com/)

## 🔄 Version History

### Version 1.0.0 (2024-11-18)
- ✅ Initial release
- ✅ Authentication system with JWT
- ✅ Role-based access control
- ✅ Dashboard with statistics
- ✅ Navigation components
- ✅ ISO 17025 audit trail integration
- ✅ Custom theme and branding

---

**© 2024 PV Test Lab. All rights reserved.**
