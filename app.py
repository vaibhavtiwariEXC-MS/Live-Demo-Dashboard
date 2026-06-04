import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Webinar Performance", layout="wide")
st.title("Webinar Performance Dashboard")

uploaded_file = st.file_uploader("Upload HubSpot Export (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("Data loaded successfully.")

    # 1. Standard Waterfall Funnel
    st.subheader("1. Standard Waterfall Funnel Metrics")
    
    # Count total registrations and attendances by splitting the multi-select date strings
    df['reg_count'] = df['Live Demo Registered'].dropna().apply(lambda x: len(str(x).split(',')))
    df['att_count'] = df['Live Demo Attended'].dropna().apply(lambda x: len(str(x).split(',')))
    
    total_registrants = df['reg_count'].sum()
    total_attendees = df['att_count'].sum()

    # Cumulative Pipeline Logic
    mql_stages = ['Marketing Qualified Lead', 'Sales Accepted Lead', 'Sales Qualified Lead', 'Opportunity', 'Customer', 'Customer - Lead', 'Customer - MQL', 'Customer - SAL', 'Customer - SQL', 'Customer - Opp']
    sal_stages = ['Sales Accepted Lead', 'Sales Qualified Lead', 'Opportunity', 'Customer', 'Customer - Lead', 'Customer - MQL', 'Customer - SAL', 'Customer - SQL', 'Customer - Opp']
    opp_stages = ['Opportunity', 'Customer', 'Customer - Lead', 'Customer - MQL', 'Customer - SAL', 'Customer - SQL', 'Customer - Opp']

    total_mqls = df['Lifecycle Stage'].isin(mql_stages).sum()
    total_sals = df['Lifecycle Stage'].isin(sal_stages).sum()
    total_opps = df['Lifecycle Stage'].isin(opp_stages).sum()

    funnel_data = dict(
        number=[total_registrants, total_attendees, total_mqls, total_sals, total_opps],
        stage=["Registrations", "Attendees", "MQLs", "SALs", "Opportunities"]
    )
    
    fig_funnel = px.funnel(funnel_data, x='number', y='stage')
    st.plotly_chart(fig_funnel, use_container_width=True)

    # 2. Promotion Channels & Volume
    st.subheader("2. Promotion Channels & Volume")
    webinars_run = st.number_input("Total Webinars Run", min_value=1, value=10)
    
    if 'Campaign Source1' in df.columns:
        # Explode the comma-separated campaign sources
        df_channels = df.copy()
        df_channels['Campaign Source1'] = df_channels['Campaign Source1'].astype(str).str.split(',')
        df_channels = df_channels.explode('Campaign Source1')
        df_channels['Campaign Source1'] = df_channels['Campaign Source1'].str.strip()
        
        channel_stats = df_channels.groupby('Campaign Source1').agg(
            Registrations=('reg_count', 'sum'),
            Attendees=('att_count', 'sum')
        ).reset_index()
        
        fig_channels = px.bar(
            channel_stats, 
            x='Campaign Source1', 
            y=['Registrations', 'Attendees'], 
            barmode='group',
            title="Registrations vs Attendance by Channel"
        )
        st.plotly_chart(fig_channels, use_container_width=True)

    # 3. Micro-Conversions & Engagement
    st.subheader("3. Micro-Conversions & Engagement")
    show_rate = (total_attendees / total_registrants * 100) if total_registrants > 0 else 0
    st.metric(label="Registration-to-Attendee Show Rate", value=f"{show_rate:.1f}%")

    # 4. Audience Segmentation & Quality
    st.subheader("4. Audience Segmentation & Quality")
    col1, col2, col3 = st.columns(3)

    # Net-new vs Existing
    df['Customer Status'] = df['Lifecycle Stage'].apply(lambda x: 'Existing' if 'Customer' in str(x) else 'Net-New')
    fig_status = px.pie(df, names='Customer Status', title='Net-New vs Existing')
    col1.plotly_chart(fig_status, use_container_width=True)

    # Persona / Job Title Logic
    def categorize_title(title):
        title = str(title).lower()
        if any(x in title for x in ['cio', 'vp', 'chief', 'director', 'head']):
            return 'Decision Maker'
        elif any(x in title for x in ['manager', 'specialist', 'procurement', 'admin']):
            return 'Gatekeeper/Evaluator'
        return 'Other'

    if 'Job Title' in df.columns:
        df['Persona'] = df['Job Title'].apply(categorize_title)
        fig_persona = px.pie(df, names='Persona', title='Persona Breakdown')
        col2.plotly_chart(fig_persona, use_container_width=True)

    # Company Size (FTE)
    if 'FTE' in df.columns:
        df['FTE'] = pd.to_numeric(df['FTE'], errors='coerce')
        bins = [0, 50, 200, 100000]
        labels = ['1-50', '51-200', '250+']
        df['Company Size'] = pd.cut(df['FTE'], bins=bins, labels=labels)
        fig_fte = px.pie(df, names='Company Size', title='Company Size (FTE)')
        col3.plotly_chart(fig_fte, use_container_width=True)

    # 5. Sales Follow-up (MQL to SAL Conversion by Month)
    st.subheader("5. Sales Follow-up Execution (March vs May)")
    date_col = 'Date entered "Marketing Qualified Lead (Lifecycle Stage Pipeline)"'
    
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Filter for March and May cohorts
        march_mqls = df[df[date_col].dt.month == 3]
        may_mqls = df[df[date_col].dt.month == 5]
        
        march_mql_count = len(march_mqls)
        may_mql_count = len(may_mqls)
        
        march_sal_count = march_mqls['Lifecycle Stage'].isin(sal_stages).sum()
        may_sal_count = may_mqls['Lifecycle Stage'].isin(sal_stages).sum()
        
        march_rate = (march_sal_count / march_mql_count * 100) if march_mql_count > 0 else 0
        may_rate = (may_sal_count / may_mql_count * 100) if may_mql_count > 0 else 0
        
        rate_data = pd.DataFrame({
            "Month": ["March", "May"],
            "MQLs Generated": [march_mql_count, may_mql_count],
            "Converted to SAL": [march_sal_count, may_sal_count],
            "Conversion Rate (%)": [march_rate, may_rate]
        })
        
        st.dataframe(rate_data)
        
        fig_rates = px.bar(rate_data, x="Month", y="Conversion Rate (%)", title="MQL to SAL Conversion Rate")
        st.plotly_chart(fig_rates, use_container_width=True)
    else:
        st.warning(f"Could not find the column: {date_col}")
