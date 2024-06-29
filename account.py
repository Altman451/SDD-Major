import streamlit as st
import firebase_admin
from getpass import getpass
from streamlit_extras.add_vertical_space import add_vertical_space
from firebase_admin import credentials
from firebase_admin import auth

# Intialize FireBase
if not firebase_admin._apps:
    cred = credentials.Certificate('financial-manager-63442-6e985cafc943.json') 
    firebase_admin.initialize_app(cred)

def page():     
        # Close sidebar
        no_sidebar=st.empty()
        add_vertical_space(5)
        change_title=st.empty()
        change_title.markdown("<h1 style='text-align: center; color: light green;'>Log In / Sign Up</h1>", unsafe_allow_html=True)
        add_vertical_space(5)
        
        # Check if username and email have been inputted
        if 'username' not in st.session_state:
            st.session_state.username = ''
        if 'useremail' not in st.session_state:
            st.session_state.useremail = ''

        # Logs user in
        def login():
            try:
                user=auth.get_user_by_email(email)
                st.session_state.username = user.uid
                st.session_state.useremail = user.email
                st.session_state.signedout = True
                st.session_state.signout = True
            except:
                st.warning('Login Failed')
        
        # Adds user details to list database
        def signup():
            try:
                user = auth.create_user(email = email, password=password, uid=username)
                login()
            except:
                st.warning('Sign Up Failed')
        
        # Clears session for user and disables access to website
        def sign_out():
            st.session_state.signout= False
            st.session_state.signedout = False 
            st.session_state.username = ''
            no_sidebar.empty()

        # Closes sidebar when app opens to prevent access from unwanted parties
        if 'signedout' not in st.session_state:
            st.session_state.signedout = False
        if 'signout' not in st.session_state:
            st.session_state.signout = False
        if not st.session_state['signedout']:
            no_sidebar.markdown(
                    """
                <style>
                    [data-testid="collapsedControl"] {
                        display: none
                    }
                </style>
                """,
                    unsafe_allow_html=True,
                )
            
            # Fields to fill out Log in/Sign up info
            username = st.text_input('Username (Optional If Logging In)', max_chars=64)
            email = st.text_input('Email', max_chars=320)
            password = st.text_input('Password', type='password', max_chars=128)
            add_vertical_space(5)
            columns = st.columns((5,7,7,5))
            with columns[1]:
                st.button('Log In', use_container_width=True, on_click=login)
            with columns[2]:
                st.button('Sign Up', use_container_width=True, on_click=signup)
        
        # Shows username and user email, provides button to sign out, and changes text
        if st.session_state.signout:
            change_title.markdown("<h1 style='text-align: center; color: light green;'>Welcome to your new finance manager</h1>", unsafe_allow_html=True)
            st.text('Name:'+st.session_state.username)
            st.text('Email:'+st.session_state.useremail)
            st.button('Sign Out', on_click=sign_out)