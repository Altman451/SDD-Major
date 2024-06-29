import streamlit as st
import pandas as pd
import altair as alt
import plotly.graph_objects as go
from streamlit_extras.add_vertical_space import add_vertical_space
import plotly.express as px
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import pandas as pd
import json

# Title and description
def page():
    db = firestore.client()
    user_uid = st.session_state.username
    user_ref = db.collection('users').document(user_uid)

    transactions_collection = user_ref.collection('transactions')
    assets_collection = user_ref.collection('assets')
    liabilities_collection = user_ref.collection('liabilities')

    # Failsafe put into place if the sidebar isnt closed while user is on log in/sign up page. Prevents access to dashboard entirely until user has logged in or signed up
    if st.session_state.signout:
        st.title('Business Cash Flow Analyzer')

        # Define categories for inflows, outflows, assets, and liabilities
        inflow_categories = ['Sales Revenue', 'Investment', 'Loan', 'Refund', 'Interest Income', 'Capital Injection']
        outflow_categories = ['Operating Expenses', 'Salaries and Wages', 'Rent', 'Utilities', 'Equipment Purchase', 'Taxes', 'Interest Expense', 'Loan Repayment', 'Marketing and Advertising', 'Cost of Goods Sold (COGS)']
        asset_categories = ['Current Asset', 'Non-Current Asset']
        liability_categories = ['Short-Term Liability', 'Long-Term Liability']

        @st.cache_resource
        def init_data():
            return {'transactions': [], 'assets': [], 'liabilities': [], 'total_cash': 0.0}

        state = init_data()

        @st.cache_resource
        def load_data():
            transactions = transactions_collection.stream()
            for transaction in transactions:
                state['transactions'].append(transaction.to_dict())

            assets = assets_collection.stream()
            for asset in assets:
                state['assets'].append(asset.to_dict())

            liabilities = liabilities_collection.stream()
            for liability in liabilities:
                state['liabilities'].append(liability.to_dict())

            # Calculate total cash
            total_cash = 0.0
            for transaction in state['transactions']:
                if transaction['Type'] == 'Incoming':
                    total_cash += transaction['Amount']
                elif transaction['Type'] == 'Outgoing':
                    total_cash -= transaction['Amount']
            state['total_cash'] = total_cash

        load_data()

        colradio, colcat, colfilter = st.columns([0.3, 0.4, 0.3])
        for i in range(6):
            st.write('')
        colfiller, colenterbutton, colfiller2 = st.columns([0.41, 0.18, 0.41])
        colradio.subheader('Enter Cash Transactions')
        st.markdown("""
        <style>
        [role=radiogroup]{
            gap: 4.2rem;
        }
        </style>
        """, unsafe_allow_html=True)
        transaction_type = colradio.radio(r"$\textsf{\Large Transaction Type:}$", ['Incoming', 'Outgoing', 'Asset', 'Liabilities'])

        # Provide Categories
        colcat.subheader('Provide Category, Amount, Month and Year')
        if transaction_type == 'Incoming':
            category = colcat.selectbox(r"$\textsf{\Large Category:}$", inflow_categories + ['Other'])
        elif transaction_type == 'Outgoing':
            category = colcat.selectbox(r"$\textsf{\Large Category:}$", outflow_categories + ['Other'])
        elif transaction_type == 'Asset':
            category = colcat.selectbox(r"$\textsf{\Large Category:}$", asset_categories)
        else:
            category = colcat.selectbox(r"$\textsf{\Large Category:}$", liability_categories)

        if category in ['Other', 'Other']:
            category = colcat.text_input('Enter custom category:', max_chars=50)
            if not category:
                colcat.warning('Please enter a category name.')

        # Select amount, month and year
        amount = colcat.number_input(r"$\textsf{\Large Amount:}$", min_value=0.01, step=0.01, format="%.2f")
        months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        selected_month = colcat.selectbox(r"$\textsf{\Large Select Month:}$", months)
        selected_year = colcat.number_input(r"$\textsf{\Large Select Year:}$", min_value=1994, max_value=9999, value=2023, step=1)

        # Updates values for every type of transaction
        @st.cache_data
        def update_transactions(transaction_type, category, amount, selected_month, selected_year, state):
            entry = {
                'Type': transaction_type,
                'Category': category,
                'Amount': amount,
                'Month': selected_month,
                'Year': selected_year
            }
            if transaction_type == 'Incoming':
                state['total_cash'] += amount
            elif transaction_type == 'Outgoing':
                state['total_cash'] -= amount

            if transaction_type == 'Asset':
                state['assets'].append(entry)
                assets_collection.add(entry)
            elif transaction_type == 'Liabilities':
                state['liabilities'].append(entry)
                liabilities_collection.add(entry)
            else:
                state['transactions'].append(entry)
                transactions_collection.add(entry)

            colcat.success('Transaction added successfully!')

        # Add transaction to dataframe
        if colenterbutton.button('Enter', use_container_width=True):
            update_transactions(transaction_type, category, amount, selected_month, selected_year, state)

        # Filters that allow user to select a specific graph or to change year
        colfilter.subheader('Filter Data by Year and Graph')
        filter_year = colfilter.number_input(r"$\textsf{\Large Select A Year To View:}$", min_value=1994, value=2023, step=1)
        selected_graph = colfilter.selectbox(r"$\textsf{\Large Pick A Specific Graph}$", ['All', 'Liquidity Ratio', 'Solvency Ratio', 'Debt Management Ratio', 'Top 5 Expenses', 'Profit Percentages', 'Cash Flow Chart', 'Revenue Line Graph', 'Profit Margin Chart'])
        
        # Graph descriptions
        graph_descriptions = {
            'Liquidity Ratio': "The liquidity ratio is a financial metric that measures a company's ability to meet its short-term obligations using its most liquid assets. A liquidity ratio in the red, ranging from 0 to 1, indicates that the company may struggle to cover its current liabilities, which can lead to financial distress, difficulty securing financing, and potential insolvency. Being in the yellow, with a ratio between 1 and 2, suggests the company has adequate liquidity to meet its short-term obligations but may face challenges if unexpected expenses arise or if there's a significant downturn in business. Companies in this range should monitor their cash flows closely to maintain stability. Finally, a liquidity ratio in the green, from 2 to 3, signifies strong financial health and robust liquidity, enabling the company to comfortably cover its liabilities, take advantage of investment opportunities, and weather economic fluctuations. This position often instills confidence in investors and creditors, potentially leading to more favorable borrowing terms and investment opportunities.",
            'Solvency Ratio': "The solvency ratio is a key financial metric that assesses a company's ability to meet its long-term debt obligations, reflecting its overall financial stability and sustainability. A solvency ratio in the red, either between 0-10 or 40-50, signals that the company is at high risk of financial instability or default. This situation can lead to severe consequences, including difficulty in securing long-term financing, loss of investor confidence, and potential bankruptcy. A solvency ratio in the yellow, ranging from 10-20 or 30-40, indicates moderate risk. Companies in this category have a reasonable ability to meet their long-term obligations but may face pressure during economic downturns or periods of financial stress. They need to manage their debt levels carefully and seek to improve their financial position. A solvency ratio in the green, between 20-30, signifies a strong financial position with a solid ability to meet long-term debts. Companies in this range are generally viewed as financially stable, capable of sustaining operations, and attractive to investors and creditors. This favorable position enables them to secure better financing terms, invest in growth opportunities, and confidently navigate economic fluctuations.",
            'Debt Management Ratio': "The debt management ratio, also known as the debt-to-equity ratio, evaluates a company's financial leverage by comparing its total debt to its equity. A ratio in the red, between 0-0.3, indicates that the company has very low leverage, suggesting it might not be fully utilizing debt to finance its growth. This conservative approach can limit the company's potential for expansion and its ability to take advantage of investment opportunities, though it does signify low financial risk. Being in the yellow, with a ratio between 0.3-0.6, implies a balanced approach to debt management. Companies in this range effectively use debt to fuel growth while maintaining manageable financial risk. They can attract investors and creditors with their balanced leverage, but they must monitor debt levels to ensure they do not overextend. A debt management ratio in the green, from 0.6-1, reflects optimal leverage, where the company maximizes growth opportunities through debt while maintaining strong financial health. Companies in this category are viewed as efficiently managing their debt, positioning themselves well for both expansion and financial stability. This favorable position typically leads to increased investor confidence and access to better financing options.",
            'Top 5 Expenses': "The top 5 expenses graph, depicted here as a pie chart, provides a clear visual representation of a company's largest expenditure categories. This graph helps stakeholders quickly identify where the bulk of the company's resources are being allocated, offering insights into operational priorities and potential areas for cost optimization. By highlighting the top five expenses, the graph can reveal whether spending is heavily concentrated in certain areas, such as payroll, rent, raw materials, marketing, or research and development. This information is crucial for financial planning and decision-making, as it allows management to assess whether the current allocation aligns with strategic goals and to identify opportunities for reducing costs or reallocating resources to support growth and efficiency. Regularly reviewing the top 5 expenses can also help in monitoring financial health, improving budget management, and ensuring that the company remains agile and responsive to changing economic conditions.",
            'Profit Percentages': "This chart tracks a company's profitability month by month, illustrating the percentage of revenue that translates into profit after all expenses and taxes are deducted. This visual representation allows stakeholders to easily observe trends in profitability over time, highlighting periods of growth, stability, or decline. Upward trends indicate healthy financial performance and efficient cost management, suggesting the company is consistently improving its profit margins. Conversely, downward trends or fluctuations may signal challenges such as increased costs, pricing pressures, or economic downturns affecting profitability. The chart also reveals seasonal variations or the impact of strategic initiatives on financial outcomes, providing valuable insights for decision-making. By regularly analyzing the profit percentage line chart, businesses can optimize financial strategies, allocate resources effectively, and adapt to market conditions to maintain and enhance profitability over the long term.",
            'Cash Flow Chart': "The 'Cash Flow Chart' visualizes the monthly inflows and outflows of cash within a business, providing a comprehensive overview of financial liquidity over time. It presents bars for both inflows and outflows categorized by months, allowing stakeholders to easily track and analyze cash movements. This chart is crucial for understanding the timing and magnitude of financial transactions, identifying peak periods of revenue generation, and assessing the impact of expenses on overall cash position. It facilitates strategic financial planning by highlighting trends, irregularities, and potential cash flow bottlenecks, helping businesses optimize resource allocation and maintain financial stability.",
            'Revenue Line Graph': "This graph tracks a company's income month by month, showcasing the total earnings generated over a specific period. Each point on the graph represents the revenue earned during a particular month, offering a visual depiction of sales performance and revenue trends over time. This graphical representation enables stakeholders to quickly assess the growth trajectory of the company's sales, identifying peak periods, seasonal fluctuations, or trends in customer demand. Upward trends indicate robust sales growth and market expansion, suggesting effective marketing strategies or product innovation. Conversely, downward trends or fluctuations may indicate challenges such as market saturation, economic downturns, or competitive pressures impacting revenue generation. By analyzing the revenue line graph regularly, businesses can make informed decisions about sales forecasts, resource allocation, and strategic planning to capitalize on growth opportunities and mitigate potential risks in the marketplace.",
            'Profit Margin Chart': "This profit margin chart displays both gross and net profit margins in months, offering a comprehensive view of a company's profitability dynamics. The chart visually represents the percentage of revenue retained as profit after deducting different levels of expenses. The gross profit margin, calculated as gross profit divided by revenue, reflects the profitability of core business operations before accounting for overhead costs. It illustrates the efficiency of production or service delivery and pricing strategies. The net profit margin, calculated as net profit divided by revenue, factors in all expenses including taxes and reflects overall profitability after all costs are accounted for. Trends in these margins over time provide insights into operational efficiency, pricing effectiveness, and financial health. Rising gross profit margins suggest improved efficiency in production or service delivery, while increasing net profit margins indicate effective cost management and revenue growth strategies. Declining margins may signal rising costs, pricing pressures, or economic challenges impacting profitability. Analyzing the profit margin chart helps businesses adjust strategies, optimize pricing, and manage costs to enhance profitability and sustain long-term financial health."
        }

        # Graph remedies
        graph_remedies = {
            'Liquidity Ratio': "Improving liquidity involves managing both current assets and liabilities effectively. First, streamline accounts receivable by incentivizing early payments from customers or tightening credit policies. Second, optimize inventory levels by forecasting demand more accurately and reducing slow-moving stock. Third, negotiate favorable terms with suppliers to extend payment deadlines without incurring penalties. Fourth, maintain a cash reserve for unexpected expenses or opportunities. Finally, regularly review and adjust your cash flow forecast to anticipate and address liquidity challenges proactively. By implementing these strategies, you can enhance liquidity and ensure your business has the necessary funds to operate smoothly.",
            'Solvency Ratio': "Improving solvency involves effectively managing both assets and liabilities. Start by analyzing your current financial position, including income streams, expenses, and debt obligations. Increase your income by exploring additional sources such as side gigs or investments that align with your skills and resources. Simultaneously, reduce unnecessary expenses by creating a budget and identifying areas where you can cut costs. Finally, prioritize debt repayment by focusing on high-interest loans first while maintaining a consistent payment schedule for all debts to steadily improve your financial health and solvency over time.",
            'Debt Management Ratio': "Debt management involves several key steps to regain control of your finances. Start by compiling a detailed list of all your debts, including amounts owed, interest rates, and minimum payments. Next, prioritize high-interest debts to pay off first, while making at least minimum payments on all others to avoid penalties. Consider consolidating debts with high interest rates into a lower-interest loan if possible. Finally, create a realistic budget to allocate funds towards debt repayment each month, and seek professional advice if needed to navigate complex financial situations. By following these steps consistently, you can effectively manage and eventually eliminate your debts.",
            'Top 5 Expenses': "To improve expenses, conduct a thorough analysis of current expenditures to identify areas where costs can be reduced or optimized. Implement a budgeting system that tracks expenses closely and sets clear spending limits for different departments or projects. Negotiate with vendors and suppliers for better pricing or discounts based on bulk purchases or long-term contracts. Encourage a culture of cost-consciousness among employees by promoting efficiency and minimizing wastage. Regularly review and adjust expense management strategies to adapt to changing market conditions and business needs.",
            'Profit Percentages': "Analyzing profit percentages involves evaluating revenue streams and cost structures to enhance profitability. Start by identifying the most profitable products or services and allocating resources accordingly. Implement pricing strategies that maximize profit margins without compromising competitiveness. Monitor and manage variable costs such as materials, labor, and distribution to optimize profit margins. Additionally, explore opportunities for revenue diversification or cost-saving initiatives to improve overall profitability. Regularly reviewing and adjusting profit strategies based on market trends and financial performance will help sustain and grow profitability over time.",
            'Cash Flow Chart': "To optimize cash flow, focus on accelerating receivables by offering incentives for early payments and tightening credit terms where appropriate. Manage payables by negotiating extended terms with suppliers without penalties to preserve cash. Forecast cash needs and maintain adequate reserves to cover operational expenses during lean periods. Continuously monitor cash flow patterns and adjust forecasts based on actual performance to proactively manage liquidity. Implementing effective cash flow management ensures stability and flexibility in financial operations, supporting sustainable business growth and resilience.",
            'Revenue Line Graph': "Maximizing revenue involves strategic planning and execution to drive sales growth. Identify high-demand products or services and allocate resources to capitalize on market opportunities. Implement targeted marketing campaigns to attract and retain customers, leveraging customer insights and feedback for product innovation. Diversify revenue streams by exploring new markets or expanding product lines to mitigate risk and capture additional growth opportunities. Regularly analyze sales trends and adjust strategies to optimize revenue generation and maintain competitive advantage in the marketplace.",
            'Profit Margin Chart': "Improving profit margins requires a focus on operational efficiency and cost management. Streamline production processes to reduce variable costs and improve productivity. Negotiate better terms with suppliers to lower procurement costs without compromising quality. Implement pricing strategies that align with market demand and maximize profitability. Monitor and analyze gross and net profit margins regularly to identify areas for improvement and adjust pricing or cost structures accordingly. Enhancing profit margins enhances overall profitability and strengthens financial health, positioning the business for sustained growth and success."
        }

        # Display transactions table and cash balance
        if state['transactions'] or state['assets'] or state['liabilities']:
            df_transactions = pd.DataFrame(state['transactions'], columns=['Type', 'Category', 'Amount', 'Month', 'Year'])
            df_assets = pd.DataFrame(state['assets'], columns=['Type', 'Category', 'Amount', 'Month', 'Year'])
            df_liabilities = pd.DataFrame(state['liabilities'], columns=['Type', 'Category', 'Amount', 'Month', 'Year'])

            df_transactions = df_transactions[df_transactions['Year'] == filter_year]
            df_assets = df_assets[df_assets['Year'] == filter_year]
            df_liabilities = df_liabilities[df_liabilities['Year'] == filter_year]

            if df_transactions.empty and df_assets.empty and df_liabilities.empty:
                st.warning('No data available for the selected year. Please select a different year or input data for this year.')
            else:

                # Calculate total incoming and outgoing
                total_incoming = df_transactions[df_transactions['Type'] == 'Incoming']['Amount'].sum()
                total_outgoing = df_transactions[df_transactions['Type'] == 'Outgoing']['Amount'].sum()

                # Calculate current assets and current liabilities
                current_assets = df_assets[df_assets['Category'] == 'Current Asset']['Amount'].sum()
                current_liabilities = df_liabilities[df_liabilities['Category'] == 'Short-Term Liability']['Amount'].sum()
                # Calculate long-term liabilities
                total_liabilities = df_liabilities['Amount'].sum()
                
                # Calculate liquidity ratio
                liquidity_ratio = current_assets / current_liabilities if current_liabilities > 0 else float('inf')

                # Calculate solvency ratio
                net_income = total_incoming - total_outgoing
                solvency_ratio = (net_income / total_liabilities) * 100 if total_liabilities > 0 else float('inf')

                # Calculate total assets
                total_assets = df_assets['Amount'].sum()

                # Calculate debt management ratio (Debt-to-Asset Ratio)
                debt_management_ratio = total_liabilities / total_assets if total_assets > 0 else 0
                
                # Display selected graph(s)
                if selected_graph == 'All' or selected_graph in graph_descriptions and graph_remedies:
                    st.subheader(selected_graph)
                    col1,col2= st.columns([0.5,0.5])
                    col3,col4 = st.columns([0.5,0.5])
                    col5, col6 = st.columns([0.5,0.5])
                    col7, col8 = st.columns([0.5,0.5])
                    
                    # Makes sure that text and chart are side-by-side and don't overlap
                    if selected_graph in graph_descriptions:
                        if selected_graph == 'Liquidity Ratio':
                            col2.write(graph_descriptions[selected_graph])
                            add_vertical_space(5)
                            col2.write(graph_remedies[selected_graph])
                        
                        if selected_graph == 'Solvency Ratio':
                            col1.write(graph_descriptions[selected_graph])
                            add_vertical_space(5)
                            col1.write(graph_remedies[selected_graph])
                        
                        if selected_graph == 'Debt Management Ratio':
                            col4.write(graph_descriptions[selected_graph])
                            add_vertical_space(5)
                            col4.write(graph_remedies[selected_graph])
                        
                        if selected_graph == 'Top 5 Expenses':
                            col3.write(graph_descriptions[selected_graph])
                            add_vertical_space(5)
                            col3.write(graph_remedies[selected_graph])
                        
                        if selected_graph == 'Profit Percentages':
                            col8.write(graph_descriptions[selected_graph])
                            add_vertical_space(5)
                            col8.write(graph_remedies[selected_graph])

                        if selected_graph == 'Cash Flow Chart':
                            col6.write(graph_descriptions[selected_graph])
                            add_vertical_space(5)
                            col6.write(graph_remedies[selected_graph])

                        if selected_graph == 'Revenue Line Graph':
                            col7.write(graph_descriptions[selected_graph])
                            add_vertical_space(5)
                            col7.write(graph_remedies[selected_graph])

                        if selected_graph == 'Profit Margin Chart':
                            col5.write(graph_descriptions[selected_graph])
                            add_vertical_space(5)
                            col5.write(graph_remedies[selected_graph])

                    if selected_graph == 'All' or selected_graph == 'Liquidity Ratio':
                        # Display liquidity ratio only if data is sufficient
                        if current_liabilities > 0:

                            # Create gauge chart for liquidity ratio only if there is sufficient data
                            fig_liquidity = go.Figure(go.Indicator(
                                mode="gauge+number",
                                value=liquidity_ratio,
                                title={'text': "Liquidity Ratio"},
                                gauge={
                                    'axis': {'range': [0, 3]},
                                    'bar': {'color': "#000053"},
                                    'steps': [
                                        {'range': [0, 1], 'color': "#FF474C"},
                                        {'range': [1, 2], 'color': "#fffd8d"},
                                        {'range': [2, 3], 'color': "#6FC276"}
                                    ],
                                }
                            ))
                            col1.plotly_chart(fig_liquidity)

                        else:
                            col1.warning('Insufficient data to display Liquidity Ratio. Please add more assets and/or liabilities.')

                    if selected_graph == 'All' or selected_graph == 'Solvency Ratio':
                        # Display solvency ratio only if data is sufficient
                        if total_liabilities > 0:

                            # Create gauge chart for solvency ratio only if there is sufficient data
                            fig_solvency = go.Figure(go.Indicator(
                                mode="gauge+number",
                                value=solvency_ratio,
                                title={'text': "Solvency Ratio"},
                                gauge={
                                    'axis': {'range': [0, 50]},
                                    'bar': {'color': "#000053"},
                                    'steps': [
                                        {'range': [0, 10], 'color': "#FF474C"},
                                        {'range': [10, 20], 'color': "#fffd8d"},
                                        {'range': [20, 30], 'color': "#6FC276"},
                                        {'range': [30, 40], 'color': "#fffd8d"},
                                        {'range': [40, 50], 'color': "#FF474C"}
                                    ],
                                }
                            ))
                            col2.plotly_chart(fig_solvency)

                        else:
                            col2.warning('Insufficient data to display Solvency Ratio. Please add more assets and/or liabilities.')

                    if selected_graph == 'All' or selected_graph == 'Debt Management Ratio':
                        # Display debt management ratio only if data is sufficient
                        if total_assets > 0:

                            # Create gauge chart for debt management ratio only if there is sufficient data
                            fig_debt_management = go.Figure(go.Indicator(
                                mode="gauge+number",
                                value=debt_management_ratio,
                                title={'text': "Debt Management Ratio"},
                                gauge={
                                    'axis': {'range': [0, 1]},
                                    'bar': {'color': "#000053"},
                                    'steps': [
                                        {'range': [0, 0.3], 'color': "#FF474C"},
                                        {'range': [0.3, 0.6], 'color': "#fffd8d"},
                                        {'range': [0.6, 1], 'color': "#6FC276"}
                                    ],
                                }
                            ))
                            col3.plotly_chart(fig_debt_management)

                        else:
                            col3.warning('Insufficient data to display Debt Management Ratio. Please add more assets and/or liabilities.')

                    # Display top 5 expenses by category only if there are sufficient outflow transactions
                    if selected_graph == 'All' or selected_graph == 'Top 5 Expenses':
                        if len(df_transactions[df_transactions['Type'] == 'Outgoing']) >= 5:
                            top_expenses = df_transactions[df_transactions['Type'] == 'Outgoing'].groupby('Category')['Amount'].sum().nlargest(5)
                            
                            # Create pie chart for top 5 expenses by category
                            fig_expenses = go.Figure(data=[go.Pie(labels=top_expenses.index, values=top_expenses.values, hole=0.3)])
                            fig_expenses.update_layout(title='Top 5 Expenses by Category')
                            col4.plotly_chart(fig_expenses)
                        else:
                            col4.warning('Insufficient data to display Top 5 Expenses. Please add more outgoing transactions.')

                    # Display profit percentages and cash flow only if there are both inflow and outflow transactions
                    if selected_graph == 'All' or selected_graph == 'Profit Percentages' or selected_graph == 'Revenue Line Graph' or selected_graph == 'Profit Margin Chart' or selected_graph == 'Cash Flow Chart':
                        has_inflow = not df_transactions[df_transactions['Type'] == 'Incoming'].empty
                        has_outflow = not df_transactions[df_transactions['Type'] == 'Outgoing'].empty
                        if has_inflow and has_outflow:
                            # Prepare data for profit percentages
                            if 'Sales Revenue' in df_transactions['Category'].unique():
                                profit_percentages = []
                                months_with_transactions = set()

                                for month in months:
                                    sales_revenue = df_transactions[(df_transactions['Category'] == 'Sales Revenue') & (df_transactions['Month'] == month)]['Amount'].sum()
                                    outflows = df_transactions[df_transactions['Type'] == 'Outgoing'].groupby('Month')['Amount'].sum().get(month, 0)
                                    if sales_revenue > 0 and outflows > 0:
                                        profit_percentage = ((sales_revenue - outflows) / outflows) * 100
                                        profit_percentages.append({'Month': month, 'Profit Percentage': profit_percentage})
                                        months_with_transactions.add(month)

                                # Display profit percentages
                                if profit_percentages:
                                    # Create DataFrame for profit percentages
                                    df_profit_percentages = pd.DataFrame(profit_percentages)

                                    # Create line chart for profit percentages only if there are at least two months with transactions
                                    if len(months_with_transactions) >= 1 and (selected_graph == 'All' or selected_graph == 'Profit Percentages'):
                                        chart_profit_percentage = alt.Chart(df_profit_percentages).mark_line(point=True).encode(
                                            x=alt.X('Month:O', axis=alt.Axis(title='Month'), sort=months),
                                            y=alt.Y('Profit Percentage:Q', axis=alt.Axis(title='Profit Percentage (%)')),
                                            tooltip=['Month', alt.Tooltip('Profit Percentage:Q', format='.2f')]
                                        ).properties(
                                            title='Profit Percentage Over Months'
                                        )

                                        # Display line chart
                                        col7.altair_chart(chart_profit_percentage, use_container_width=True)

                            # Prepare data for inflows and outflows charts
                            df_inflows = df_transactions[df_transactions['Type'] == 'Incoming'].groupby(['Month', 'Year']).sum().reset_index()
                            df_outflows = df_transactions[df_transactions['Type'] == 'Outgoing'].groupby(['Month', 'Year']).sum().reset_index()

                            if selected_graph == 'All' or selected_graph == 'Revenue Line Graph':
                                # Create revenue line graph only if there is sales revenue data
                                df_sales_revenue = df_transactions[(df_transactions['Category'] == 'Sales Revenue')].groupby(['Month', 'Year']).sum().reset_index()

                                if not df_sales_revenue.empty:
                                    revenue_chart = alt.Chart(df_sales_revenue).mark_line(point=True).encode(
                                        x=alt.X('Month:O', axis=alt.Axis(title='Month-Year'), sort=months),
                                        y=alt.Y('Amount:Q', axis=alt.Axis(title='Revenue ($)')),
                                        tooltip=['Month', 'Year', 'Amount']
                                    ).properties(
                                        title='Monthly Sales Revenue'
                                    )
                                    col8.altair_chart(revenue_chart, use_container_width=True)
                            
                            if selected_graph == 'Cash Flow Chart' or selected_graph == 'All':
                                # Create a cash flow chart is there is enough cash flow data
                                if not df_transactions.empty:
                                    df_inflows['Flow'] = 'Inflows'
                                    df_outflows['Flow'] = 'Outflows'
                                    cash_flow = pd.concat([df_inflows, df_outflows], ignore_index=True)

                                    # Sort by month
                                    cash_flow['Month'] = pd.Categorical(cash_flow['Month'], categories=months, ordered=True)
                                    cash_flow = cash_flow.sort_values('Month')

                                    fig = go.Figure(data=[
                                        go.Bar(name='Inflows', x=cash_flow[cash_flow['Flow'] == 'Inflows']['Month'], y=cash_flow[cash_flow['Flow'] == 'Inflows']['Amount'], marker_color='#6FC276'),
                                        go.Bar(name='Outflows', x=cash_flow[cash_flow['Flow'] == 'Outflows']['Month'], y=cash_flow[cash_flow['Flow'] == 'Outflows']['Amount'], marker_color='#FF474C')
                                    ])

                                    # Update the layout
                                    fig.update_layout(
                                        barmode='group',
                                        title='Total Inflows and Outflows',
                                        xaxis_title='Month',
                                        yaxis_title='Amount',
                                        legend_title='Type'
                                    )
                                    col5.plotly_chart(fig, use_container_width=True)

                            if selected_graph == 'All' or selected_graph == 'Profit Margin Chart':
                                # Calculate gross profit margin and net profit margin only if there is sales revenue data
                                if 'Sales Revenue' in df_transactions['Category'].unique():
                                    gross_profit_margins = []
                                    net_profit_margins = []
                                    for month in months:
                                        sales_revenue = df_transactions[(df_transactions['Category'] == 'Sales Revenue') & (df_transactions['Month'] == month)]['Amount'].sum()
                                        cost_of_goods_sold = df_transactions[(df_transactions['Category'] == 'Cost of Goods Sold (COGS)') & (df_transactions['Month'] == month)]['Amount'].sum()
                                        total_outflows = df_transactions[(df_transactions['Type'] == 'Outgoing') & (df_transactions['Month'] == month)]['Amount'].sum()
                                        
                                        if sales_revenue > 0:
                                            gross_profit_margin = ((sales_revenue - cost_of_goods_sold) / sales_revenue) * 100
                                            net_profit_margin = ((sales_revenue - total_outflows) / sales_revenue) * 100
                                            gross_profit_margins.append({'Month': month, 'Gross Profit Margin': gross_profit_margin})
                                            net_profit_margins.append({'Month': month, 'Net Profit Margin': net_profit_margin})

                                    # Create DataFrame for profit margins
                                    df_gross_profit_margins = pd.DataFrame(gross_profit_margins)
                                    df_net_profit_margins = pd.DataFrame(net_profit_margins)

                                    # Create line charts for gross and net profit margins using Plotly only if there are sufficient data
                                    if not df_gross_profit_margins.empty and not df_net_profit_margins.empty and (selected_graph == 'All' or selected_graph == 'Profit Margin Chart'):
                                        fig_profit_margins = go.Figure()
                                        
                                        fig_profit_margins.add_trace(go.Scatter(
                                            x=df_gross_profit_margins['Month'],
                                            y=df_gross_profit_margins['Gross Profit Margin'],
                                            mode='lines+markers',
                                            name='Gross Profit Margin'
                                        ))
                                        
                                        fig_profit_margins.add_trace(go.Scatter(
                                            x=df_net_profit_margins['Month'],
                                            y=df_net_profit_margins['Net Profit Margin'],
                                            mode='lines+markers',
                                            name='Net Profit Margin'
                                        ))

                                        fig_profit_margins.update_layout(
                                            title='Gross and Net Profit Margins Over Months',
                                            xaxis_title='Month',
                                            yaxis_title='Profit Margin (%)'
                                        )
                                        col6.plotly_chart(fig_profit_margins, use_container_width=True)

                        else:
                            st.warning('Insufficient data to display Profit Percentages, Revenue Line Graph, or Profit Margin Chart. Please add both incoming and outgoing transactions.')
                    
                    if selected_graph == 'All':
                        # Shows dataframe themselves if user wants to download their raw financial data or add it to an existing spreadsheet
                        st.subheader('Download Your Data')
                        colfak, col9, colfak2, col10 = st.columns([0.1,0.4,0.15,0.35])
                        if not df_transactions.empty:
                            col9.write('Financial Flows')
                            col9.write(df_transactions)

                        if not df_assets.empty:
                            col10.write('Assets')
                            col10.write(df_assets)

                        if not df_liabilities.empty:
                            col10.write('Liabilities')
                            col10.write(df_liabilities)

        else:
            st.info('Add transactions above to see summary.')
            st.write(f'Current Net Cash Balance: ${state["total_cash"]:.2f}')
    
    else:
        st.warning("Please log in or sign up to access this page")