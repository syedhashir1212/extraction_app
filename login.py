import logging
import os
import sys
import warnings
import streamlit as st

warnings.filterwarnings('ignore')
logging.getLogger('streamlit').setLevel(logging.ERROR)


# Dummy credentials
USERS = {
    "sp": {"password": "123", "role": "client"},
    "admin": {"password": "123", "role": "admin"},
}

def login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state.user = username
            st.session_state.role = USERS[username]["role"]
            st.session_state.logged_in = True
            st.experimental_set_query_params(page="home")
        else:
            st.error("Invalid username or password")