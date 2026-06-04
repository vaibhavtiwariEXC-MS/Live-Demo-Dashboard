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
    
    col_tot_met, col_tot_gauge, col_unq_met, col_unq_gauge = st.columns([1, 1.5, 1, 1.5])
    
    with col_tot_met:
        st.metric(label="Total Live Demos Run", value=17)
        
        total_reg_volume = df['reg_volume'].sum()
        total_att_volume = df['att_volume'].sum()
        
        st.metric(label="Total Registrations", value=int(total_reg_volume))
        st.metric(label="Total Attendees", value=int(total_att_volume))

    with col_tot_gauge:
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

    with col_unq_met:
        # Blank space to push metrics down so they align with the left column
        st.write("") 
        st.write("")
        st.write("")
        
        unique_registrants = len(df[df['reg_volume'] > 0])
        unique_attendees = len(df[df['att_volume'] > 0])
        
        st.metric(label="Unique Registrants", value=unique_registrants)
        st.metric(label="Unique Attendees", value=unique_attendees)

    with col_unq_gauge:
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

    # Frequency Distribution Graphs
    reg_dist = df[df['reg_volume'] > 0]['reg_volume'].value_counts().reset_index()
    reg_dist.columns = ['Number of Registrations', 'People']
    reg_dist = reg_dist.sort_values('Number of Registrations')

    att_dist = df[df['att_volume'] > 0]['att_volume'].value_counts().reset_index()
    att_dist.columns = ['Number of Attendances', 'People']
    att_dist = att_dist.sort_values('Number of Attendances')

    col_dist1, col_dist2 = st.columns(2)
    
    with col_dist1:
        fig_reg_dist = px.bar(reg_dist, x='Number of Registrations', y='People', title="Registration Frequency per Person")
        fig_reg_dist.update_layout(xaxis=dict(tickmode='linear', dtick=1))
        st.plotly_chart(fig_reg_dist, use_container_width=True)
        
    with col_dist2:
        fig_att_dist = px.bar(att_dist, x='Number of Attendances', y='People', title="Attendance Frequency per Person")
        fig_att_dist.update_layout(xaxis=dict(tickmode='linear', dtick=1))
        st.plotly_chart(fig_att_dist, use_container_width=True)

    # Day of Week Analysis
    st.subheader("Day of Week Analysis")
    
    reg_dates = df['Live Demo Registered'].dropna().astype(str).str.replace(';', ',').str.split(',')
    reg_exploded = reg_dates.explode().str.strip()
    reg_days = reg_exploded.apply(lambda x: str(x).split(' ')[-1])
    reg_day_counts = reg_days.value_counts().reset_index()
    reg_day_counts.columns = ['Weekday', 'Registrations']

    att_dates = df['Live Demo Attended'].dropna().astype(str).str.replace(';', ',').str.split(',')
    att_exploded = att_dates.explode().str.strip()
    att_days = att_exploded.apply(lambda x: str(x).split(' ')[-1])
    att_day_counts = att_days.value_counts().reset_index()
    att_day_counts.columns = ['Weekday', 'Attendees']

    day_stats = pd.merge(reg_day_counts, att_day_counts, on='Weekday', how='outer').fillna(0)
    
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_stats['Weekday'] = pd.Categorical(day_stats['Weekday'], categories=days_order, ordered=True)
    day_stats = day_stats.sort_values('Weekday')

    fig_days = px.bar(
        day_stats, 
        x='Weekday', 
        y=['Registrations', 'Attendees'], 
        barmode='group',
        title="Volume by Day of the Week"
    )
    st.plotly_chart(fig_days, use_container_width=True)

    st.divider()
    # --- NARRATIVE PART 2: The Audience ---
    st.header("Who is Attending?")
    st.write("Breaking down the audience by customer status, company size, and job title.")

    col_status, col_fte = st.columns(2)
    
    with col_status:
        fig_status = px.pie(df, names='Customer Status', title='Net-New vs Existing Audience')
        st.plotly_chart(fig_status, use_container_width=True)

    with col_fte:
        if 'FTE' in df.columns:
            df['FTE'] = pd.to_numeric(df['FTE'], errors='coerce')
            df_fte = df.dropna(subset=['FTE'])
            if not df_fte.empty:
                fig_hist = px.histogram(
                    df_fte, 
                    x="FTE", 
                    title="Company Size (FTE) Distribution",
                    labels={'FTE': 'Full Time Employees'}
                )
                fig_hist.update_traces(xbins=dict(start=0, size=5000))
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.warning("No valid FTE data found to generate histogram.")

    if 'Job Title' in df.columns:
        import matplotlib.pyplot as plt
        from wordcloud import WordCloud
        
        titles = df['Job Title'].dropna().astype(str).tolist()
        text = " ".join(titles)
        
        if text.strip():
            # 1. Word Cloud View
            st.write("**Job Title Distribution (Word Cloud)**")
            wordcloud = WordCloud(width=1200, height=400, background_color='#0E1117', colormap='Blues').generate(text)
            fig_wc, ax = plt.subplots(figsize=(12, 4), facecolor='#0E1117')
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig_wc)
            
            # 2. Treemap View
            st.write("**Job Title Volume (Treemap)**")
            df_titles = df.dropna(subset=['Job Title']).copy()
            df_titles['Job Title'] = df_titles['Job Title'].astype(str).str.title().str.strip()
            
            title_counts = df_titles['Job Title'].value_counts().reset_index()
            title_counts.columns = ['Job Title', 'Count']
            title_counts['Root'] = 'All Roles'
            
            fig_tree = px.treemap(
                title_counts, 
                path=['Root', 'Job Title'], 
                values='Count',
                title="Job Titles Sized by Volume"
            )
            fig_tree.update_traces(textinfo="label+value")
            fig_tree.update_layout(margin=dict(t=50, l=10, r=10, b=10))
            st.plotly_chart(fig_tree, use_container_width=True)
        else:
            st.warning("No valid job titles found to generate visualizations.")

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
