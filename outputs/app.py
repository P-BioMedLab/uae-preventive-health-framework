import streamlit as st
import plotly.graph_objects as go
import numpy as np

# Page configuration
st.set_page_config(
    page_title="UAE Preventive Medicine ROI Calculator",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS to match original design
st.markdown("""
    <style>
    /* Main app styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0 !important;
    }
    
    .block-container {
        padding: 2rem 2rem 2rem 2rem !important;
        max-width: 100% !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background-color: #f8f9fa !important;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
        padding: 25px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        font-size: 2.2em;
        margin: 0;
        font-weight: 600;
    }
    
    .main-header p {
        margin: 8px 0 0 0;
        font-size: 1em;
        opacity: 0.95;
    }
    
    /* Content container */
    .content-box {
        background: white;
        border-radius: 12px;
        padding: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    /* Section titles */
    .section-title {
        font-size: 1.5em;
        font-weight: 600;
        color: #2c3e50;
        border-bottom: 3px solid #3498db;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    
    /* Custom metric cards */
    [data-testid="stMetricValue"] {
        font-size: 2em !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px !important;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    [data-testid="stMetric"] label {
        color: white !important;
        font-size: 0.95em !important;
        font-weight: 500 !important;
    }
    
    [data-testid="stMetricValue"] {
        color: white !important;
    }
    
    /* Preset buttons */
    .stButton button {
        border-radius: 6px;
        font-weight: 500;
        border: none;
        padding: 8px 16px;
        transition: all 0.3s;
    }
    
    /* Health metrics styling */
    .health-metric {
        background: white;
        border: 2px solid #e9ecef;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        margin: 10px 0;
    }
    
    .health-metric-value {
        font-size: 1.8em;
        font-weight: 700;
        margin-bottom: 8px;
    }
    
    .health-metric-label {
        font-size: 0.9em;
        color: #7f8c8d;
        font-weight: 500;
    }
    
    .metric-events { color: #27ae60; }
    .metric-deaths { color: #e74c3c; }
    .metric-qalys { color: #3498db; }
    .metric-benefit { color: #9b59b6; }
    
    /* Slider styling */
    .stSlider {
        padding: 10px 0;
    }
    
    /* Info box */
    .info-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 15px;
        margin-top: 20px;
        font-size: 0.85em;
        color: #856404;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Intervention data
INTERVENTION_DATA = {
    'Comprehensive Portfolio': {
        'baseROI': 157, 'baseCostPerQaly': 62600, 'basePopulation': 2640000,
        'baseCost': 773, 'baseUptake': 0.80, 'baseEffectiveness': 0.62,
        'healthImpact': {'events': 158080, 'deaths': 16325, 'qalys': 326280},
        'investment': 20.4e9, 'benefits': 52.4e9
    },
    'Cardiovascular Disease Prevention': {
        'baseROI': 180, 'baseCostPerQaly': 61400, 'basePopulation': 500000,
        'baseCost': 1640, 'baseUptake': 0.80, 'baseEffectiveness': 0.75,
        'healthImpact': {'events': 12450, 'deaths': 3120, 'qalys': 133800},
        'investment': 8.2e9, 'benefits': 22.96e9
    },
    'Type 2 Diabetes Prevention': {
        'baseROI': 110, 'baseCostPerQaly': 32100, 'basePopulation': 750000,
        'baseCost': 413, 'baseUptake': 0.80, 'baseEffectiveness': 0.58,
        'healthImpact': {'events': 127500, 'deaths': 4200, 'qalys': 96600},
        'investment': 3.1e9, 'benefits': 6.51e9
    },
    'Cancer Screening (Breast & Colorectal)': {
        'baseROI': 145, 'baseCostPerQaly': 42200, 'basePopulation': 1126000,
        'baseCost': 426, 'baseUptake': 0.80, 'baseEffectiveness': 0.52,
        'healthImpact': {'events': 8420, 'deaths': 3100, 'qalys': 113720},
        'investment': 4.8e9, 'benefits': 11.76e9
    },
    "Alzheimer's Disease Prevention": {
        'baseROI': 89, 'baseCostPerQaly': 48900, 'basePopulation': 30000,
        'baseCost': 9667, 'baseUptake': 0.80, 'baseEffectiveness': 0.50,
        'healthImpact': {'events': 2700, 'deaths': 800, 'qalys': 59300},
        'investment': 2.9e9, 'benefits': 5.48e9
    },
    'Osteoporosis Prevention': {
        'baseROI': 84, 'baseCostPerQaly': 35800, 'basePopulation': 234000,
        'baseCost': 598, 'baseUptake': 0.80, 'baseEffectiveness': 0.65,
        'healthImpact': {'events': 10530, 'deaths': 1200, 'qalys': 39100},
        'investment': 1.4e9, 'benefits': 2.58e9
    }
}

def calculate_discount_factor(years, discount_rate=0.03):
    return sum(1 / (1 + discount_rate) ** t for t in range(years))

def get_time_horizon_multiplier(time_horizon):
    baseline_factor = calculate_discount_factor(10)
    current_factor = calculate_discount_factor(time_horizon)
    return current_factor / baseline_factor

def format_aed(value):
    abs_val = abs(value)
    if abs_val >= 1e9:
        return f"AED {value/1e9:.1f}B"
    elif abs_val >= 1e6:
        return f"AED {value/1e6:.1f}M"
    return f"AED {int(value):,}"

def calculate_results(data, population, cost_per_person, uptake, effectiveness, time_horizon):
    is_baseline = (
        abs(population - data['basePopulation']) / data['basePopulation'] < 0.05 and
        abs(cost_per_person - data['baseCost']) / data['baseCost'] < 0.05 and
        abs(uptake - data['baseUptake']) / data['baseUptake'] < 0.05 and
        abs(effectiveness - data['baseEffectiveness']) / data['baseEffectiveness'] < 0.05 and
        time_horizon == 10
    )
    
    if is_baseline:
        roi = data['baseROI']
        cost_per_qaly = data['baseCostPerQaly']
        total_investment = data['investment']
        total_benefits = data['benefits']
        events = data['healthImpact']['events']
        deaths = data['healthImpact']['deaths']
        qalys = data['healthImpact']['qalys']
    else:
        pop_ratio = population / data['basePopulation']
        cost_ratio = cost_per_person / data['baseCost']
        uptake_ratio = uptake / data['baseUptake']
        eff_ratio = effectiveness / data['baseEffectiveness']
        time_multiplier = get_time_horizon_multiplier(time_horizon)
        
        roi = round(data['baseROI'] * (uptake_ratio ** 0.4) * (eff_ratio ** 0.5) * 
                   ((1/cost_ratio) ** 0.3) * (time_multiplier ** 0.2))
        cost_per_qaly = round(data['baseCostPerQaly'] * cost_ratio * (1/uptake_ratio) * (1/eff_ratio))
        
        total_investment = data['investment'] * pop_ratio * cost_ratio * uptake_ratio * time_multiplier
        total_benefits = total_investment * (roi / 100 + 1)
        
        events = round(data['healthImpact']['events'] * pop_ratio * uptake_ratio * eff_ratio * time_multiplier)
        deaths = round(data['healthImpact']['deaths'] * pop_ratio * uptake_ratio * eff_ratio * time_multiplier)
        qalys = round(data['healthImpact']['qalys'] * pop_ratio * uptake_ratio * eff_ratio * time_multiplier)
    
    net_benefit = total_benefits - total_investment
    
    return {
        'roi': roi, 'cost_per_qaly': cost_per_qaly,
        'total_investment': total_investment, 'total_benefits': total_benefits,
        'net_benefit': net_benefit, 'events': events, 'deaths': deaths, 'qalys': qalys
    }

def calculate_sensitivity(base_roi):
    return {
        'Effectiveness': base_roi * 0.246,
        'Cost per Person': base_roi * 0.20,
        'Uptake Rate': base_roi * 0.15,
        'Time Horizon': base_roi * 0.125,
        'Population Size': base_roi * 0.099
    }

# Initialize session state
if 'preset' not in st.session_state:
    st.session_state.preset = 'Baseline'

# Sidebar
with st.sidebar:
    st.markdown('<h2 class="section-title">Scenario Parameters</h2>', unsafe_allow_html=True)
    
    intervention = st.selectbox("Intervention Type:", list(INTERVENTION_DATA.keys()), index=0)
    data = INTERVENTION_DATA[intervention]
    
    st.markdown("#### Quick Presets")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Baseline", use_container_width=True, type="primary" if st.session_state.preset == 'Baseline' else "secondary"):
            st.session_state.update({
                'preset': 'Baseline',
                'population': data['basePopulation'],
                'cost_per_person': data['baseCost'],
                'uptake': int(data['baseUptake'] * 100),
                'effectiveness': int(data['baseEffectiveness'] * 100),
                'time_horizon': 10
            })
            st.rerun()
    
    with col2:
        if st.button("Conservative", use_container_width=True, type="primary" if st.session_state.preset == 'Conservative' else "secondary"):
            st.session_state.update({
                'preset': 'Conservative',
                'population': int(data['basePopulation'] * 0.90),
                'cost_per_person': int(data['baseCost'] * 1.25),
                'uptake': int(data['baseUptake'] * 0.80 * 100),
                'effectiveness': int(data['baseEffectiveness'] * 0.85 * 100),
                'time_horizon': 10
            })
            st.rerun()
    
    with col3:
        if st.button("Optimistic", use_container_width=True, type="primary" if st.session_state.preset == 'Optimistic' else "secondary"):
            st.session_state.update({
                'preset': 'Optimistic',
                'population': int(data['basePopulation'] * 1.10),
                'cost_per_person': int(data['baseCost'] * 0.85),
                'uptake': min(int(data['baseUptake'] * 1.15 * 100), 95),
                'effectiveness': min(int(data['baseEffectiveness'] * 1.15 * 100), 80),
                'time_horizon': 10
            })
            st.rerun()
    
    st.markdown("---")
    
    population = st.slider("Target Population Size:", 20000, 3000000, 
                          st.session_state.get('population', data['basePopulation']), 5000)
    st.caption(f"**{population:,}**")
    
    cost_per_person = st.slider("Cost per Person (AED):", 400, 10000,
                                st.session_state.get('cost_per_person', data['baseCost']), 50)
    st.caption(f"**AED {cost_per_person:,}**")
    
    uptake = st.slider("Program Uptake Rate (%):", 30, 95,
                      st.session_state.get('uptake', int(data['baseUptake'] * 100)), 5)
    st.caption(f"**{uptake}%**")
    
    effectiveness = st.slider("Intervention Effectiveness (%):", 30, 80,
                             st.session_state.get('effectiveness', int(data['baseEffectiveness'] * 100)), 5)
    st.caption(f"**{effectiveness}%**")
    
    time_horizon = st.slider("Time Horizon (Years):", 5, 20,
                            st.session_state.get('time_horizon', 10), 5)
    st.caption(f"**{time_horizon} years**")
    
    st.markdown("""
    <div class="info-box">
        <strong>Note:</strong> Calculator provides estimates based on simplified scaling from full Markov model results. 
        Time horizons use 3% discounting. Conservative and optimistic scenarios use 95% CI bounds from Monte Carlo analysis.
    </div>
    """, unsafe_allow_html=True)

# Main content
st.markdown("""
    <div class="main-header">
        <h1>🏥 UAE Preventive Medicine ROI Calculator</h1>
        <p>Data-Driven Framework for Preventive Health Investment Analysis</p>
    </div>
""", unsafe_allow_html=True)

results = calculate_results(data, population, cost_per_person, uptake/100, effectiveness/100, time_horizon)

# Results section
st.markdown('<div class="content-box">', unsafe_allow_html=True)
st.markdown('<h2 class="section-title">📈 Results & Analysis</h2>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.metric("Return on Investment", f"{results['roi']}%")
with col2:
    st.metric("Cost per QALY", f"AED {results['cost_per_qaly']:,}")

st.markdown("</div>", unsafe_allow_html=True)

# Investment vs Benefits
st.markdown('<div class="content-box">', unsafe_allow_html=True)
st.markdown(f'<div style="font-size: 1.2em; font-weight: 600; color: #2c3e50; margin-bottom: 15px;">Investment vs. Benefits ({time_horizon}-Year Projection)</div>', unsafe_allow_html=True)

fig_invest = go.Figure(data=[
    go.Bar(
        x=['Investment', 'Benefits'],
        y=[results['total_investment'], results['total_benefits']],
        marker_color=['#e74c3c', '#27ae60'],
        text=[format_aed(results['total_investment']), format_aed(results['total_benefits'])],
        textposition='outside',
        textfont=dict(size=14, color='#2c3e50', family='Arial Black')
    )
])

# Set y-axis range to show proper proportions (start from 0, extend 10% above max value)
max_value = max(results['total_investment'], results['total_benefits'])
fig_invest.update_layout(
    yaxis_title="Amount (AED)",
    yaxis=dict(range=[0, max_value * 1.15]),
    showlegend=False,
    height=350,
    plot_bgcolor='white',
    paper_bgcolor='white',
    font=dict(size=12, color='#2c3e50'),
    margin=dict(l=40, r=40, t=40, b=40)
)

st.plotly_chart(fig_invest, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# Health Impact Metrics
st.markdown('<div class="content-box">', unsafe_allow_html=True)
st.markdown('<div style="font-size: 1.2em; font-weight: 600; color: #2c3e50; margin-bottom: 15px;">Health Impact Metrics</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="health-metric">
        <div class="health-metric-value metric-events">{results['events']:,}</div>
        <div class="health-metric-label">Disease Events Prevented</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="health-metric">
        <div class="health-metric-value metric-deaths">{results['deaths']:,}</div>
        <div class="health-metric-label">Premature Deaths Averted</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="health-metric">
        <div class="health-metric-value metric-qalys">{results['qalys']:,}</div>
        <div class="health-metric-label">QALYs Gained</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="health-metric">
        <div class="health-metric-value metric-benefit">{format_aed(results['net_benefit'])}</div>
        <div class="health-metric-label">Net Societal Benefit</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Sensitivity Analysis
st.markdown('<div class="content-box">', unsafe_allow_html=True)
st.markdown('<div style="font-size: 1.2em; font-weight: 600; color: #2c3e50; margin-bottom: 15px;">🎯 Sensitivity Analysis: Key Drivers of ROI</div>', unsafe_allow_html=True)

sensitivity = calculate_sensitivity(results['roi'])
factors = list(sensitivity.keys())
values = list(sensitivity.values())

fig_tornado = go.Figure()
fig_tornado.add_trace(go.Bar(
    y=factors,
    x=values,
    orientation='h',
    marker=dict(color='#3498db'),
    text=[f"±{v:.0f}%" for v in values],
    textposition='outside',
    textfont=dict(size=12, color='#2c3e50')
))

fig_tornado.update_layout(
    xaxis_title="Impact on ROI (%)",
    height=280,
    showlegend=False,
    plot_bgcolor='white',
    paper_bgcolor='white',
    font=dict(size=12, color='#2c3e50'),
    margin=dict(l=120, r=40, t=20, b=40)
)

st.plotly_chart(fig_tornado, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)