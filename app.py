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

    # 1. Standard Waterfall Funnel Metrics (Updated for Customer Stages)
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

    # Strictly enforced pipeline stages for Net-New
    nn_mql_stages = ['Marketing Qualified Lead', 'Sales Accepted Lead', 'Sales Qualified Lead', 'Opportunity']
    nn_sal_stages = ['Sales Accepted Lead', 'Sales Qualified Lead', 'Opportunity']
    nn_sql_stages = ['Sales Qualified Lead', 'Opportunity']
    nn_opp_stages = ['Opportunity']

    # Strictly enforced pipeline stages for Existing Customers
    cust_mql_stages = ['Customer - MQL', 'Customer - SAL', 'Customer - SQL', 'Customer - Opp']
    cust_sal_stages = ['Customer - SAL', 'Customer - SQL', 'Customer - Opp']
    cust_sql_stages = ['Customer - SQL', 'Customer - Opp']
    cust_opp_stages = ['Customer - Opp']

    # Helper function to generate funnel dataframe with custom stage lists
    def build_funnel_df(cohort_df, base_label, mql_list, sal_list, sql_list, opp_list):
        total_count = len(cohort_df)
        mqls = cohort_df['Lifecycle Stage'].isin(mql_list).sum()
        sals = cohort_df['Lifecycle Stage'].isin(sal_list).sum()
        sqls = cohort_df['Lifecycle Stage'].isin(sql_list).sum()
        opps = cohort_df['Lifecycle Stage'].isin(opp_list).sum()
        
        return pd.DataFrame(dict(
            number=[total_count, mqls, sals, sqls, opps],
            stage=[base_label, "MQLs", "SALs", "SQLs", "Opportunities"]
        ))

    # Build the 4 dataframes passing the correct stage lists
    df_funnel_nn_reg = build_funnel_df(nn_reg, "Registrants", nn_mql_stages, nn_sal_stages, nn_sql_stages, nn_opp_stages)
    df_funnel_nn_att = build_funnel_df(nn_att, "Attendees", nn_mql_stages, nn_sal_stages, nn_sql_stages, nn_opp_stages)
    
    df_funnel_cust_reg = build_funnel_df(cust_reg, "Registrants", cust_mql_stages, cust_sal_stages, cust_sql_stages, cust_opp_stages)
    df_funnel_cust_att = build_funnel_df(cust_att, "Attendees", cust_mql_stages, cust_sal_stages, cust_sql_stages, cust_opp_stages)

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
        
    # 2. Promotion Channels & Volume (Updated for Static Webinar Count)
    st.subheader("2. Promotion Channels & Volume")
    
    webinars_run = 17
    st.metric(label="Total Webinars Run", value=webinars_run)
    
    # Calculate volume of multi-select dates for channels
    df['reg_volume'] = df['Live Demo Registered'].dropna().apply(lambda x: len(str(x).split(',')))
    df['att_volume'] = df['Live Demo Attended'].dropna().apply(lambda x: len(str(x).split(',')))
    
    if 'Campaign Source1' in df.columns:
        df_channels = df.copy()
        
        # Standardize delimiters (replace semicolons with commas) and split
        df_channels['Campaign Source1'] = df_channels['Campaign Source1'].astype(str).str.replace(';', ',').str.split(',')
        
        # Calculate the weight for fractional attribution
        df_channels['campaign_count'] = df_channels['Campaign Source1'].apply(lambda x: len(x) if isinstance(x, list) else 1)
        
        # Apply the fractional weight to volumes
        df_channels['reg_weighted'] = df_channels['reg_volume'] / df_channels['campaign_count']
        df_channels['att_weighted'] = df_channels['att_volume'] / df_channels['campaign_count']
        
        # Explode the lists into individual rows
        df_channels = df_channels.explode('Campaign Source1')
        df_channels['Campaign Source1'] = df_channels['Campaign Source1'].str.strip()
        
        # Group and sum the fractional values
        channel_stats = df_channels.groupby('Campaign Source1').agg(
            Registrations=('reg_weighted', 'sum'),
            Attendees=('att_weighted', 'sum')
        ).reset_index()
        
        # Plotting two pie charts
        col_pie1, col_pie2 = st.columns(2)
        
        with col_pie1:
            fig_reg_pie = px.pie(channel_stats, names='Campaign Source1', values='Registrations', title="Registrations by Channel (Fractional)")
            st.plotly_chart(fig_reg_pie, use_container_width=True)
            
        with col_pie2:
            fig_att_pie = px.pie(channel_stats, names='Campaign Source1', values='Attendees', title="Attendees by Channel (Fractional)")
            st.plotly_chart(fig_att_pie, use_container_width=True)
            
    # 3. Micro-Conversions & Engagement (Updated to Gauge Chart)
    st.subheader("3. Micro-Conversions & Engagement")
    
    total_reg_volume = df['reg_volume'].sum()
    total_att_volume = df['att_volume'].sum()
    show_rate = (total_att_volume / total_reg_volume * 100) if total_reg_volume > 0 else 0

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=show_rate,
        title={'text': "Registration-to-Attendee Show Rate"},
        number={'suffix': "%", 'valueformat': ".1f"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': "#1f77b4"},
            'steps': [
                {'range': [0, 40], 'color': "rgba(255, 99, 71, 0.2)"},
                {'range': [40, 60], 'color': "rgba(255, 215, 0, 0.2)"},
                {'range': [60, 100], 'color': "rgba(144, 238, 144, 0.2)"}
            ],
        }
    ))
    
    # Adjust margins so the gauge doesn't take up excessive vertical space
    fig_gauge.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=300)
    
    st.plotly_chart(fig_gauge, use_container_width=True)

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
