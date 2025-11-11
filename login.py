import streamlit as st
import json
import bcrypt
import os
import re



USER_CREDENTIALS_FILE = "users.json"

def load_users():
    if not os.path.exists(USER_CREDENTIALS_FILE):
        with open(USER_CREDENTIALS_FILE, "w") as f:
            json.dump({}, f)
    with open(USER_CREDENTIALS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_CREDENTIALS_FILE, "w") as f:
        json.dump(users, f)

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def is_strong_password(password):
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    return re.match(pattern, password)

def main():
    st.set_page_config(page_title="Login | Deepfake Detector", page_icon="🔐")

    users = load_users()

    # Initialize auth mode
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "Login"

    # ---------- CSS ----------
    st.markdown("""
        <style>
            .stApp {
                background: url("https://images.unsplash.com/photo-1516117172878-fd2c41f4a759") no-repeat center center fixed;
                background-size: cover;
            }
            .auth-box {
                background-color: rgba(255, 255, 255, 0.1);
                padding: 2rem;
                border-radius: 20px;
                box-shadow: 0px 4px 30px rgba(0, 0, 0, 0.4);
                width: 400px;
                margin: auto;
            }
            .gradient-btn {
                background: linear-gradient(to right, #f43b47, #453a94);
                border: none;
                border-radius: 30px;
                padding: 10px 25px;
                font-size: 16px;
                color: white;
                width: 100%;
                margin-top: 20px;
            }
            .auth-toggle {
                display: flex;
                justify-content: center;
                margin-bottom: 20px;
            }
            .auth-toggle button {
                padding: 0.5rem 2rem;
                border: none;
                font-weight: bold;
                border-radius: 25px 0 0 25px;
                margin-right: 0.5rem;
            }
            .selected {
                background: linear-gradient(to right, #f43b47, #453a94);
                color: white;
            }
            .unselected {
                background: #eee;
                color: #333;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='auth-box'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;'>🔐 Video Deepfake Detector</h2>", unsafe_allow_html=True)

    # Toggle buttons (Streamlit-native)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login", use_container_width=True):
            st.session_state.auth_mode = "Login"
    with col2:
        if st.button("Register", use_container_width=True):
            st.session_state.auth_mode = "Register"

    st.markdown("---")

    # ---------- Login ----------
    if st.session_state.auth_mode == "Login":
        st.subheader("Login to your account")
        username = st.text_input("User ID", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
       # st.checkbox("Remember Password")

        if st.button("Log In", key="login_btn", use_container_width=True):
            if username in users and check_password(password, users[username]):
                st.success(f"Welcome, {username}!")
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.switch_page("pages/home.py")
            else:
                st.error("Invalid username or password.")

    # ---------- Register ----------
    elif st.session_state.auth_mode == "Register":
        st.subheader("Register a new account")
        new_username = st.text_input("User ID", key="reg_user")
        new_password = st.text_input("Password", type="password", key="reg_pass")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_conf")
        agree = st.checkbox("I agree to the terms & conditions")

        if st.button("Register", key="reg_btn", use_container_width=True):
            if not agree:
                st.warning("You must agree to the terms & conditions.")
            elif new_username in users:
                st.error("Username already exists.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif not is_strong_password(new_password):
                st.error("Password must be at least 8 characters long, include uppercase, lowercase, number, and special character.")
            else:
                users[new_username] = hash_password(new_password)
                save_users(users)
                st.success("Registration successful! You can now log in.")
                st.session_state.auth_mode = "Login"

    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
