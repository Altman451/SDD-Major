import streamlit as st
import account, testing_2
from streamlit_option_menu import option_menu

# Closes sidebar when opening app
st.set_page_config(page_title='Finance Dashboard', page_icon =':money_with_wings:',initial_sidebar_state="collapsed",layout='wide')

# Sets class for multiple pages (this case being dashboard and account)
class MultiPage:

    def __init__(self):
        self.page=[]
        
    def add_page(self, title, func):
        self.page.append({'title': title, 'function': func})
        
    def run():
        # Options provided in sidebar
        with st.sidebar:
            page = option_menu(
                menu_title = 'Menu',
                options = ['Home', 'Account'],
                icons = ['house-fill','person-circle','info-circle-fill'],
                menu_icon='three-dots-vertical',
                default_index=1,
                styles={
                        "container": {"padding": "5!important","background-color":''},
            "icon": {"color": "white", "font-size": "23px"}, 
            "nav-link": {"color":"white","font-size": "20px", "text-align": "left", "margin":"0px", "--hover-color": "#282434"},
            "nav-link-selected": {"background-color": "#282434"},
                    }
                )
            
        if page == 'Home':
                testing_2.page()
        if page == 'Account':
                account.page()
    run()