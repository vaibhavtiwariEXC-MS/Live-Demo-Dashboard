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

    with st.expander("View Raw Data"):
        st.dataframe(df)

    # Pre-calculate base metrics used across the dashboard
    df['Customer Status'] = df['Lifecycle Stage'].apply(lambda x: 'Existing' if 'Customer' in str(x) else 'Net-New')
    df['reg_volume'] = df['Live Demo Registered'].dropna().apply(lambda x: len(str(x).split(',')))
    df['att_volume'] = df['Live Demo Attended'].dropna().apply(lambda x: len(str(x).split(',')))

    # --- NARRATIVE PART 1: The Top Line ---
    st.header("Engagement Overview")
    st.write("Tracking overall volume and show rates across all sessions.")
    
    col_metric, col_gauge = st.columns([1, 2])
    
    with col_metric:
        st.metric(label="Total Webinars Run", value=17)
        
        total_reg_volume = df['reg_volume'].sum()
        total_att_volume = df['att_volume'].sum()
        
        st.metric(label="Total Registrations", value=int(total_reg_volume))
        st.metric(label="Total Attendees", value=int(total_att_volume))

    with col_gauge:
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
        fig_gauge.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)

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
            st.write("**Job Title Distribution**")
            wordcloud = WordCloud(width=1200, height=400, background_color='#0E1117', colormap='Blues').generate(text)
            fig_wc, ax = plt.subplots(figsize=(12, 4), facecolor='#0E1117')
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig_wc)

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
