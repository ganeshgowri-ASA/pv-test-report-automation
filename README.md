# PV Test Report Automation System

World-class PV (Photovoltaic) test lab report automation system covering IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759, ISO 17025, ISO 9001, NABL, ILAC, BIS standards with full traceability, reviewer workflows, LLM integration, and multi-format export capabilities.

## 🚀 Quick Start

### Run the Streamlit UI Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

Access the application at: `http://localhost:8501`

**Demo Credentials:**
- Admin: `admin` / `admin123`
- Engineer: `engineer` / `eng123`
- Reviewer: `reviewer` / `rev123`

## 📁 Project Structure

```
pv-test-report-automation/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── UI_README.md               # Detailed UI documentation
├── .streamlit/                # Streamlit configuration
│   └── config.toml
└── src/
    └── ui/
        ├── components/        # UI components (navbar, sidebar)
        └── pages/            # Application pages (login, home)
```

## ✨ Features

- ✅ **Authentication**: JWT-based authentication with role-based access control
- ✅ **Dashboard**: Real-time statistics, activity feed, and quick actions
- ✅ **Navigation**: Intuitive sidebar and breadcrumb navigation
- ✅ **Role-Based Access**: Admin, Engineer, Reviewer, Operator, Viewer roles
- ✅ **ISO 17025 Compliance**: Full audit trail and traceability
- ✅ **Responsive Design**: Modern UI with custom branding

## 📖 Documentation

See [UI_README.md](UI_README.md) for detailed documentation on:
- Installation and setup
- User roles and permissions
- Development guidelines
- Deployment instructions
- API documentation

## 🔐 Security

- JWT token authentication
- Bcrypt password hashing
- Role-based access control (RBAC)
- Session management
- Audit trail logging

## 📊 Standards Compliance

- IEC 61215, 61730, 61853, 62716, 61701, 62804, 60904, 62759
- ISO 17025, ISO 9001
- NABL, ILAC, BIS certification support

## 📄 License

MIT License - see LICENSE file for details
