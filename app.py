import logging
import warnings
import streamlit as st
from login import login

logging.getLogger('streamlit').setLevel(logging.ERROR)


warnings.filterwarnings('ignore', category=DeprecationWarning)

def logout():
    # Clear session state and redirect to login
    st.session_state.clear()
    st.experimental_set_query_params(page="login")

def main():
    st.title("PTIS")

    # Initialize session state if not set
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    # Get the current page from query parameters
    query_params = st.experimental_get_query_params()
    page = query_params.get("page", ["login"])[0]

    if page == "login":
        if not st.session_state.logged_in:
            login()
        else:
            st.experimental_set_query_params(page="home")
    elif page == "home":
        if st.session_state.logged_in:
            st.sidebar.button("Logout", on_click=logout)  # Logout button in sidebar
            role = st.session_state.role
            if role == "client":
                import sprint_page
                sprint_page.display()
            elif role == "admin":
                import admin_page
                admin_page.main_admin()
            else:
                st.write("Role not recognized")
        else:
            st.experimental_set_query_params(page="login")
    else:
        st.experimental_set_query_params(page="login")

if __name__ == "__main__":
    main()
