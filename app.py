import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Webinar Performance", layout="wide")
st.title("Webinar Performance Dashboard")

uploaded_file = st.file_uploader("Upload HubSpot Export (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("Data loaded successfully.")

    # 1. Standard Waterfall Funnel Metrics (Updated for 4 Funnels)
    st.subheader("1. Standard Waterfall Funnel Metrics")
    
    # Define Customer Status first so we can split the cohorts
    df['Customer Status'] = df['Lifecycle Stage'].apply(lambda x: 'Existing' if 'Customer' in str(x) else 'Net-New')

    # Define known Registrants and Attendees (Filtering out nulls)
    df_registrants = df[df['Live Demo Registered'].notna() & (df['Live Demo Registered'] != '')]
    df_attendees = df[df['Live Demo Attended'].notna() & (df['Live Demo Attended'] != '')]

    # Split into Net-New and Customer DataFrames
    nn_reg = df_registrants[df_registrants['Customer Status'] == 'Net-New']
    cust_reg = df_registrants[df_registrants['Customer Status'] == 'Existing']
    
    nn_att = df_attendees[df_attendees['Customer Status'] == 'Net-New']
    cust_att = df_attendees[df_attendees['Customer Status'] == 'Existing']

    # Strictly enforced pipeline stages (Customers excluded from bottom of funnel)
    mql_stages = ['Marketing Qualified Lead', 'Sales Accepted Lead', 'Sales Qualified Lead', 'Opportunity']
    sal_stages = ['Sales Accepted Lead', 'Sales Qualified Lead', 'Opportunity']
    sql_stages = ['Sales Qualified Lead', 'Opportunity']
    opp_stages = ['Opportunity']

    # Helper function to generate funnel dataframe
    def build_funnel_df(cohort_df, base_label):
        total_count = len(cohort_df)
        mqls = cohort_df['Lifecycle Stage'].isin(mql_stages).sum()
        sals = cohort_df['Lifecycle Stage'].isin(sal_stages).sum()
        sqls = cohort_df['Lifecycle Stage'].isin(sql_stages).sum()
        opps = cohort_df['Lifecycle Stage'].isin(opp_stages).sum()
        
        return pd.DataFrame(dict(
            number=[total_count, mqls, sals, sqls, opps],
            stage=[base_label, "MQLs", "SALs", "SQLs", "Opportunities"]
        ))

    # Build the 4 dataframes
    df_funnel_nn_reg = build_funnel_df(nn_reg, "Registrants")
    df_funnel_nn_att = build_funnel_df(nn_att, "Attendees")
    df_funnel_cust_reg = build_funnel_df(cust_reg, "Registrants")
    df_funnel_cust_att = build_funnel_df(cust_att, "Attendees")

    # Plotting in a 2x2 grid
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    
    with col1:
        st.plotly_chart(px.funnel(df_funnel_nn_reg, x='number', y='stage', title="Net-New Registrants"), use_container_width=True)
    with col2:
        st.plotly_chart(px.funnel(df_funnel_nn_att, x='number', y='stage', title="Net-New Attendees"), use_container_width=True)
    with col3:
        st.plotly_chart(px.funnel(df_funnel_cust_reg, x='number', y='stage', title="Customer Registrants"), use_container_width=True)
    with col4:
        st.plotly_chart(px.funnel(df_funnel_cust_att, x='number', y='stage', title="Customer Attendees"), use_container_width=True)
    # 2. Promotion Channels & Volume
    st.subheader("2. Promotion Channels & Volume")
    webinars_run = st.number_input("Total Webinars Run", min_value=1, value=10)
    
    # Calculate volume of multi-select dates for channels and show rate
    df['reg_volume'] = df['Live Demo Registered'].dropna().apply(lambda x: len(str(x).split(',')))
    df['att_volume'] = df['Live Demo Attended'].dropna().apply(lambda x: len(str(x).split(',')))
    
    if 'Campaign Source1' in df.columns:
        df_channels = df.copy()
        df_channels['Campaign Source1'] = df_channels['Campaign Source1'].astype(str).str.split(',')
        df_channels = df_channels.explode('Campaign Source1')
        df_channels['Campaign Source1'] = df_channels['Campaign Source1'].str.strip()
        
        channel_stats = df_channels.groupby('Campaign Source1').agg(
            Registrations=('reg_volume', 'sum'),
            Attendees=('att_volume', 'sum')
        ).reset_index()
        
        fig_channels = px.bar(
            channel_stats, 
            x='Campaign Source1', 
            y=['Registrations', 'Attendees'], 
            barmode='group',
            title="Total Volumes by Channel"
        )
        st.plotly_chart(fig_channels, use_container_width=True)

    # 3. Micro-Conversions & Engagement
    st.subheader("3. Micro-Conversions & Engagement")
    total_reg_volume = df['reg_volume'].sum()
    total_att_volume = df['att_volume'].sum()
    show_rate = (total_att_volume / total_reg_volume * 100) if total_reg_volume > 0 else 0
    st.metric(label="Registration-to-Attendee Show Rate (Volume)", value=f"{show_rate:.1f}%")

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
