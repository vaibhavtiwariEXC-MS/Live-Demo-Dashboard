import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Live Demo Performance", layout="wide")
st.title("Live Demo Performance Dashboard")

uploaded_file = st.file_uploader("Upload HubSpot Export (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("Data loaded successfully.")

    with st.expander("View Raw Data"):
        st.dataframe(df)

 
    # Pre-calculate base metrics used across the dashboard
    df['Customer Status'] = df['Lifecycle Stage'].apply(lambda x: 'Existing' if 'Customer' in str(x) else 'Net-New')
    
    # Standardize delimiters to ensure accurate frequency counts
    df['reg_volume'] = df['Live Demo Registered'].dropna().apply(lambda x: len(str(x).replace(';', ',').split(',')))
    df['att_volume'] = df['Live Demo Attended'].dropna().apply(lambda x: len(str(x).replace(';', ',').split(',')))

    # --- NARRATIVE PART 1: The Top Line ---
    st.header("Engagement Overview")
    st.write("Tracking overall volume, show rates, and frequency across all sessions.")
    
    # 1. Core Metrics Row
    total_reg_volume = df['reg_volume'].sum()
    total_att_volume = df['att_volume'].sum()
    unique_registrants = len(df[df['reg_volume'] > 0])
    unique_attendees = len(df[df['att_volume'] > 0])
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric(label="Total Registrations", value=int(total_reg_volume))
    col_m2.metric(label="Unique Registrants", value=unique_registrants)
    col_m3.metric(label="Total Attendees", value=int(total_att_volume))
    col_m4.metric(label="Unique Attendees", value=unique_attendees)

    # 2. Gauges Row
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        show_rate = (total_att_volume / total_reg_volume * 100) if total_reg_volume > 0 else 0
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=show_rate,
            title={'text': "Total Show Rate (Volume)"},
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
        fig_gauge.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_g2:
        unique_show_rate = (unique_attendees / unique_registrants * 100) if unique_registrants > 0 else 0
        fig_gauge_unq = go.Figure(go.Indicator(
            mode="gauge+number",
            value=unique_show_rate,
            title={'text': "Unique Show Rate (People)"},
            number={'suffix': "%", 'valueformat': ".1f"},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1},
                'bar': {'color': "#ff7f0e"}, 
                'steps': [
                    {'range': [0, 40], 'color': "rgba(255, 99, 71, 0.2)"},
                    {'range': [40, 60], 'color': "rgba(255, 215, 0, 0.2)"},
                    {'range': [60, 100], 'color': "rgba(144, 238, 144, 0.2)"}
                ],
            }
        ))
        fig_gauge_unq.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=300)
        st.plotly_chart(fig_gauge_unq, use_container_width=True)

    # 3. Frequency Distribution Graphs (Using safe rename_axis to prevent dataframe shape errors)
    reg_dist = df[df['reg_volume'] > 0]['reg_volume'].value_counts().rename_axis('Number of Registrations').reset_index(name='People')
    att_dist = df[df['att_volume'] > 0]['att_volume'].value_counts().rename_axis('Number of Attendances').reset_index(name='People')

    col_dist1, col_dist2 = st.columns(2)
    with col_dist1:
        if not reg_dist.empty:
            fig_reg_dist = px.bar(reg_dist, x='Number of Registrations', y='People', title="Registration Frequency per Person")
            fig_reg_dist.update_layout(xaxis=dict(tickmode='linear', dtick=1))
            st.plotly_chart(fig_reg_dist, use_container_width=True)
        
    with col_dist2:
        if not att_dist.empty:
            fig_att_dist = px.bar(att_dist, x='Number of Attendances', y='People', title="Attendance Frequency per Person")
            fig_att_dist.update_layout(xaxis=dict(tickmode='linear', dtick=1))
            st.plotly_chart(fig_att_dist, use_container_width=True)

    # 4. Pacing & Timing (Using regex for bulletproof date extraction)
    st.subheader("Pacing & Timing")
    
    reg_dates_raw = df['Live Demo Registered'].dropna().astype(str).str.replace(';', ',').str.split(',').explode().str.strip()
    att_dates_raw = df['Live Demo Attended'].dropna().astype(str).str.replace(';', ',').str.split(',').explode().str.strip()

    # Extract just the date segment (MM.DD.YYYY) and drop invalid text
    reg_dates_clean = pd.to_datetime(reg_dates_raw.str.extract(r'(\d{1,2}[\.\-/]\d{1,2}[\.\-/]\d{4})')[0], errors='coerce').dropna()
    att_dates_clean = pd.to_datetime(att_dates_raw.str.extract(r'(\d{1,2}[\.\-/]\d{1,2}[\.\-/]\d{4})')[0], errors='coerce').dropna()

    if not reg_dates_clean.empty or not att_dates_clean.empty:
        reg_weeks = reg_dates_clean.dt.to_period('W-MON').dt.start_time.value_counts().rename_axis('Week Starting').reset_index(name='Registrations') if not reg_dates_clean.empty else pd.DataFrame(columns=['Week Starting', 'Registrations'])
        att_weeks = att_dates_clean.dt.to_period('W-MON').dt.start_time.value_counts().rename_axis('Week Starting').reset_index(name='Attendees') if not att_dates_clean.empty else pd.DataFrame(columns=['Week Starting', 'Attendees'])
        
        weekly_stats = pd.merge(reg_weeks, att_weeks, on='Week Starting', how='outer').fillna(0).sort_values('Week Starting')

        fig_weekly = px.line(weekly_stats, x='Week Starting', y=['Registrations', 'Attendees'], title="Week-by-Week Trend", markers=True)
        fig_weekly.update_layout(xaxis_tickformat="%b %d")
        st.plotly_chart(fig_weekly, use_container_width=True)
    else:
        st.warning("Could not parse dates for week-by-week trend.")

    # Day of Week Analysis (Safely grabbing just the day name)
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    reg_day_counts = reg_dates_raw.apply(lambda x: str(x).split()[-1]).value_counts().rename_axis('Weekday').reset_index(name='Registrations')
    att_day_counts = att_dates_raw.apply(lambda x: str(x).split()[-1]).value_counts().rename_axis('Weekday').reset_index(name='Attendees')

    day_stats = pd.merge(reg_day_counts, att_day_counts, on='Weekday', how='outer').fillna(0)
    day_stats = day_stats[day_stats['Weekday'].isin(days_order)].copy()
    day_stats['Weekday'] = pd.Categorical(day_stats['Weekday'], categories=days_order, ordered=True)
    day_stats = day_stats.sort_values('Weekday')

    if not day_stats.empty:
        fig_days = px.bar(day_stats, x='Weekday', y=['Registrations', 'Attendees'], barmode='group', title="Volume by Day of the Week")
        st.plotly_chart(fig_days, use_container_width=True)

    st.divider()
        
    # --- NARRATIVE PART 2: The Audience ---
    st.header("Who is in the Pipeline?")
    st.write("Comparing the profile of people who registered versus the people who actually showed up.")

    # Filter cohorts based on volume calculations from Part 1
    df_reg = df[df['reg_volume'] > 0].copy()
    df_att = df[df['att_volume'] > 0].copy()

    # Create UI Tabs
    tab_reg, tab_att = st.tabs(["Registrants", "Attendees"])

    def render_audience_section(cohort_df, cohort_label):
        col_status, col_fte = st.columns(2)
        
        with col_status:
            fig_status = px.pie(cohort_df, names='Customer Status', title=f'Net-New vs Existing ({cohort_label})')
            st.plotly_chart(fig_status, use_container_width=True)

        with col_fte:
            if 'FTE' in cohort_df.columns:
                cohort_df['FTE'] = pd.to_numeric(cohort_df['FTE'], errors='coerce')
                df_fte = cohort_df.dropna(subset=['FTE'])
                if not df_fte.empty:
                    fig_hist = px.histogram(
                        df_fte, 
                        x="FTE", 
                        title=f"Company Size (FTE) Distribution ({cohort_label})",
                        labels={'FTE': 'Full Time Employees'}
                    )
                    fig_hist.update_traces(xbins=dict(start=0, size=5000))
                    st.plotly_chart(fig_hist, use_container_width=True)
                else:
                    st.warning("No valid FTE data found.")

        if 'Job Title' in cohort_df.columns:
            import matplotlib.pyplot as plt
            from wordcloud import WordCloud
            
            titles = cohort_df['Job Title'].dropna().astype(str).tolist()
            text = " ".join(titles)
            
            if text.strip():
                # 1. Word Cloud View
                st.write(f"**Job Title Distribution (Word Cloud) - {cohort_label}**")
                wordcloud = WordCloud(width=1200, height=400, background_color='#0E1117', colormap='Blues').generate(text)
                fig_wc, ax = plt.subplots(figsize=(12, 4), facecolor='#0E1117')
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig_wc)
                
                # 2. Treemap View
                st.write(f"**Job Title Volume (Treemap) - {cohort_label}**")
                df_titles = cohort_df.dropna(subset=['Job Title']).copy()
                df_titles['Job Title'] = df_titles['Job Title'].astype(str).str.title().str.strip()
                
                title_counts = df_titles['Job Title'].value_counts().reset_index()
                title_counts.columns = ['Job Title', 'Count']
                title_counts['Root'] = 'All Roles'
                
                fig_tree = px.treemap(
                    title_counts, 
                    path=['Root', 'Job Title'], 
                    values='Count',
                    title=f"Job Titles Sized by Volume ({cohort_label})"
                )
                fig_tree.update_traces(textinfo="label+value")
                fig_tree.update_layout(margin=dict(t=50, l=10, r=10, b=10))
                st.plotly_chart(fig_tree, use_container_width=True)
            else:
                st.warning("No valid job titles found.")

    # Render the tabs
    with tab_reg:
        render_audience_section(df_reg, "Registrants")

    with tab_att:
        render_audience_section(df_att, "Attendees")

    st.divider()
    # --- NARRATIVE PART 3: Acquisition Sources ---
    st.header("Acquisition Sources")
    st.write("Tracking which channels drive registrations versus actual attendance.")

    if 'Campaign Source1' in df.columns:
        df_channels = df.copy()
        df_channels['Campaign Source1'] = df_channels['Campaign Source1'].astype(str).str.replace(';', ',').str.split(',')
        df_channels['campaign_count'] = df_channels['Campaign Source1'].apply(lambda x: len(x) if isinstance(x, list) else 1)
        
        df_channels['reg_weighted'] = df_channels['reg_volume'] / df_channels['campaign_count']
        df_channels['att_weighted'] = df_channels['att_volume'] / df_channels['campaign_count']
        
        df_channels = df_channels.explode('Campaign Source1')
        df_channels['Campaign Source1'] = df_channels['Campaign Source1'].str.strip()
        
        channel_stats = df_channels.groupby('Campaign Source1').agg(
            Registrations=('reg_weighted', 'sum'),
            Attendees=('att_weighted', 'sum')
        ).reset_index()
        
        col_pie1, col_pie2 = st.columns(2)
        with col_pie1:
            fig_reg_pie = px.pie(channel_stats, names='Campaign Source1', values='Registrations', title="Registrations by Channel (Fractional)")
            st.plotly_chart(fig_reg_pie, use_container_width=True)
            
        with col_pie2:
            fig_att_pie = px.pie(channel_stats, names='Campaign Source1', values='Attendees', title="Attendees by Channel (Fractional)")
            st.plotly_chart(fig_att_pie, use_container_width=True)

    st.divider()

    # --- NARRATIVE PART 4: Pipeline Impact ---
    st.header("Pipeline Impact")
    st.write("Following the cohorts down the funnel to measure revenue potential.")

    df_registrants = df[df['Live Demo Registered'].notna() & (df['Live Demo Registered'] != '')]
    df_attendees = df[df['Live Demo Attended'].notna() & (df['Live Demo Attended'] != '')]

    nn_reg = df_registrants[df_registrants['Customer Status'] == 'Net-New']
    cust_reg = df_registrants[df_registrants['Customer Status'] == 'Existing']
    nn_att = df_attendees[df_attendees['Customer Status'] == 'Net-New']
    cust_att = df_attendees[df_attendees['Customer Status'] == 'Existing']

    nn_mql_stages = ['Marketing Qualified Lead', 'Sales Accepted Lead', 'Sales Qualified Lead', 'Opportunity']
    nn_sal_stages = ['Sales Accepted Lead', 'Sales Qualified Lead', 'Opportunity']
    nn_sql_stages = ['Sales Qualified Lead', 'Opportunity']
    nn_opp_stages = ['Opportunity']

    cust_mql_stages = ['Customer - MQL', 'Customer - SAL', 'Customer - SQL', 'Customer - Opp']
    cust_sal_stages = ['Customer - SAL', 'Customer - SQL', 'Customer - Opp']
    cust_sql_stages = ['Customer - SQL', 'Customer - Opp']
    cust_opp_stages = ['Customer - Opp']

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

    df_funnel_nn_reg = build_funnel_df(nn_reg, "Registrants", nn_mql_stages, nn_sal_stages, nn_sql_stages, nn_opp_stages)
    df_funnel_nn_att = build_funnel_df(nn_att, "Attendees", nn_mql_stages, nn_sal_stages, nn_sql_stages, nn_opp_stages)
    df_funnel_cust_reg = build_funnel_df(cust_reg, "Registrants", cust_mql_stages, cust_sal_stages, cust_sql_stages, cust_opp_stages)
    df_funnel_cust_att = build_funnel_df(cust_att, "Attendees", cust_mql_stages, cust_sal_stages, cust_sql_stages, cust_opp_stages)

    col_f1, col_f2 = st.columns(2)
    col_f3, col_f4 = st.columns(2)
    
    with col_f1:
        st.plotly_chart(px.funnel(df_funnel_nn_reg, x='number', y='stage', title="Net-New Registrants"), use_container_width=True)
    with col_f2:
        st.plotly_chart(px.funnel(df_funnel_nn_att, x='number', y='stage', title="Net-New Attendees"), use_container_width=True)
    with col_f3:
        st.plotly_chart(px.funnel(df_funnel_cust_reg, x='number', y='stage', title="Customer Registrants"), use_container_width=True)
    with col_f4:
        st.plotly_chart(px.funnel(df_funnel_cust_att, x='number', y='stage', title="Customer Attendees"), use_container_width=True)
