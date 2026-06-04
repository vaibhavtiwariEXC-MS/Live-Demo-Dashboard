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
        fig_gauge.update_layout(margin=dict(l=20, r=
