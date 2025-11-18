"""
Login Page with JWT Authentication
Includes login form, token generation, remember me, and password reset
"""
import streamlit as st
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict
import os


# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24


def render_login_page():
    """
    Renders the login page with authentication form.
    ISO 17025 compliance: Records all login attempts in audit trail.
    """
    # Custom CSS for login page
    st.markdown("""
        <style>
        .login-container {
            max-width: 450px;
            margin: 0 auto;
            padding: 2rem;
        }
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .login-logo {
            font-size: 4rem;
            margin-bottom: 1rem;
        }
        .login-title {
            color: #007bff;
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .login-subtitle {
            color: #6c757d;
            font-size: 1rem;
        }
        .compliance-badge {
            text-align: center;
            margin-top: 2rem;
            padding: 1rem;
            background-color: #f8f9fa;
            border-radius: 0.5rem;
        }
        .compliance-badge img {
            height: 40px;
            margin: 0 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Login container
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)

    # Header
    st.markdown("""
        <div class='login-header'>
            <div class='login-logo'>⚡</div>
            <h1 class='login-title'>PV Lab Portal</h1>
            <p class='login-subtitle'>Test Report Automation System</p>
        </div>
    """, unsafe_allow_html=True)

    # Login form
    with st.form("login_form", clear_on_submit=False):
        st.markdown("### Login")

        username = st.text_input(
            "Username",
            placeholder="Enter your username",
            key="login_username"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password"
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            remember_me = st.checkbox("Remember me", key="remember_me")

        with col2:
            st.markdown("<div style='text-align: right;'><a href='#' style='color: #007bff; text-decoration: none;'>Forgot password?</a></div>", unsafe_allow_html=True)

        submit_button = st.form_submit_button("Login", use_container_width=True, type="primary")

        if submit_button:
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                # Authenticate user
                user = authenticate_user(username, password)

                if user:
                    # Generate JWT token
                    token = generate_jwt_token(user, remember_me)

                    # Store in session state
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.session_state.token = token

                    if remember_me:
                        st.session_state.remember_token = token

                    # Record login in audit trail
                    record_login_attempt(username, success=True, user_id=user['id'])

                    st.success(f"Welcome back, {user['name']}!")
                    st.balloons()

                    # Redirect to home page
                    st.session_state.current_page = 'home'
                    st.rerun()
                else:
                    # Record failed login attempt
                    record_login_attempt(username, success=False)
                    st.error("Invalid username or password. Please try again.")

    # Additional information
    st.markdown("---")

    # Demo credentials info (remove in production)
    with st.expander("ℹ️ Demo Credentials", expanded=False):
        st.info("""
        **Demo Accounts:**
        - Admin: `admin` / `admin123`
        - Engineer: `engineer` / `eng123`
        - Reviewer: `reviewer` / `rev123`
        - Operator: `operator` / `op123`
        - Viewer: `viewer` / `view123`
        """)

    # Compliance badges
    st.markdown("""
        <div class='compliance-badge'>
            <p style='color: #6c757d; font-size: 0.9rem; margin-bottom: 0.5rem;'>
                <strong>Certified & Compliant</strong>
            </p>
            <p style='color: #6c757d; font-size: 0.8rem;'>
                ISO 17025 | ISO 9001 | NABL | ILAC | BIS
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Footer
    st.markdown("""
        <div style='text-align: center; margin-top: 3rem; color: #6c757d; font-size: 0.8rem;'>
            <p>© 2024 PV Test Lab. All rights reserved.</p>
            <p>Version 1.0.0 | <a href='#' style='color: #007bff;'>Privacy Policy</a> | <a href='#' style='color: #007bff;'>Terms of Service</a></p>
        </div>
    """, unsafe_allow_html=True)


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """
    Authenticates a user against the database.
    In production, this should query a database with hashed passwords.

    Args:
        username: User's username
        password: User's password (plain text)

    Returns:
        User dictionary if authenticated, None otherwise
    """
    # Demo user database (replace with actual database in production)
    demo_users = {
        'admin': {
            'id': 1,
            'username': 'admin',
            'password_hash': hash_password('admin123'),
            'name': 'Administrator',
            'email': 'admin@pvlab.com',
            'role': 'admin',
            'department': 'Administration',
            'active': True
        },
        'engineer': {
            'id': 2,
            'username': 'engineer',
            'password_hash': hash_password('eng123'),
            'name': 'Test Engineer',
            'email': 'engineer@pvlab.com',
            'role': 'engineer',
            'department': 'Testing',
            'active': True
        },
        'reviewer': {
            'id': 3,
            'username': 'reviewer',
            'password_hash': hash_password('rev123'),
            'name': 'Technical Reviewer',
            'email': 'reviewer@pvlab.com',
            'role': 'reviewer',
            'department': 'Quality Assurance',
            'active': True
        },
        'operator': {
            'id': 4,
            'username': 'operator',
            'password_hash': hash_password('op123'),
            'name': 'Lab Operator',
            'email': 'operator@pvlab.com',
            'role': 'operator',
            'department': 'Testing',
            'active': True
        },
        'viewer': {
            'id': 5,
            'username': 'viewer',
            'password_hash': hash_password('view123'),
            'name': 'Report Viewer',
            'email': 'viewer@pvlab.com',
            'role': 'viewer',
            'department': 'Management',
            'active': True
        }
    }

    # Get user from database
    user = demo_users.get(username)

    if not user:
        return None

    # Check if user is active
    if not user.get('active', False):
        return None

    # Verify password
    if verify_password(password, user['password_hash']):
        # Remove password hash before returning
        user_data = {k: v for k, v in user.items() if k != 'password_hash'}
        return user_data

    return None


def hash_password(password: str) -> str:
    """
    Hashes a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifies a password against a hash.

    Args:
        password: Plain text password
        password_hash: Hashed password

    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False


def generate_jwt_token(user: Dict, remember_me: bool = False) -> str:
    """
    Generates a JWT token for authenticated user.

    Args:
        user: User dictionary
        remember_me: Whether to extend token expiration

    Returns:
        JWT token string
    """
    # Set expiration
    if remember_me:
        expiration = datetime.utcnow() + timedelta(days=30)
    else:
        expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)

    # Create payload
    payload = {
        'user_id': user['id'],
        'username': user['username'],
        'role': user['role'],
        'email': user['email'],
        'exp': expiration,
        'iat': datetime.utcnow()
    }

    # Generate token
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return token


def verify_jwt_token(token: str) -> Optional[Dict]:
    """
    Verifies and decodes a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        st.error("Session expired. Please login again.")
        return None
    except jwt.InvalidTokenError:
        st.error("Invalid token. Please login again.")
        return None


def record_login_attempt(username: str, success: bool, user_id: Optional[int] = None):
    """
    Records login attempt in audit trail.
    ISO 17025 compliance requirement.

    Args:
        username: Username attempted
        success: Whether login was successful
        user_id: User ID if successful
    """
    # TODO: Implement actual audit trail logging to database
    # For now, just add to session state for demo
    if 'audit_trail' not in st.session_state:
        st.session_state.audit_trail = []

    audit_entry = {
        'timestamp': datetime.now(),
        'event_type': 'login_success' if success else 'login_failure',
        'username': username,
        'user_id': user_id,
        'ip_address': 'localhost',  # In production, get actual IP
        'user_agent': 'Streamlit',  # In production, get actual user agent
        'success': success
    }

    st.session_state.audit_trail.append(audit_entry)


def render_password_reset():
    """
    Renders the password reset form.
    """
    st.markdown("### Password Reset")

    with st.form("password_reset_form"):
        email = st.text_input("Email Address", placeholder="Enter your email")

        submit = st.form_submit_button("Send Reset Link", use_container_width=True)

        if submit:
            if not email:
                st.error("Please enter your email address.")
            else:
                # TODO: Implement actual password reset logic
                st.success("Password reset link sent to your email!")
                st.info("Please check your email for further instructions.")


def check_authentication() -> bool:
    """
    Checks if user is authenticated.

    Returns:
        True if authenticated, False otherwise
    """
    # Check if token exists in session state
    if 'token' in st.session_state:
        payload = verify_jwt_token(st.session_state.token)
        if payload:
            return True

    # Check remember me token
    if 'remember_token' in st.session_state:
        payload = verify_jwt_token(st.session_state.remember_token)
        if payload:
            # Restore session
            st.session_state.authenticated = True
            st.session_state.token = st.session_state.remember_token
            # TODO: Load full user data from database
            return True

    return False
