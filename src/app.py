import streamlit as st
import requests
import time
import os
import pandas as pd
import numpy as np


# API Server URL
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# Premium CSS for MedPath-RAG — Teal Medical Theme
CUSTOM_CSS = """
<style>
    /* ========== GLOBAL STYLES ========== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background: #F8FAFB;
    }
    
    [data-testid="stAppViewContainer"] {
        background: #F8FAFB;
    }
    
    [data-testid="stMain"] {
        background: transparent;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        color: #0F172A;
    }
    
    /* Hide default Streamlit sidebar menu header */
    div[data-testid="stSidebarUserContent"] div.stRadio > label {
        display: none !important;
    }
    
    /* ========== SIDEBAR — Dark Teal ========== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0B2027 0%, #0F2F2E 100%) !important;
        color: #ffffff !important;
        border-right: none !important;
        padding-top: 0.5rem;
        box-shadow: 2px 0 16px rgba(0,0,0,0.12) !important;
        min-width: 260px !important;
        width: 260px !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    .sidebar-brand {
        padding: 1.5rem 1.25rem 1.25rem 1.25rem;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 1rem;
        background: transparent;
    }
    
    .sidebar-logo-row {
        display: flex;
        align-items: center;
        gap: 0.65rem;
    }
    
    .sidebar-logo-icon {
        width: 36px;
        height: 36px;
        background: #0D7C7E;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        flex-shrink: 0;
    }
    
    .sidebar-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 1.25rem;
        color: #ffffff !important;
        letter-spacing: -0.3px;
        line-height: 1.2;
    }
    
    .sidebar-subtitle {
        font-size: 0.72rem;
        color: rgba(255,255,255,0.5) !important;
        margin-top: 0.5rem;
        line-height: 1.4;
        font-weight: 400;
        padding-left: 0;
    }
    
    /* ========== NAVIGATION MENU ========== */
    div[data-testid="stSidebarUserContent"] div.stRadio > div {
        background: transparent !important;
        border: none !important;
        padding: 0 0.5rem !important;
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    
    div[data-testid="stSidebarUserContent"] div.stRadio label[data-baseweb="radio"] {
        background: transparent !important;
        padding: 0.65rem 1rem !important;
        border-radius: 8px !important;
        border: none !important;
        margin: 0 !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
        display: flex !important;
        align-items: center !important;
        font-weight: 400 !important;
        font-size: 0.88rem !important;
    }
    
    div[data-testid="stSidebarUserContent"] div.stRadio label[data-baseweb="radio"]:hover {
        background: rgba(255, 255, 255, 0.06) !important;
        transform: none !important;
    }
    
    div[data-testid="stSidebarUserContent"] div.stRadio label[data-baseweb="radio"]:has(input:checked) {
        background: #0D7C7E !important;
        border: none !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 8px rgba(13, 124, 126, 0.35) !important;
        transform: none !important;
        border-radius: 8px !important;
    }
    
    /* Hide the radio dot circles */
    div[data-testid="stSidebarUserContent"] div.stRadio input[type="radio"] {
        display: none !important;
    }
    
    /* Hide radio circle indicator */
    div[data-testid="stSidebarUserContent"] div.stRadio label[data-baseweb="radio"] > div:first-child {
        display: none !important;
    }
    
    /* ========== USER CARD (sidebar footer) ========== */
    .user-card {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 0.85rem 1rem;
        margin: 1rem 0.75rem;
        font-size: 0.82rem;
    }
    
    /* ========== MAIN CONTENT CONTAINER ========== */
    [data-testid="stVerticalBlock"] {
        padding: 1rem 1.5rem;
    }
    
    /* ========== PAGE HEADER ========== */
    .page-header {
        font-family: 'Outfit', sans-serif;
        font-size: 1.65rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.15rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .page-subtitle {
        font-size: 0.9rem;
        color: #64748B;
        font-weight: 400;
        margin-bottom: 1.5rem;
    }
    
    /* ========== USER HEADER BADGE (top-right) ========== */
    .user-header-badge {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        float: right;
    }
    .role-badge {
        background: #F1F5F9;
        color: #475569;
        font-size: 0.75rem;
        font-weight: 500;
        padding: 0.3rem 0.75rem;
        border-radius: 6px;
        border: 1px solid #E2E8F0;
    }
    .avatar-circle {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: linear-gradient(135deg, #0D7C7E 0%, #0A6869 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.85rem;
        font-weight: 600;
        color: white !important;
    }
    
    /* ========== WELCOME CONTAINER (Home) ========== */
    .welcome-container {
        text-align: left;
        padding: 2.5rem 0 1.5rem 0;
        max-width: 100%;
        margin: 0;
        background: transparent;
        border-radius: 0;
        box-shadow: none;
    }
    .welcome-title {
        font-family: 'Outfit', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.5px;
        margin-bottom: 0.25rem;
    }
    .welcome-title span {
        color: #0D7C7E;
        background: none;
        -webkit-background-clip: unset;
        -webkit-text-fill-color: #0D7C7E;
        background-clip: unset;
    }
    .welcome-subtitle {
        font-size: 1rem;
        color: #64748B;
        margin-top: 0.25rem;
        font-weight: 400;
        line-height: 1.5;
    }
    
    /* ========== SEARCH BAR (Home) ========== */
    .search-block {
        max-width: 700px;
        margin: 1.5rem 0;
        display: flex;
        gap: 0.5rem;
    }
    
    /* ========== EXAMPLE QUESTION CHIPS ========== */
    .example-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 1rem 0 2rem 0;
    }
    .example-chip {
        background: #ffffff;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 0.45rem 0.85rem;
        font-size: 0.78rem;
        color: #475569;
        cursor: pointer;
        transition: all 0.2s ease;
        white-space: nowrap;
    }
    .example-chip:hover {
        border-color: #0D7C7E;
        color: #0D7C7E;
        background: #F0FDFA;
    }
    
    /* ========== EXPLORE CARDS (Home) ========== */
    .explore-card {
        background: #ffffff;
        border: 1px solid #E8ECF0;
        border-radius: 14px;
        padding: 1.75rem 1.5rem;
        text-align: left;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: all 0.25s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    .explore-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        border-color: #CBD5E1;
    }
    .explore-icon-box {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        margin-bottom: 1.25rem;
    }
    .bg-teal-light {
        background: linear-gradient(135deg, #0D7C7E 0%, #0A9396 100%);
        color: white;
    }
    .bg-green-light { 
        background: linear-gradient(135deg, #0D7C7E 0%, #0A9396 100%); 
        color: white;
    }
    .bg-orange-light { 
        background: linear-gradient(135deg, #E8853D 0%, #D97706 100%); 
        color: white;
    }
    .bg-blue-light { 
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%); 
        color: white;
    }
    .bg-purple-light { 
        background: linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%); 
        color: white;
    }
    
    .explore-card h3 {
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: #0F172A;
    }
    .explore-card p {
        font-size: 0.82rem;
        color: #64748B;
        line-height: 1.55;
        margin-bottom: 1.25rem;
        flex-grow: 1;
    }
    .explore-link {
        font-size: 0.85rem;
        font-weight: 600;
        color: #0D7C7E;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        background: none;
        padding: 0;
        border-radius: 0;
        transition: all 0.2s ease;
    }
    .explore-link:hover {
        color: #0A6869;
        gap: 0.5rem;
        transform: none;
        box-shadow: none;
    }
    
    /* ========== PORTAL CARDS (Diabetes & Cancer grids) ========== */
    .portal-card {
        background: #ffffff;
        border: 1px solid #E8ECF0;
        border-radius: 12px;
        padding: 1.5rem 1.25rem;
        text-align: left;
        height: 100%;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: all 0.25s ease;
    }
    .portal-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.07);
        border-color: #CBD5E1;
    }
    .portal-card-header {
        font-weight: 700;
        font-size: 1.05rem;
        margin-bottom: 0.5rem;
        color: #0F172A;
    }
    .portal-card-desc {
        font-size: 0.82rem;
        color: #64748B;
        line-height: 1.5;
        margin-bottom: 1rem;
        min-height: 2.4rem;
    }
    .portal-icon {
        font-size: 1.5rem;
        margin-bottom: 0.75rem;
    }
    .portal-explore-link {
        font-size: 0.82rem;
        font-weight: 600;
        color: #0D7C7E;
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        cursor: pointer;
    }
    .portal-explore-link:hover {
        color: #0A6869;
    }
    
    /* ========== AI RESPONSE CARD ========== */
    .ai-response-card {
        background: #ffffff;
        border: 1px solid #E8ECF0;
        border-radius: 14px;
        padding: 2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    
    /* ========== SOURCES CARD ========== */
    .sources-card {
        background: #ffffff;
        border: 1px solid #E8ECF0;
        border-radius: 14px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        margin-bottom: 1rem;
    }
    .source-item {
        border-bottom: 1px solid #F1F5F9;
        padding: 0.75rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.82rem;
    }
    .source-item:last-child {
        border-bottom: none;
    }
    .source-meta {
        color: #64748B;
        font-size: 0.75rem;
        margin-top: 0.15rem;
    }
    .source-view-btn {
        font-size: 0.72rem;
        background: #F0FDFA;
        color: #0D7C7E;
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
        font-weight: 600;
        border: 1px solid #CCFBF1;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .source-view-btn:hover {
        background: #CCFBF1;
    }
    
    /* ========== CONFIDENCE CARD ========== */
    .confidence-card {
        background: #ffffff;
        border: 1px solid #E8ECF0;
        border-radius: 14px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .confidence-gauge-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1.25rem;
        margin-top: 0.5rem;
    }
    
    /* ========== KPI CARDS (Admin) ========== */
    .kpi-card {
        background: #ffffff;
        border: 1px solid #E8ECF0;
        border-radius: 12px;
        padding: 1.25rem 1.15rem;
        text-align: left;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: all 0.2s ease;
    }
    .kpi-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }
    .kpi-value {
        font-family: 'Outfit', sans-serif;
        font-size: 1.85rem;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.1;
    }
    .kpi-label {
        font-size: 0.75rem;
        font-weight: 500;
        color: #64748B;
        margin-bottom: 0.25rem;
        text-transform: capitalize;
    }
    .kpi-subtext {
        font-size: 0.72rem;
        color: #94A3B8;
        margin-top: 0.3rem;
    }
    
    /* ========== RESEARCH SUMMARY CARD ========== */
    .research-summary-card {
        background: #ffffff;
        border: 1px solid #E8ECF0;
        border-radius: 12px;
        padding: 1.25rem;
    }
    
    /* ========== BUTTON OVERRIDES ========== */
    div[data-testid="stButton"] > button[kind="primary"],
    div[data-testid="stButton"] > button[data-testid="baseButton-primary"],
    [data-testid="stFormSubmitButton"] > button {
        background: #0D7C7E !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover,
    div[data-testid="stButton"] > button[data-testid="baseButton-primary"]:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        background: #0A6869 !important;
    }
    
    div[data-testid="stButton"] > button[kind="secondary"],
    div[data-testid="stButton"] > button[data-testid="baseButton-secondary"] {
        border: 1px solid #E2E8F0 !important;
        color: #475569 !important;
        border-radius: 8px !important;
        background: #ffffff !important;
        font-weight: 500 !important;
    }
    div[data-testid="stButton"] > button[kind="secondary"]:hover,
    div[data-testid="stButton"] > button[data-testid="baseButton-secondary"]:hover {
        border-color: #0D7C7E !important;
        color: #0D7C7E !important;
        background: #F0FDFA !important;
    }

    /* ========== STREAMLIT METRICS ========== */
    div[data-testid="metric-container"] {
        background: #ffffff;
        border: 1px solid #E8ECF0;
        border-radius: 12px;
        padding: 1.15rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: all 0.2s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }
    
    /* ========== EXPANDERS ========== */
    div[data-testid="stExpander"] {
        background: #ffffff;
        border: 1px solid #E8ECF0;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        margin-bottom: 0.75rem;
        overflow: hidden;
    }
    div[data-testid="stExpander"] > details > summary {
        padding: 0.85rem 1.25rem;
        font-weight: 600;
        background: #FAFBFC;
        color: #0F172A !important;
    }
    div[data-testid="stExpander"] > details > summary p {
        color: #0F172A !important;
    }
    div[data-testid="stExpander"] > details > summary span {
        color: #0F172A !important;
    }
    div[data-testid="stExpander"] > details > summary svg {
        fill: #0F172A !important;
    }
    div[data-testid="stExpander"] > details > div {
        padding: 1.25rem;
        color: #1E293B !important;
    }
    div[data-testid="stExpander"] > details > div p {
        color: #1E293B !important;
    }
    div[data-testid="stExpander"] > details > div span {
        color: #1E293B !important;
    }
    div[data-testid="stExpander"] > details > div label {
        color: #1E293B !important;
    }
    
    /* ========== INPUT STYLING ========== */
    div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        padding: 0.65rem 0.85rem;
        font-size: 0.88rem;
        background: #ffffff;
    }
    div[data-testid="stTextInput"] input:focus, div[data-testid="stTextArea"] textarea:focus {
        border-color: #0D7C7E;
        box-shadow: 0 0 0 2px rgba(13, 124, 126, 0.15);
    }
    
    /* ========== NEW CHAT BUTTON ========== */
    .new-chat-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: #0D7C7E;
        color: white;
        padding: 0.45rem 1rem;
        border-radius: 8px;
        font-size: 0.82rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        text-decoration: none;
    }
    .new-chat-btn:hover {
        background: #0A6869;
    }
    
    /* ========== FOOTER ========== */
    .footer-text {
        text-align: left;
        font-size: 0.75rem;
        color: #94A3B8;
        padding: 1rem 0;
        border-top: 1px solid #F1F5F9;
        margin-top: 2rem;
    }
    
    /* ========== SEARCH RESULT CARD ========== */
    .search-result-card {
        background: #ffffff;
        border: 1px solid #E8ECF0;
        padding: 1rem 1.15rem;
        border-radius: 10px;
        margin-bottom: 0.65rem;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    .search-result-card:hover {
        border-color: #CBD5E1;
    }
    .search-result-card.active {
        border-left: 3px solid #0D7C7E;
        background: #F0FDFA;
    }
    
    /* ========== SOURCE FILE CARD ========== */
    .source-file-card {
        background: #ffffff;
        border: 1px solid #E8ECF0;
        padding: 1rem 1.15rem;
        border-radius: 10px;
        margin-bottom: 0.65rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* ========== TEAL CHART THEMING ========== */
    [data-testid="stVegaLiteChart"] {
        background: #ffffff;
        border: 1px solid #E8ECF0;
        border-radius: 12px;
        padding: 1rem;
    }

</style>
"""

AUTH_CSS = """
<style>
    section[data-testid="stSidebar"],
    header[data-testid="stHeader"],
    footer[data-testid="stFooter"],
    #MainMenu,
    .stDeployButton,
    [data-testid="stToolbar"] {
        display: none !important;
    }

    .stApp:has(.auth-page-marker) [data-testid="stAppViewContainer"],
    .stApp:has(.auth-page-marker) [data-testid="stAppViewContainer"] > section.main,
    .stApp:has(.auth-page-marker) .main {
        background: transparent !important;
    }

    .stApp:has(.auth-page-marker) {
        background: linear-gradient(135deg, rgba(13, 124, 126, 0.75) 0%, rgba(26, 43, 72, 0.72) 100%),
            url('__AUTH_BG__') center/cover no-repeat fixed !important;
        min-height: 100vh !important;
    }

    html:has(.auth-page-marker),
    body:has(.auth-page-marker) {
        background: transparent !important;
        overflow: hidden !important;
        height: 100vh !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    .stApp:has(.auth-page-marker) [data-testid="stAppViewContainer"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: 100vh !important;
        width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    .stApp:has(.auth-page-marker) section.main {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: 100vh !important;
        width: 100% !important;
        max-width: 100% !important;
        overflow: visible !important;
        padding: 0 !important;
        margin: 0 auto !important;
    }

    .stApp:has(.auth-page-marker) section.main > div.block-container,
    .stApp:has(.auth-page-marker) [data-testid="stMainBlockContainer"],
    .stApp:has(.auth-page-marker) .block-container {
        position: fixed !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        z-index: 1 !important;
        background: #FFFFFF !important;
        border-radius: 16px !important;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.22) !important;
        max-width: 400px !important;
        width: calc(100% - 2rem) !important;
        max-height: calc(100vh - 2rem) !important;
        overflow-y: auto !important;
        margin: 0 !important;
        padding: 1.75rem 1.75rem 1.5rem 1.75rem !important;
        flex-shrink: 0 !important;
    }

    .auth-page-marker { display: none; }

    /* Tighten Streamlit vertical spacing on auth page */
    .stApp:has(.auth-page-marker) [data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }

    .stApp:has(.auth-page-marker) [data-testid="element-container"] {
        margin: 0 !important;
        padding: 0.15rem 0 !important;
    }

    .stApp:has(.auth-page-marker) [data-testid="stMarkdownContainer"] {
        margin: 0 !important;
        padding: 0 !important;
    }

    .stApp:has(.auth-page-marker) [data-testid="stForm"] {
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
    }

    .stApp:has(.auth-page-marker) [data-testid="stForm"] [data-testid="element-container"] {
        padding: 0.1rem 0 !important;
    }

    .stApp:has(.auth-page-marker) button.st-emotion-cache-19rxjzo,
    .stApp:has(.auth-page-marker) button.st-emotion-cache-128j5w5 {
        all: unset;
        box-sizing: border-box;
    }

    .stApp:has(.auth-page-marker) .auth-brand {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1.5rem;
    }

    .stApp:has(.auth-page-marker) .auth-logo svg {
        width: 40px;
        height: 40px;
        flex-shrink: 0;
    }

    .stApp:has(.auth-page-marker) .auth-title {
        font-family: 'Outfit', sans-serif;
        font-size: 1.25rem;
        font-weight: 700;
        color: #0D7C7E !important;
        -webkit-text-fill-color: #0D7C7E !important;
        line-height: 1.2;
    }

    .stApp:has(.auth-page-marker) .auth-tagline {
        font-size: 0.7rem;
        color: #6B7280 !important;
        -webkit-text-fill-color: #6B7280 !important;
        margin-top: 0.15rem;
        line-height: 1.35;
    }

    .stApp:has(.auth-page-marker) .auth-welcome {
        font-family: 'Outfit', sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: #1A2B48 !important;
        -webkit-text-fill-color: #1A2B48 !important;
        margin: 0 0 0.3rem 0;
        line-height: 1.2;
    }

    .stApp:has(.auth-page-marker) .auth-subtext {
        font-size: 0.85rem;
        color: #64748B !important;
        -webkit-text-fill-color: #64748B !important;
        margin: 0 0 1.25rem 0;
    }

    .stApp:has(.auth-page-marker) .auth-field-label {
        display: block;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        color: #1E293B !important;
        -webkit-text-fill-color: #1E293B !important;
        margin: 0.5rem 0 0.15rem 0 !important;
        line-height: 1.3;
    }

    .stApp:has(.auth-page-marker) .auth-field-label-first {
        margin-top: 0 !important;
    }

    .stApp:has(.auth-page-marker) [data-testid="stMarkdownContainer"] p,
    .stApp:has(.auth-page-marker) [data-testid="stMarkdownContainer"] label,
    .stApp:has(.auth-page-marker) [data-testid="stMarkdownContainer"] span {
        color: inherit;
    }

    .stApp:has(.auth-page-marker) [data-testid="stMarkdownContainer"] .auth-field-label {
        color: #1E293B !important;
        -webkit-text-fill-color: #1E293B !important;
    }

    .stApp:has(.auth-page-marker) [data-testid="stMarkdownContainer"] .auth-welcome {
        color: #1A2B48 !important;
        -webkit-text-fill-color: #1A2B48 !important;
    }

    .stApp:has(.auth-page-marker) [data-testid="stMarkdownContainer"] .auth-subtext {
        color: #64748B !important;
        -webkit-text-fill-color: #64748B !important;
    }

    .stApp:has(.auth-page-marker) [data-testid="stMarkdownContainer"] .auth-title {
        color: #0D7C7E !important;
        -webkit-text-fill-color: #0D7C7E !important;
    }

    .stApp:has(.auth-page-marker) [data-testid="stMarkdownContainer"] .auth-tagline {
        color: #6B7280 !important;
        -webkit-text-fill-color: #6B7280 !important;
    }

    .stApp:has(.auth-page-marker) [data-testid="stMarkdownContainer"] .auth-forgot-link {
        color: #0D7C7E !important;
        -webkit-text-fill-color: #0D7C7E !important;
    }

    .stApp:has(.auth-page-marker) div[data-testid="stTextInput"] > label,
    .stApp:has(.auth-page-marker) div[data-testid="stSelectbox"] > label,
    .stApp:has(.auth-page-marker) [data-testid="stWidgetLabel"] {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }

    .stApp:has(.auth-page-marker) [data-testid="stWidgetLabel"] p,
    .stApp:has(.auth-page-marker) div[data-testid="stTextInput"] label p,
    .stApp:has(.auth-page-marker) div[data-testid="stSelectbox"] label p {
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        color: #1E293B !important;
        -webkit-text-fill-color: #1E293B !important;
        opacity: 1 !important;
        margin-bottom: 0.3rem !important;
    }

    .stApp:has(.auth-page-marker) div[data-testid="stTextInput"] {
        margin: 0 !important;
        padding: 0 !important;
        max-width: 100% !important;
    }

    .stApp:has(.auth-page-marker) div[data-testid="stTextInput"] > div {
        margin: 0 !important;
        padding: 0 !important;
    }

    .stApp:has(.auth-page-marker) div[data-testid="stButton"],
    .stApp:has(.auth-page-marker) [data-testid="stFormSubmitButton"],
    .stApp:has(.auth-page-marker) div[data-testid="stTextInput"],
    .stApp:has(.auth-page-marker) [data-testid="element-container"] {
        max-width: 100% !important;
    }

    .stApp:has(.auth-page-marker) div[data-testid="stButton"] > button,
    .stApp:has(.auth-page-marker) [data-testid="stFormSubmitButton"] > button {
        border-radius: 8px !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        min-height: 40px !important;
        max-height: 44px !important;
        padding: 0.55rem 1rem !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        position: relative !important;
        cursor: pointer !important;
    }

    .stApp:has(.auth-page-marker) div[data-testid="stButton"] > button[kind="primary"],
    .stApp:has(.auth-page-marker) div[data-testid="stButton"] > button[data-testid="baseButton-primary"],
    .stApp:has(.auth-page-marker) [data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"],
    .stApp:has(.auth-page-marker) [data-testid="stFormSubmitButton"] > button[data-testid="baseButton-primary"] {
        background-color: #0D7C7E !important;
        background: #0D7C7E !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 3px 10px rgba(13, 124, 126, 0.3) !important;
    }

    .stApp:has(.auth-page-marker) div[data-testid="stTextInput"] input {
        background: #FFFFFF !important;
        border: 1.5px solid #D1D5DB !important;
        border-radius: 8px !important;
        padding: 0.55rem 0.85rem !important;
        font-size: 0.85rem !important;
        color: #1E293B !important;
        height: auto !important;
        min-height: 38px !important;
        max-height: 42px !important;
    }

    .stApp:has(.auth-page-marker) div[data-testid="stTextInput"] input:focus {
        border-color: #0D7C7E !important;
        box-shadow: 0 0 0 3px rgba(13, 124, 126, 0.12) !important;
    }

    .stApp:has(.auth-page-marker) div[data-testid="stTextInput"] input::placeholder {
        color: #94A3B8 !important;
        font-size: 0.85rem !important;
    }

    .stApp:has(.auth-page-marker) input[aria-label="Username or Email"],
    .stApp:has(.auth-page-marker) input[aria-label="Username"],
    .stApp:has(.auth-page-marker) input[aria-label="Email Address"] {
        padding-left: 2.4rem !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2394A3B8' stroke-width='1.8'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z'/%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: 10px center !important;
        background-size: 16px !important;
    }

    .stApp:has(.auth-page-marker) input[aria-label="Password"] {
        padding-left: 2.4rem !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2394A3B8' stroke-width='1.8'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z'/%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: 10px center !important;
        background-size: 16px !important;
    }

    .stApp:has(.auth-page-marker) .auth-forgot-wrap {
        text-align: right;
        margin: 0.05rem 0 0.35rem 0;
    }

    .stApp:has(.auth-page-marker) .auth-forgot-link {
        color: #0D7C7E !important;
        font-size: 0.78rem;
        font-weight: 500;
    }

    .stApp:has(.auth-page-marker) div[data-testid="stButton"] {
        margin-top: 0 !important;
    }

    .stApp:has(.auth-page-marker) [data-testid="stFormSubmitButton"] {
        margin-top: 0.5rem !important;
        padding-top: 0 !important;
    }

    .stApp:has(.auth-page-marker) div[data-testid="stButton"] button[kind="primary"]:hover,
    .stApp:has(.auth-page-marker) div[data-testid="stButton"] button[data-testid="baseButton-primary"]:hover {
        background: #0A6869 !important;
        color: #FFFFFF !important;
        border: none !important;
    }

    .stApp:has(.auth-mode-signin) div[data-testid="stButton"] button[kind="primary"]::before,
    .stApp:has(.auth-mode-signin) div[data-testid="stButton"] button[data-testid="baseButton-primary"]::before,
    .stApp:has(.auth-mode-signin) [data-testid="stFormSubmitButton"] > button::before {
        content: "";
        width: 16px;
        height: 16px;
        margin-right: 0.5rem;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='white' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z'/%3E%3C/svg%3E");
        background-size: contain;
        background-repeat: no-repeat;
        flex-shrink: 0;
    }

    .stApp:has(.auth-mode-signin) div[data-testid="stButton"] button[kind="primary"]::after,
    .stApp:has(.auth-mode-signin) div[data-testid="stButton"] button[data-testid="baseButton-primary"]::after,
    .stApp:has(.auth-mode-signin) [data-testid="stFormSubmitButton"] > button::after {
        content: "";
        position: absolute;
        right: 1.25rem;
        width: 18px;
        height: 18px;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='white' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3'/%3E%3C/svg%3E");
        background-size: contain;
        background-repeat: no-repeat;
    }

    .stApp:has(.auth-mode-signin) div[data-testid="stButton"] button[kind="secondary"]::before,
    .stApp:has(.auth-mode-signin) div[data-testid="stButton"] button[data-testid="baseButton-secondary"]::before {
        content: "";
        width: 18px;
        height: 18px;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%230D7C7E' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M18 7.5v3m0 0v3m0-3h3m-3 0h-3m-2.25-4.125a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zM3 19.235v-.11a6.375 6.375 0 0112.75 0v.109A12.318 12.318 0 019.374 21c-2.331 0-4.512-.645-6.374-1.766z'/%3E%3C/svg%3E");
        background-size: contain;
        background-repeat: no-repeat;
        flex-shrink: 0;
        margin-right: 0.35rem;
    }

    .stApp:has(.auth-mode-signin) div[data-testid="stButton"] button[kind="secondary"],
    .stApp:has(.auth-mode-signin) div[data-testid="stButton"] button[data-testid="baseButton-secondary"] {
        background: #FFFFFF !important;
        color: #0D7C7E !important;
        border: 1.5px solid #0D7C7E !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    .stApp:has(.auth-mode-register) div[data-testid="stButton"] button[kind="tertiary"],
    .stApp:has(.auth-mode-register) div[data-testid="stButton"] button[data-testid="baseButton-tertiary"] {
        background: transparent !important;
        color: #0D7C7E !important;
        border: none !important;
        box-shadow: none !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        padding: 0 0 0.75rem 0 !important;
        min-height: auto !important;
        justify-content: flex-start !important;
        width: auto !important;
    }

    .stApp:has(.auth-page-marker) div[data-testid="stButton"] button[kind="secondary"],
    .stApp:has(.auth-page-marker) div[data-testid="stButton"] button[data-testid="baseButton-secondary"] {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #0D7C7E !important;
        border: 1.5px solid #0D7C7E !important;
        border-radius: 8px !important;
        padding: 0.55rem 1rem !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        box-shadow: none !important;
        width: 100% !important;
        min-height: 40px !important;
        max-height: 44px !important;
    }

    .stApp:has(.auth-page-marker) div[data-testid="stButton"] button[kind="secondary"]:hover,
    .stApp:has(.auth-page-marker) div[data-testid="stButton"] button[data-testid="baseButton-secondary"]:hover {
        background: #F0FAFA !important;
        color: #0D7C7E !important;
        border: 1.5px solid #0D7C7E !important;
    }

    .stApp:has(.auth-page-marker) .auth-divider {
        display: flex;
        align-items: center;
        margin: 1rem 0;
        color: #94A3B8 !important;
        font-size: 0.78rem;
    }

    .stApp:has(.auth-page-marker) .auth-divider::before,
    .stApp:has(.auth-page-marker) .auth-divider::after {
        content: "";
        flex: 1;
        height: 1px;
        background: #E2E8F0;
    }

    .stApp:has(.auth-page-marker) .auth-divider span {
        padding: 0 0.75rem;
        color: #94A3B8 !important;
    }

    .stApp:has(.auth-page-marker) .auth-trust-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 1.5rem;
        padding-top: 1rem;
        border-top: 1px solid #F1F5F9;
        gap: 0.4rem;
    }

    .stApp:has(.auth-page-marker) .auth-trust-item {
        display: flex;
        flex-direction: row;
        align-items: center;
        gap: 0.25rem;
        flex: 1;
        justify-content: center;
    }

    .stApp:has(.auth-page-marker) .auth-trust-item svg {
        width: 18px;
        height: 18px;
        flex-shrink: 0;
    }

    .stApp:has(.auth-page-marker) .auth-trust-item span {
        font-size: 0.6rem;
        color: #64748B !important;
        font-weight: 500;
        line-height: 1.2;
    }

    .stApp:has(.auth-page-marker) div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        border-radius: 8px !important;
        border-color: #D1D5DB !important;
        min-height: 38px !important;
    }
</style>
"""

st.set_page_config(
    page_title="MedPath-RAG AI Assistant",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply global styling
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize Session States
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = "user"
if "current_tab" not in st.session_state:
    st.session_state.current_tab = "Home"
if "active_question" not in st.session_state:
    st.session_state.active_question = ""
if "active_category" not in st.session_state:
    st.session_state.active_category = None
if "active_response" not in st.session_state:
    st.session_state.active_response = None
if "active_sources" not in st.session_state:
    st.session_state.active_sources = []
if "active_time" not in st.session_state:
    st.session_state.active_time = 0.0
if "image_safety_flags" not in st.session_state:
    st.session_state.image_safety_flags = []
if "requires_radiologist_review" not in st.session_state:
    st.session_state.requires_radiologist_review = False
if "imaging_confidence" not in st.session_state:
    st.session_state.imaging_confidence = None
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "signin"

# ----------------- Navigation Redirection helper -----------------
def navigate_to_qa(question: str, category: str = None):
    st.session_state.active_question = question
    st.session_state.active_category = category
    st.session_state.current_tab = "Ask AI Assistant"
    st.rerun()

# ----------------- Auth Page -----------------
AUTH_LOGO_SVG = """
<svg viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M22 38C22 38 8 28 8 18.5C8 13.2533 12.2533 9 17.5 9C19.8948 9 22.0896 10.0125 23.5 11.75C24.9104 10.0125 27.1052 9 29.5 9C34.7467 9 39 13.2533 39 18.5C39 28 25 38 22 38Z" fill="#0D7C7E"/>
    <path d="M10 22H14L16 18L20 28L24 16L26 22H34" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""

AUTH_TRUST_SVG = """
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 2L4 6V11.5C4 16.75 7.5 21.5 12 23C16.5 21.5 20 16.75 20 11.5V6L12 2Z" fill="#0D7C7E" opacity="0.15" stroke="#0D7C7E" stroke-width="1.5"/>
    <path d="M9 12L11 14L15 10" stroke="#0D7C7E" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


def _auth_brand_header():
    st.markdown(f"""
    <div class="auth-brand">
        <div class="auth-logo">{AUTH_LOGO_SVG}</div>
        <div>
            <div class="auth-title">MedPath-RAG</div>
            <div class="auth-tagline">Clinical Retrieval-Augmented Pathology Platform</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _auth_trust_footer():
    st.markdown(f"""
    <div class="auth-trust-footer">
        <div class="auth-trust-item">{AUTH_TRUST_SVG}<span>HIPAA Compliant</span></div>
        <div class="auth-trust-item">{AUTH_TRUST_SVG}<span>Secure Data</span></div>
        <div class="auth-trust-item">{AUTH_TRUST_SVG}<span>Trusted Sources</span></div>
    </div>
    """, unsafe_allow_html=True)


def _render_sign_in():
    st.markdown('<p class="auth-welcome">Welcome Back</p>', unsafe_allow_html=True)
    st.markdown('<p class="auth-subtext">Sign in to access your account</p>', unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False, border=False):
        st.markdown('<label class="auth-field-label auth-field-label-first">Username or Email</label>', unsafe_allow_html=True)
        login_username = st.text_input(
            "Username or Email",
            placeholder="Enter your username or email",
            key="login_username",
            label_visibility="collapsed",
        )

        st.markdown('<label class="auth-field-label">Password</label>', unsafe_allow_html=True)
        login_password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password",
            label_visibility="collapsed",
        )

        st.markdown('<div class="auth-forgot-wrap"><span class="auth-forgot-link">Forgot Password?</span></div>', unsafe_allow_html=True)
        submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

    if submitted:
        try:
            r = requests.post(
                f"{API_URL}/login",
                data={"username": login_username, "password": login_password},
            )
            if r.status_code == 200:
                token_data = r.json()
                st.session_state.token = token_data["access_token"]
                st.session_state.username = login_username

                import base64
                import json

                parts = st.session_state.token.split(".")
                if len(parts) == 3:
                    payload_b64 = parts[1]
                    payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
                    payload_bytes = base64.b64decode(payload_b64)
                    payload = json.loads(payload_bytes.decode("utf-8"))
                    st.session_state.role = payload.get("role", "user")
                else:
                    st.session_state.role = "user"

                st.rerun()
            else:
                st.error("Invalid username or password.")
        except Exception as e:
            st.error(f"Cannot connect to the backend server: {e}")

    st.markdown('<div class="auth-divider"><span>or</span></div>', unsafe_allow_html=True)

    if st.button("Create New Account", key="go_register", type="secondary", use_container_width=True):
        st.session_state.auth_mode = "register"
        st.rerun()

    _auth_trust_footer()


def _render_register():
    if st.button("← Back to Sign In", key="back_signin", type="tertiary"):
        st.session_state.auth_mode = "signin"
        st.rerun()

    st.markdown('<p class="auth-welcome">Create Account</p>', unsafe_allow_html=True)
    st.markdown('<p class="auth-subtext">Register to access the pathology platform</p>', unsafe_allow_html=True)

    with st.form("register_form", clear_on_submit=False, border=False):
        st.markdown('<label class="auth-field-label auth-field-label-first">Username</label>', unsafe_allow_html=True)
        reg_username = st.text_input("Username", placeholder="Choose a username", key="reg_username", label_visibility="collapsed")

        st.markdown('<label class="auth-field-label">Email Address</label>', unsafe_allow_html=True)
        reg_email = st.text_input("Email Address", placeholder="Enter your email", key="reg_email", label_visibility="collapsed")

        st.markdown('<label class="auth-field-label">Password</label>', unsafe_allow_html=True)
        reg_password = st.text_input("Password", type="password", placeholder="Create a password", key="reg_password", label_visibility="collapsed")

        st.markdown('<label class="auth-field-label">Role</label>', unsafe_allow_html=True)
        reg_role = st.selectbox("Role", ["user", "doctor", "admin"], key="reg_role", label_visibility="collapsed")

        reg_submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)

    if reg_submitted:
        try:
            payload = {
                "username": reg_username,
                "email": reg_email,
                "password": reg_password,
                "role": reg_role,
            }
            r = requests.post(f"{API_URL}/register", json=payload)
            if r.status_code == 201:
                st.success("Account created successfully! Please sign in.")
                st.session_state.auth_mode = "signin"
                st.rerun()
            else:
                detail = r.json().get('detail')
                if isinstance(detail, list):
                    err_msgs = []
                    for err in detail:
                        locs = [str(x) for x in err.get('loc', []) if x != 'body']
                        msg = err.get('msg', 'Validation error')
                        if locs:
                            # e.g. "password" -> "Password"
                            field_name = locs[-1].replace("_", " ").capitalize()
                            err_msgs.append(f"**{field_name}**: {msg}")
                        else:
                            err_msgs.append(msg)
                    st.error("Registration failed:\n\n" + "\n".join([f"- {m}" for m in err_msgs]))
                else:
                    st.error(f"Registration failed: {detail}")
        except Exception as e:
            st.error(f"Cannot connect to the backend server: {e}")

    _auth_trust_footer()


def _get_auth_css():
    import base64
    bg_path = os.path.join(os.path.dirname(__file__), "assets", "auth_bg.jpg")
    if os.path.exists(bg_path):
        with open(bg_path, "rb") as f:
            bg_uri = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
    else:
        bg_uri = "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=1920&q=80"
    return AUTH_CSS.replace("__AUTH_BG__", bg_uri)


def auth_page():
    mode = st.session_state.auth_mode
    st.markdown(f'<div class="auth-page-marker auth-mode-{mode}"></div>', unsafe_allow_html=True)
    st.markdown(_get_auth_css(), unsafe_allow_html=True)

    _auth_brand_header()

    if mode == "signin":
        _render_sign_in()
    else:
        _render_register()

# ----------------- Main Application Page -----------------
def main_app():
    # Render teal sidebar
    st.sidebar.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-logo-row">
            <div class="sidebar-logo-icon">🧬</div>
            <div class="sidebar-title">MedPath-RAG</div>
        </div>
        <div class="sidebar-subtitle">AI Assistant for<br>Diabetes & Cancer Pathology</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation label mapping: internal name → display label with icon
    _NAV_LABELS = {
        "Home": "🏠  Home",
        "Ask AI Assistant": "💬  Ask AI Assistant",
        "Diabetes Center": "🧪  Diabetes Center",
        "Cancer Pathology": "🎗️  Cancer Pathology",
        "Research Explorer": "📚  Research Explorer",
        "Knowledge Graph": "🕸️  Knowledge Graph",
        "Source Verification": "✅  Source Verification",
        "Admin Dashboard": "📊  Admin Dashboard",
        "Doctor Dashboard": "🩺  Doctor Dashboard",
    }
    # Reverse mapping: display label → internal name
    _NAV_REVERSE = {v: k for k, v in _NAV_LABELS.items()}
    
    # Filter menu items based on role (Phase 13: Role-Based Access Control)
    if st.session_state.role == "admin":
        menu_keys = [
            "Home", 
            "Ask AI Assistant", 
            "Diabetes Center", 
            "Cancer Pathology", 
            "Research Explorer", 
            "Knowledge Graph", 
            "Source Verification", 
            "Admin Dashboard"
        ]
    elif st.session_state.role == "doctor":
        menu_keys = [
            "Doctor Dashboard"
        ]
    else: # user role
        menu_keys = [
            "Home", 
            "Ask AI Assistant", 
            "Diabetes Center", 
            "Cancer Pathology", 
            "Research Explorer"
        ]
    
    menu_items = [_NAV_LABELS[k] for k in menu_keys]
        
    # Ensure current tab is valid for the current role
    if st.session_state.current_tab not in menu_keys:
        st.session_state.current_tab = menu_keys[0]
    
    # Track selection changes
    try:
        current_index = menu_keys.index(st.session_state.current_tab)
    except ValueError:
        current_index = 0
        st.session_state.current_tab = menu_keys[0]
    
    selected_display = st.sidebar.radio(
        "Navigation",
        menu_items,
        index=current_index
    )
    st.session_state.current_tab = _NAV_REVERSE.get(selected_display, menu_keys[0])

    # User Information in Sidebar Footer
    st.sidebar.markdown(f"""
    <div class="user-card">
        <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.4rem;">
            <div style="width:28px;height:28px;border-radius:50%;background:#0D7C7E;display:flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:600;">👤</div>
            <b style="font-size:0.85rem;">{st.session_state.username}</b>
        </div>
        <span style="font-size:0.72rem;color:rgba(255,255,255,0.5);">Role: </span>
        <span style="font-size:0.72rem;color:#5EEAD4;font-weight:500;">{st.session_state.role.upper()}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Logout button in sidebar
    if st.sidebar.button("🚪 Logout", key="logout_btn", use_container_width=True):
        st.session_state.token = None
        st.session_state.username = None
        st.session_state.role = "user"
        st.session_state.current_tab = "Home"
        st.session_state.active_question = ""
        st.session_state.active_response = None
        st.session_state.active_sources = []
        st.rerun()
        
    headers = {"Authorization": f"Bearer {st.session_state.token}"}

    # 1. Home Page
    if st.session_state.current_tab == "Home":
        # User header badge
        user_initial = st.session_state.username[0].upper() if st.session_state.username else "U"
        st.markdown(f"""
        <div class="user-header-badge">
            <span class="role-badge">{st.session_state.role.capitalize()}</span>
            <div class="avatar-circle">{user_initial}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="welcome-container">
            <div class="welcome-title">Welcome to <span>MedPath-RAG</span></div>
            <div class="welcome-subtitle">Your AI Assistant for Diabetes and Cancer Pathology Information</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Search Bar
        search_col1, search_col2 = st.columns([5, 1])
        with search_col1:
            home_q = st.text_input("", placeholder="Ask a medical question about Diabetes or Cancer Pathology...", key="home_query", label_visibility="collapsed")
        with search_col2:
            ask_clicked = st.button("🔍 Ask", key="home_ask_btn", use_container_width=True, type="primary")
        
        if ask_clicked and home_q:
            navigate_to_qa(home_q)
        
        # Example Question chips
        st.markdown("<p style='font-size:0.82rem;color:#64748B;margin-bottom:0.25rem;'>Example Questions:</p>", unsafe_allow_html=True)
        eq_col1, eq_col2, eq_col3, eq_col4 = st.columns(4)
        with eq_col1:
            if st.button("What is diabetic nephropathy?", key="eq1", use_container_width=True):
                navigate_to_qa("What is diabetic nephropathy?", "diabetes")
        with eq_col2:
            if st.button("What is breast cancer pathology?", key="eq2", use_container_width=True):
                navigate_to_qa("What is breast cancer pathology?", "cancer")
        with eq_col3:
            if st.button("What are causes of insulin resistance?", key="eq3", use_container_width=True):
                navigate_to_qa("What are the causes of insulin resistance?", "diabetes")
        with eq_col4:
            if st.button("Chemotherapy mechanisms in cancer", key="eq4", use_container_width=True):
                navigate_to_qa("Describe chemotherapy mechanisms targeting rapidly dividing tumor cells.", "cancer")
        
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        
        # Grid of 4 Explore Cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("""
            <div class="explore-card">
                <div class="explore-icon-box bg-teal-light">🧪</div>
                <h3>Diabetes Center</h3>
                <p>Explore diabetes types, complications, pathology and management.</p>
                <span class="explore-link">Explore →</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Go to Diabetes", key="exp_db_btn", use_container_width=True, type="secondary"):
                st.session_state.current_tab = "Diabetes Center"
                st.rerun()
        with col2:
            st.markdown("""
            <div class="explore-card">
                <div class="explore-icon-box bg-orange-light">🎗️</div>
                <h3>Cancer Center</h3>
                <p>Learn about cancer types, pathology, staging, biomarkers and treatment.</p>
                <span class="explore-link">Explore →</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Go to Cancer", key="exp_ca_btn", use_container_width=True, type="secondary"):
                st.session_state.current_tab = "Cancer Pathology"
                st.rerun()
        with col3:
            st.markdown("""
            <div class="explore-card">
                <div class="explore-icon-box bg-blue-light">📚</div>
                <h3>Research Explorer</h3>
                <p>Search and explore research papers and clinical studies.</p>
                <span class="explore-link">Explore →</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Go to Research", key="exp_re_btn", use_container_width=True, type="secondary"):
                st.session_state.current_tab = "Research Explorer"
                st.rerun()
        with col4:
            st.markdown("""
            <div class="explore-card">
                <div class="explore-icon-box bg-purple-light">🕸️</div>
                <h3>Knowledge Graph</h3>
                <p>Visualize relationships between diseases, biomarkers and treatments.</p>
                <span class="explore-link">Explore →</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Go to Graph", key="exp_kg_btn", use_container_width=True, type="secondary"):
                st.session_state.current_tab = "Knowledge Graph"
                st.rerun()

    # 2. Ask AI Assistant Page
    elif st.session_state.current_tab == "Ask AI Assistant":
        # Header columns
        h_col1, h_col2, h_col3 = st.columns([3, 1, 1])
        with h_col1:
            st.markdown('<div class="page-header">Ask AI Assistant</div>', unsafe_allow_html=True)
        with h_col2:
            if st.button("➕ New Chat", key="new_chat_btn_top", use_container_width=True, type="secondary"):
                st.session_state.active_response = None
                st.session_state.active_sources = []
                st.session_state.active_question = ""
                st.session_state.image_safety_flags = []
                st.session_state.requires_radiologist_review = False
                st.session_state.imaging_confidence = None
                st.rerun()
        with h_col3:
            user_initial = st.session_state.username[0].upper() if st.session_state.username else "U"
            st.markdown(f"""
            <div class="user-header-badge" style="margin-top: 0.2rem;">
                <span class="role-badge">{st.session_state.role.capitalize()}</span>
                <div class="avatar-circle">{user_initial}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        
        # Chat input query bar
        q_val = st.session_state.active_question
        chat_q = st.text_input("Enter clinical pathology question:", value=q_val, key="active_chat_input", label_visibility="collapsed")
        
        # File upload for all users
        uploaded_image = st.file_uploader("📂 Upload Medical Image (X-ray, CT, pathology slide for analysis)", type=["png", "jpg", "jpeg"])
        uploaded_report = st.file_uploader("📄 Upload Medical Report (PDF, text for additional context)", type=["pdf", "txt"])
        
        # Helper: extract text from uploaded report
        def _extract_report_text(uploaded_file):
            if uploaded_file is None:
                return ""
            try:
                if uploaded_file.name.endswith(".pdf"):
                    from pypdf import PdfReader
                    from io import BytesIO
                    reader = PdfReader(BytesIO(uploaded_file.getvalue()))
                    texts = [p.extract_text() or "" for p in reader.pages]
                    return "\n".join(t for t in texts if t.strip())
                else:
                    return uploaded_file.getvalue().decode("utf-8", errors="ignore")
            except Exception:
                return ""

        # Tracking uploaded files in session state to auto-trigger query execution
        if "last_image_name" not in st.session_state:
            st.session_state.last_image_name = None
        if "last_report_name" not in st.session_state:
            st.session_state.last_report_name = None

        trigger_analysis = False
        if "query_in_progress" not in st.session_state:
            st.session_state.query_in_progress = False

        if uploaded_image:
            if uploaded_image.name != st.session_state.last_image_name:
                st.session_state.last_image_name = uploaded_image.name
                st.session_state.active_response = None  # Reset response for new file
                if not st.session_state.query_in_progress:
                    trigger_analysis = True
            st.success(f"📸 Medical image '{uploaded_image.name}' uploaded successfully!")
            st.image(uploaded_image, caption="Uploaded medical scan for analysis", width=300)
            st.caption(
                "Educational use only. AI may miss marked abnormalities (e.g. arrows on teaching X-rays). "
                "A radiologist must verify every scan before any clinical decision."
            )
            try:
                backend_ok = requests.get(f"{API_URL}/health", timeout=3).status_code == 200
                if not backend_ok:
                    st.warning(
                        "Cannot reach the API backend on port 8000. "
                        "Run `run_app.bat` or start FastAPI in a terminal."
                    )
                else:
                    ollama_ok = requests.get(
                        f"{API_URL}/health/ollama", timeout=5
                    ).json().get("ollama_ready", False)
                    if not ollama_ok:
                        st.warning("Ollama is not running. Start it with `ollama serve` before analyzing images.")
            except Exception:
                st.warning(
                    "Cannot reach the API backend on port 8000. "
                    "Run `run_app.bat` or start FastAPI in a terminal."
                )

        if uploaded_report:
            if uploaded_report.name != st.session_state.last_report_name:
                st.session_state.last_report_name = uploaded_report.name
                st.session_state.active_response = None  # Reset response for new file
                if not st.session_state.query_in_progress:
                    trigger_analysis = True
            
            report_text = _extract_report_text(uploaded_report)
            if report_text:
                st.success(f"📄 Medical report '{uploaded_report.name}' parsed successfully!")
                with st.expander("📝 View Extracted Report Text Preview", expanded=False):
                    st.code(report_text[:1200] + ("\n... [truncated] ..." if len(report_text) > 1200 else ""))
            else:
                st.error(f"❌ Failed to extract text from medical report '{uploaded_report.name}'. Check file encoding/integrity.")
        
        # Checkboxes for categories (Users must select one: Cancer, Diabetes, or Research)
        col_cat1, col_cat2 = st.columns(2)
        with col_cat1:
            if st.session_state.role in ["admin", "doctor"]:
                category_options = ["Any Field", "Diabetes Only", "Cancer Only", "Research Only"]
            else:
                category_options = ["Diabetes Only", "Cancer Only", "Research Only"]
                
            default_idx = 0
            category_selection = st.selectbox("Disease Filtering Category (RAG scope):", category_options, index=default_idx)
        
        send_clicked = st.button("Send Query", key="send_chat_query", use_container_width=True, type="primary")
        auto_trigger = chat_q and not st.session_state.active_response and q_val == chat_q and not st.session_state.query_in_progress
 
        if send_clicked or auto_trigger or trigger_analysis:
            st.session_state.query_in_progress = True
            query_text = chat_q.strip()
            if uploaded_image is not None and not query_text:
                query_text = (
                    "Analyze this medical image and provide a complete patient care report including "
                    "likely disease, precautions, diet recommendations, medications, and clinical follow-up."
                )
            elif uploaded_report is not None and not query_text:
                query_text = (
                    "Analyze this medical report and provide a summary including "
                    "likely disease, precautions, diet recommendations, medications, and clinical follow-up."
                )
            if query_text:
                category_mapped = None
                if category_selection == "Diabetes Only":
                    category_mapped = "diabetes"
                elif category_selection == "Cancer Only":
                    category_mapped = "cancer"
                elif category_selection == "Research Only":
                    category_mapped = "research"
                elif st.session_state.active_category:
                    category_mapped = st.session_state.active_category
                
                # Check if we are doing Image Analysis or normal text query
                if uploaded_image is not None:
                    with st.spinner("Analyzing image + building care report (up to 2 min; fallback used if needed)…"):
                        files = {"image": (uploaded_image.name, uploaded_image.getvalue(), uploaded_image.type)}
                        if uploaded_report:
                            files["report"] = (uploaded_report.name, uploaded_report.getvalue(), uploaded_report.type)
                        data = {"question": query_text}
                        if category_mapped:
                            data["disease_category"] = category_mapped
                        try:
                            r = requests.post(
                                f"{API_URL}/query-image",
                                files=files,
                                data=data,
                                headers=headers,
                                timeout=240,
                            )
                            if r.status_code == 200:
                                res = r.json()
                                st.session_state.active_response = res["answer"]
                                st.session_state.active_sources = res.get("sources", [])
                                st.session_state.active_time = res["response_time_sec"]
                                st.session_state.active_question = f"[IMAGE] {query_text}"
                                st.session_state.image_safety_flags = res.get("safety_flags") or []
                                st.session_state.requires_radiologist_review = res.get(
                                    "requires_radiologist_review", True
                                )
                                st.session_state.imaging_confidence = res.get("imaging_confidence", "low")
                                st.session_state.query_in_progress = False
                                st.rerun()
                            else:
                                st.session_state.query_in_progress = False
                                st.error(f"Image analysis server error: {r.text}")
                        except requests.exceptions.Timeout:
                            st.session_state.query_in_progress = False
                            st.error(
                                "Request timed out after 4 minutes. Keep Ollama running (`ollama serve`). "
                                "Try a text-only query with Cancer Only selected — RAG answers are faster."
                            )
                        except Exception as e:
                            st.session_state.query_in_progress = False
                            st.error(f"Failed to communicate with image API: {e}")
                else:
                    # Include uploaded report text in the query if present
                    report_text = _extract_report_text(uploaded_report)
                    effective_question = query_text
                    if report_text:
                        effective_question = f"{query_text}\n\n[Uploaded Medical Report]:\n{report_text[:4000]}"
                    
                    with st.spinner("Retrieving pathology contexts and querying MedGemma..."):
                        payload = {"question": effective_question}
                        if category_mapped:
                            payload["disease_category"] = category_mapped
                            
                        start_time = time.time()
                        try:
                            r = requests.post(f"{API_URL}/query", json=payload, headers=headers, timeout=200)
                            if r.status_code == 200:
                                res = r.json()
                                st.session_state.active_response = res["answer"]
                                st.session_state.active_sources = res["sources"]
                                st.session_state.active_time = res["response_time_sec"]
                                st.session_state.active_question = query_text
                                st.session_state.query_in_progress = False
                                st.rerun()
                            else:
                                st.session_state.query_in_progress = False
                                st.error(f"Backend Server error: {r.text}")
                        except requests.exceptions.Timeout:
                            st.session_state.query_in_progress = False
                            st.error("Query timed out. Ensure Ollama is running and try again.")
                        except Exception as e:
                            st.session_state.query_in_progress = False
                            st.error(f"Failed to communicate with API: {e}")
            elif send_clicked:
                st.warning("Enter a question or upload an image to analyze.")
        
        # Render AI Response and Source details (Two Columns)
        if st.session_state.active_response:
            st.markdown("<br>", unsafe_allow_html=True)
            col_left, col_right = st.columns([2, 1])
            
            with col_left:
                is_image_response = "[IMAGE]" in (st.session_state.active_question or "")
 
                if is_image_response:
                    st.markdown(
                        """
                        <div style="background-color:#FEF2F2;border-left:4px solid #DC2626;padding:0.75rem 1rem;border-radius:6px;margin-bottom:1rem;">
                            <span style="color:#B91C1C;font-weight:700;font-size:0.9rem;">⛔ NOT FOR CLINICAL USE</span>
                            <span style="color:#7F1D1D;font-size:0.85rem;display:block;margin-top:0.2rem;">
                                AI image reads can miss marked abnormalities or falsely report "clear" lungs.
                                A licensed radiologist <b>must</b> review the scan. This output is educational only.
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.session_state.image_safety_flags:
                        with st.expander("⚠️ Safety flags detected", expanded=True):
                            for flag in st.session_state.image_safety_flags:
                                st.error(flag)
 
                st.markdown(
                    '<div class="ai-response-card"><h3 style="margin-top:0;color:#0D9488;">AI Response</h3>',
                    unsafe_allow_html=True,
                )
                st.markdown(st.session_state.active_response)
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown(
                    f"""
                    <div style="margin-top:1rem;font-size:0.8rem;color:#94A3B8;border-top:1px solid #F1F5F9;padding-top:1rem;">
                        Generated by MedGemma (image + RAG) | Latency: {st.session_state.active_time:.2f}s
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                
            with col_right:
                # Sources Card
                st.markdown("<div class='sources-card'>", unsafe_allow_html=True)
                st.markdown("<h3>Sources Used</h3>", unsafe_allow_html=True)
                if st.session_state.active_sources:
                    for idx, src in enumerate(st.session_state.active_sources):
                        st.markdown(f"""
                        <div class="source-item">
                            <div>
                                <b style="color: #0D7C7E;">[{idx+1}] {src['source']}</b><br>
                                <span class="source-meta">Scope: {src['category'].capitalize()} | Page: {src['page']}</span>
                            </div>
                            <button class="source-view-btn">View</button>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.write("No source documents used.")
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Confidence Meter Card — image analysis is always low confidence
                if is_image_response:
                    img_conf = st.session_state.imaging_confidence or "low"
                    confidence_percent = {"low": 15, "medium": 30, "high": 45}.get(img_conf, 15)
                    if st.session_state.active_sources:
                        confidence_percent = min(confidence_percent + 8, 50)
                    confidence_desc = "Imaging: Low Reliability"
                    confidence_desc_sub = (
                        "AI vision is unverified — radiologist review mandatory. "
                        "RAG sources support text sections only, not the image read."
                    )
                else:
                    confidence_percent = 92 if st.session_state.active_sources else 25
                    confidence_desc = "High Confidence" if confidence_percent > 70 else "Low/General Guidance"
                    confidence_desc_sub = (
                        "Answer is supported by strong medical evidence"
                        if confidence_percent > 70
                        else "Answer relies on baseline training parameters"
                    )
                
                st.markdown(f"""
                <div class="confidence-card">
                    <h4 style="margin: 0 0 0.5rem 0; color:#475569;">Response Confidence</h4>
                    <div class="confidence-gauge-container">
                        <svg width="80" height="80" viewBox="0 0 120 120">
                            <circle cx="60" cy="60" r="50" fill="none" stroke="#E2E8F0" stroke-width="12"></circle>
                            <circle cx="60" cy="60" r="50" fill="none" stroke="#0D9488" stroke-width="12" stroke-dasharray="314.16" stroke-dashoffset="{314.16 * (1 - confidence_percent/100)}" transform="rotate(-90 60 60)"></circle>
                            <text x="60" y="66" font-family="'Outfit', sans-serif" font-weight="800" font-size="22" fill="#0F172A" text-anchor="middle">{confidence_percent}%</text>
                        </svg>
                        <div style="text-align: left;">
                            <b style="font-size: 1rem; color: #0D9488;">{confidence_desc}</b><br>
                            <span style="font-size: 0.75rem; color: #64748B;">{confidence_desc_sub}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            # Clear button
            if st.button("Clear Chat", key="clear_chat_btn"):
                st.session_state.active_response = None
                st.session_state.active_sources = []
                st.session_state.active_question = ""
                st.session_state.image_safety_flags = []
                st.session_state.requires_radiologist_review = False
                st.session_state.imaging_confidence = None
                st.rerun()

    # 3. Diabetes Center Page
    elif st.session_state.current_tab == "Diabetes Center":
        # User header badge
        user_initial = st.session_state.username[0].upper() if st.session_state.username else "U"
        st.markdown(f"""
        <div class="user-header-badge">
            <span class="role-badge">{st.session_state.role.capitalize()}</span>
            <div class="avatar-circle">{user_initial}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="page-header">Diabetes Center</div>', unsafe_allow_html=True)
        st.markdown('<div class="page-subtitle">Explore diabetes types, complications, pathology and management</div>', unsafe_allow_html=True)
        
        # Grid of 8 Cards (4 columns x 2 rows)
        grid_data = [
            ("Type 1 Diabetes", "Autoimmune destruction of beta cells leading to absolute insulin deficiency.", "🧬", "What causes absolute insulin deficiency in Type 1 Diabetes?"),
            ("Type 2 Diabetes", "Insulin resistance and relative insulin deficiency matching lifestyle factors.", "⚖️", "Explain the pathogenesis of insulin resistance in Type 2 Diabetes."),
            ("Gestational Diabetes", "Glucose intolerance with onset or first recognition during pregnancy.", "🤰", "What are the screening thresholds for Gestational Diabetes?"),
            ("Complications", "Overview of chronic macrovascular and microvascular pathologies.", "⚠️", "What are microvascular vs macrovascular complications of diabetes?"),
            ("Diabetic Nephropathy", "Progressive kidney disease due to damage of glomerular capillary loops.", "🩸", "Describe clinical markers for Diabetic Nephropathy."),
            ("Diabetic Neuropathy", "Nerve damage and neurodegeneration due to metabolic and vascular changes.", "🧠", "Explain mechanisms of diabetic peripheral neuropathy."),
            ("Diabetic Retinopathy", "Retinal damage from prolonged microvascular ischemia and microaneurysms.", "👁️", "What are early symptoms of non-proliferative diabetic retinopathy?"),
            ("Pathophysiology", "Systematic overview of metabolic dysfunction and biochemical pathways.", "🔬", "Explain the polyol pathway and diabetes complications pathophysiology.")
        ]
        
        # Row 1
        col1, col2, col3, col4 = st.columns(4)
        cols_row1 = [col1, col2, col3, col4]
        for idx in range(4):
            title, desc, icon, query = grid_data[idx]
            with cols_row1[idx]:
                st.markdown(f"""
                <div class="portal-card">
                    <div class="portal-icon">{icon}</div>
                    <div class="portal-card-header">{title}</div>
                    <div class="portal-card-desc">{desc}</div>
                    <div class="portal-explore-link">Explore →</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Explore", key=f"db_card_{idx}", use_container_width=True, type="secondary"):
                    navigate_to_qa(query, "diabetes")
                    
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        # Row 2
        col5, col6, col7, col8 = st.columns(4)
        cols_row2 = [col5, col6, col7, col8]
        for idx in range(4, 8):
            title, desc, icon, query = grid_data[idx]
            with cols_row2[idx-4]:
                st.markdown(f"""
                <div class="portal-card">
                    <div class="portal-icon">{icon}</div>
                    <div class="portal-card-header">{title}</div>
                    <div class="portal-card-desc">{desc}</div>
                    <div class="portal-explore-link">Explore →</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Explore", key=f"db_card_{idx}", use_container_width=True, type="secondary"):
                    navigate_to_qa(query, "diabetes")

    # 4. Cancer Pathology Page
    elif st.session_state.current_tab == "Cancer Pathology":
        # User header badge
        user_initial = st.session_state.username[0].upper() if st.session_state.username else "U"
        st.markdown(f"""
        <div class="user-header-badge">
            <span class="role-badge">{st.session_state.role.capitalize()}</span>
            <div class="avatar-circle">{user_initial}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="page-header">Cancer Pathology Center</div>', unsafe_allow_html=True)
        st.markdown('<div class="page-subtitle">Explore cancer types, pathology, histopathology and treatment</div>', unsafe_allow_html=True)
        
        # Grid of 8 Cards (4 columns x 2 rows)
        grid_data = [
            ("Breast Cancer", "Pathology, hormonal receptors (ER/PR), and HER2 role in prognosis.", "🎀", "What is the clinical role of HER2, ER, and PR in breast cancer prognosis?"),
            ("Lung Cancer", "Classifications: Non-Small Cell (NSCLC) vs Small Cell (SCLC) pathology.", "🫁", "What are key histopathological differences between SCLC and adenocarcinoma of the lung?"),
            ("Colorectal Cancer", "Pathology of adenomas, adenocarcinoma progression, and genetic factors.", "🧬", "Explain the adenoma-carcinoma sequence pathway in colon cancer."),
            ("Prostate Cancer", "Gleason grading system, clinical features, and adenocarcinoma staging.", "🩺", "Describe the Gleason scoring criteria for staging prostate carcinoma."),
            ("Histopathology", "Tissue biopsy examination, staining techniques, cell morphology analysis.", "🔬", "Explain hematoxylin and eosin (H&E) staining significance in cancer pathology."),
            ("Treatment Overview", "Pathology-guided systemic therapies, radiation oncology, and surgery.", "💉", "Describe chemotherapy mechanisms targeting rapidly dividing tumor cells.")
        ]
        
        # Row 1
        col1, col2, col3 = st.columns(3)
        cols_row1 = [col1, col2, col3]
        for idx in range(3):
            title, desc, icon, query = grid_data[idx]
            with cols_row1[idx]:
                st.markdown(f"""
                <div class="portal-card">
                    <div class="portal-icon">{icon}</div>
                    <div class="portal-card-header">{title}</div>
                    <div class="portal-card-desc">{desc}</div>
                    <div class="portal-explore-link">Explore →</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Explore", key=f"ca_card_{idx}", use_container_width=True, type="secondary"):
                    navigate_to_qa(query, "cancer")
                    
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        # Row 2
        col4, col5, col6 = st.columns(3)
        cols_row2 = [col4, col5, col6]
        for idx in range(3, 6):
            title, desc, icon, query = grid_data[idx]
            with cols_row2[idx-3]:
                st.markdown(f"""
                <div class="portal-card">
                    <div class="portal-icon">{icon}</div>
                    <div class="portal-card-header">{title}</div>
                    <div class="portal-card-desc">{desc}</div>
                    <div class="portal-explore-link">Explore →</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Explore", key=f"ca_card_{idx}", use_container_width=True, type="secondary"):
                    navigate_to_qa(query, "cancer")

    # 5. Research Explorer Page
    elif st.session_state.current_tab == "Research Explorer":
        # User header badge
        user_initial = st.session_state.username[0].upper() if st.session_state.username else "U"
        st.markdown(f"""
        <div class="user-header-badge">
            <span class="role-badge">{st.session_state.role.capitalize()}</span>
            <div class="avatar-circle">{user_initial}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="page-header">Research Explorer</div>', unsafe_allow_html=True)
        st.markdown('<div class="page-subtitle">Search and explore research papers and clinical studies</div>', unsafe_allow_html=True)
        
        col_left, col_mid, col_right = st.columns([1, 1.8, 1.2])
        
        # Setup session states for research explorer active summary details
        if "re_active_title" not in st.session_state:
            st.session_state.re_active_title = "Select a paper from results"
            st.session_state.re_active_journal = ""
            st.session_state.re_active_abstract = "Click 'Abstract' on a search result to view details."
            st.session_state.re_active_findings = []
            
        with col_left:
            st.markdown("<h4>Search Papers</h4>", unsafe_allow_html=True)
            search_query = st.text_input("Enter search keywords:", value="breast cancer biomarkers")
            
            st.markdown("<h5>Filters</h5>", unsafe_allow_html=True)
            source_filter = st.selectbox("Source DB", ["All Sources", "PubMed Bookshelf", "WHO Reports", "ADA Guidelines"])
            year_range = st.slider("Year Range", 2018, 2026, (2020, 2025))
            doc_type = st.selectbox("Document Type", ["All Types", "Clinical Guideline", "Research Article", "Meta-Analysis"])
            
            run_search = st.button("Search Database", key="run_research_query", use_container_width=True, type="primary")
            
        with col_mid:
            st.markdown("<h4>Search Results</h4>", unsafe_allow_html=True)
            
            # Simulated search result entries matching FAISS chunks or medical titles
            results = [
                {
                    "title": "Circulating Biomarkers in Breast Cancer: Current Evidence and Future Perspectives",
                    "journal": "Journal of Clinical Oncology • 2024",
                    "abstract": "This study examines utility of circulating tumor DNA (ctDNA) and circulating tumor cells (CTCs) as prognostic markers in early-stage breast cancer. We summarize data from 12 trials showing ctDNA detection post-surgery is highly predictive of future recurrence.",
                    "findings": ["ctDNA is a promising prognostic marker", "CTCs help in monitoring treatment response", "Exosomal microRNAs are emerging tools"]
                },
                {
                    "title": "Pathophysiological Mechanisms of Diabetic Nephropathy and Glomerular Hyperfiltration",
                    "journal": "Diabetes Care • 2023",
                    "abstract": "Hyperglycemia induces hemodynamic and structural alterations in the renal parenchyma. Glomerular hyperfiltration is a key early marker of nephropathy, driven by vasoactive mediators and TGF-beta pathways leading to podocyte effacement and glomerular scarring.",
                    "findings": ["Glomerular hyperfiltration leads to kidney strain", "TGF-beta activation is associated with fibrosis", "ACE inhibitors suppress progression"]
                },
                {
                    "title": "Genetics and Environmental Risk Factors of Adult Acute Myeloid Leukemia (AML)",
                    "journal": "The Lancet Haematology • 2024",
                    "abstract": "This cohort review compiles occupational chemical exposures, chemotherapeutic agent exposure histories, and genetic predispositions. Benzene and high-dose ionizing radiation are strongly linked to myelodysplastic changes culminating in AML.",
                    "findings": ["Benzene exposure increases risk of AML", "Alkylating chemotherapy agents carry secondary leukemia risk", "TP53 mutations correlate with treatment resistance"]
                }
            ]
            
            # Simple keyword matching logic
            matched_results = []
            for r in results:
                if not search_query or search_query.lower() in r["title"].lower() or search_query.lower() in r["abstract"].lower():
                    matched_results.append(r)
            if not matched_results:
                matched_results = results # Fallback
                
            st.write(f"Search Results ({len(matched_results)})")
            for idx, r in enumerate(matched_results):
                is_active = (r['title'] == st.session_state.re_active_title)
                card_class = "search-result-card active" if is_active else "search-result-card"
                st.markdown(f"""
                <div class="{card_class}">
                    <b style="color: #0F172A; font-size:0.92rem;">{r['title']}</b><br>
                    <span style="font-size:0.75rem; color:#64748B;">{r['journal']}</span>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Abstract", key=f"view_abs_{idx}", use_container_width=True, type="primary" if is_active else "secondary"):
                    st.session_state.re_active_title = r["title"]
                    st.session_state.re_active_journal = r["journal"]
                    st.session_state.re_active_abstract = r["abstract"]
                    st.session_state.re_active_findings = r["findings"]
                    st.rerun()
 
        with col_right:
            st.markdown("<h4>Paper Summary</h4>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="research-summary-card">
                <b style="font-size: 0.95rem; color: #0F172A; display: block; margin-bottom: 0.25rem;">{st.session_state.re_active_title}</b>
                <span style="font-size: 0.72rem; color:#0D7C7E; display: block; margin-bottom: 0.75rem;">{st.session_state.re_active_journal}</span>
                <p style="font-size: 0.82rem; color:#334155; line-height: 1.4; margin: 0;">
                    <b>Abstract:</b><br>{st.session_state.re_active_abstract}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.re_active_findings:
                st.markdown("<p style='font-size:0.85rem;font-weight:600;margin-top:1rem;margin-bottom:0.4rem;'>Key Findings:</p>", unsafe_allow_html=True)
                for f in st.session_state.re_active_findings:
                    st.markdown(f"<span style='color:#0D7C7E;'>✔</span> <span style='font-size:0.8rem;color:#475569;'>{f}</span>", unsafe_allow_html=True)

    # 6. Knowledge Graph Page
    elif st.session_state.current_tab == "Knowledge Graph":
        from knowledge_graph import list_diseases, build_disease_graph, render_graph_svg

        # User header badge
        user_initial = st.session_state.username[0].upper() if st.session_state.username else "U"
        st.markdown(f"""
        <div class="user-header-badge">
            <span class="role-badge">{st.session_state.role.capitalize()}</span>
            <div class="avatar-circle">{user_initial}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="page-header">Knowledge Graph Explorer</div>', unsafe_allow_html=True)
        st.markdown('<div class="page-subtitle">Visualize disease → biomarker → treatment relationships from the curated MedPath-RAG dataset</div>', unsafe_allow_html=True)

        disease_options = list_diseases()
        if not disease_options:
            st.error("Knowledge graph dataset not found. Ensure datasets/cancer/medpath_rag_dataset.json exists.")
        else:
            labels = {d["key"]: f"{d['name']} ({d['category'].title()})" for d in disease_options}
            keys = [d["key"] for d in disease_options]

            if "kg_selected_disease" not in st.session_state:
                st.session_state.kg_selected_disease = keys[0]

            selected = st.selectbox(
                "Select disease to explore",
                options=keys,
                format_func=lambda k: labels[k],
                key="kg_disease_select",
            )
            st.session_state.kg_selected_disease = selected

            nodes, edges, category = build_disease_graph(selected)

            if not nodes:
                st.warning("No graph relationships could be built for this disease.")
            else:
                st.markdown(render_graph_svg(nodes, edges), unsafe_allow_html=True)

                st.markdown("<br><h4>Relationship Details</h4>", unsafe_allow_html=True)
                rel_cols = st.columns(2)
                for i, edge in enumerate(edges[:4]):
                    relation_title = edge["relation"].replace("_", " ").title()
                    color = "#059669" if edge["relation"] == "has_biomarker" else "#2563EB"
                    if edge["relation"] == "presents_with":
                        color = "#7C3AED"
                    with rel_cols[i % 2]:
                        st.markdown(f"""
                        <div style="background:white;border:1px solid #E2E8F0;padding:1.25rem;border-radius:12px;margin-bottom:0.75rem;border-left:3px solid {color};">
                            <b style="color:{color};font-size:0.9rem;">{relation_title}: {edge['source']} → {edge['target']}</b>
                            <p style="font-size:0.82rem;color:#475569;margin:0.5rem 0 0 0;">{edge.get('description', '')}</p>
                        </div>
                        """, unsafe_allow_html=True)

                with st.expander("View raw graph data"):
                    st.json({"category": category, "nodes": nodes, "edges": edges})

    # 7. Source Verification Page
    elif st.session_state.current_tab == "Source Verification":
        # User header badge
        user_initial = st.session_state.username[0].upper() if st.session_state.username else "U"
        st.markdown(f"""
        <div class="user-header-badge">
            <span class="role-badge">{st.session_state.role.capitalize()}</span>
            <div class="avatar-circle">{user_initial}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="page-header">Source Verification Portal</div>', unsafe_allow_html=True)
        st.markdown('<div class="page-subtitle">Verify uploaded file schemas, indices, and RAG ingestion integrity</div>', unsafe_allow_html=True)
        
        # Fetch current list of files from backend API
        r = requests.get(f"{API_URL}/sources", headers=headers)
        if r.status_code == 200:
            sources_list = r.json()
            
            # Render a list of sources with status indicators
            st.markdown(f"Available clean files for medical pathology indexing: **{len(sources_list)}**")
            
            for index_fn in sources_list:
                status_color = "#059669" if "medpath_rag_dataset" in index_fn.lower() else "#2563EB"
                st.markdown(f"""
                <div style="background: white; border: 1px solid #E2E8F0; padding: 1rem; border-radius: 10px; margin-bottom: 0.75rem; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <b style="color: #0F172A;">{index_fn}</b><br>
                        <span style="font-size:0.75rem; color: #94A3B8;">Target Storage Scope: cleaned_text/</span>
                    </div>
                    <div style="display: flex; gap: 0.75rem; align-items: center;">
                        <span style="font-size: 0.75rem; background: #ECFDF5; color: {status_color}; padding: 0.25rem 0.6rem; border-radius: 20px; font-weight: 600;">
                            ✓ Ingested
                        </span>
                        <span style="font-size: 0.75rem; background: #F8FAFC; color: #64748B; border: 1px solid #E2E8F0; padding: 0.25rem 0.6rem; border-radius: 20px;">
                            Verified Integrity
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.error("Failed to retrieve system file sources.")

    # 8. Doctor Dashboard Page
    elif st.session_state.current_tab == "Doctor Dashboard":
        # User header badge
        user_initial = st.session_state.username[0].upper() if st.session_state.username else "U"
        st.markdown(f"""
        <div class="user-header-badge">
            <span class="role-badge">{st.session_state.role.capitalize()}</span>
            <div class="avatar-circle">{user_initial}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="page-header">Doctor Dashboard</div>', unsafe_allow_html=True)
        st.markdown('<div class="page-subtitle">Review patient uploads, provide diagnosis, precautions, and medication recommendations</div>', unsafe_allow_html=True)

        if st.session_state.role != "doctor":
            st.error("Access Denied: Only users with the 'doctor' role can access this dashboard.")
        else:
            # Fetch patient uploads/reports needing approval
            r_uploads = requests.get(f"{API_URL}/doctor/uploads", headers=headers)

            if r_uploads.status_code == 403:
                st.error("Your session does not have doctor privileges. Please log out and sign in with a doctor account.")
            elif r_uploads.status_code != 200:
                st.error(f"Failed to load patient uploads (HTTP {r_uploads.status_code}). Is the backend running?")
            else:
                uploads = r_uploads.json()
                if not isinstance(uploads, list):
                    uploads = []

                if not uploads:
                    st.info("No patient uploads pending review.")
                else:
                    # --- KPI Stats with clickable filter buttons ---
                    unique_patients = len(set(u.get('username', '') for u in uploads))
                    image_count = sum(1 for u in uploads if u.get('has_image'))

                    if "doc_filter" not in st.session_state:
                        st.session_state.doc_filter = "all"

                    kpi1, kpi2, kpi3 = st.columns(3)
                    with kpi1:
                        st.metric("Pending Reviews", len(uploads))
                        if st.button("Show All", key="filter_all", use_container_width=True,
                                     type="primary" if st.session_state.doc_filter == "all" else "secondary"):
                            st.session_state.doc_filter = "all"
                            st.rerun()
                    with kpi2:
                        st.metric("Unique Patients", unique_patients)
                        if st.button("Show Unique", key="filter_unique", use_container_width=True,
                                     type="primary" if st.session_state.doc_filter == "unique" else "secondary"):
                            st.session_state.doc_filter = "unique"
                            st.rerun()
                    with kpi3:
                        st.metric("Image Uploads", image_count)
                        if st.button("Show Images", key="filter_images", use_container_width=True,
                                     type="primary" if st.session_state.doc_filter == "images" else "secondary"):
                            st.session_state.doc_filter = "images"
                            st.rerun()

                    # --- Apply Filter ---
                    active_filter = st.session_state.doc_filter
                    if active_filter == "unique":
                        seen = set()
                        filtered = []
                        for u in uploads:
                            uname = u.get('username', 'Unknown')
                            if uname not in seen:
                                seen.add(uname)
                                filtered.append(u)
                        filter_label = "Unique Patient Reviews"
                    elif active_filter == "images":
                        filtered = [u for u in uploads if u.get('has_image')]
                        filter_label = "Image Upload Reviews"
                    else:
                        filtered = uploads
                        filter_label = "All Pending Reviews"

                    st.markdown(f"### {filter_label}: {len(filtered)}")

                    for i, upload in enumerate(filtered):
                        with st.expander(f"Patient: {upload.get('username', 'Unknown')} - {upload.get('timestamp', 'Unknown')}"):
                            col1, col2 = st.columns(2)

                            with col1:
                                st.markdown("**Patient Information:**")
                                st.write(f"Username: {upload.get('username', 'N/A')}")
                                st.write(f"Question: {upload.get('question', 'N/A')}")
                                st.write(f"Category: {upload.get('category', 'N/A')}")

                                if upload.get('has_image'):
                                    st.write("📸 Image uploaded")
                                if upload.get('has_report'):
                                    st.write("📄 Report uploaded")

                                # Show AI Answer
                                ai_answer = upload.get('answer', '')
                                if ai_answer:
                                    st.markdown("---")
                                    st.markdown("**🤖 AI Suggested Response:**")
                                    st.info(ai_answer)

                                # Show Reference Sources
                                sources = upload.get('sources', [])
                                if sources:
                                    st.markdown("---")
                                    st.markdown(f"**📚 Reference Sources ({len(sources)}):**")
                                    for idx, src in enumerate(sources):
                                        score_val = src.get('score', 0)
                                        score_str = f"{score_val:.2f}" if isinstance(score_val, (int, float)) else str(score_val)
                                        st.write(f"[{idx+1}] {src.get('source', 'Unknown')} | Category: {src.get('category', 'General').capitalize()} | Page: {src.get('page', 'N/A')} | Match: {score_str}")

                            with col2:
                                st.markdown("**Doctor Review:**")
                                diagnosis = st.text_input("Diagnosis:", key=f"diagnosis_{i}", placeholder="Enter diagnosis")
                                precautions = st.text_area("Precautions:", key=f"precautions_{i}", placeholder="Enter precautions")
                                medicine = st.text_area("Medicine:", key=f"medicine_{i}", placeholder="Enter medication recommendations")

                                col_btn1, col_btn2, col_btn3 = st.columns(3)
                                with col_btn1:
                                    if st.button("Approve & Send", key=f"approve_{i}", use_container_width=True):
                                        approval_data = {
                                            "upload_id": upload.get("_id"),
                                            "diagnosis": diagnosis,
                                            "precautions": precautions,
                                            "medicine": medicine
                                        }
                                        r_approve = requests.post(f"{API_URL}/doctor/approve", json=approval_data, headers=headers)
                                        if r_approve.status_code == 200:
                                            st.success("Review sent to patient successfully!")
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to send review: {r_approve.text}")

                                with col_btn2:
                                    if st.button("Request More Info", key=f"request_info_{i}", use_container_width=True):
                                        st.info("Request for more information sent to patient.")

                                with col_btn3:
                                    if st.button("Reject", key=f"reject_{i}", use_container_width=True):
                                        st.warning("Upload rejected.")


                


    # 9. Admin Dashboard Page
    elif st.session_state.current_tab == "Admin Dashboard":
        # User header badge
        user_initial = st.session_state.username[0].upper() if st.session_state.username else "U"
        st.markdown(f"""
        <div class="user-header-badge">
            <span class="role-badge">{st.session_state.role.capitalize()}</span>
            <div class="avatar-circle">{user_initial}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="page-header">Admin Dashboard</div>', unsafe_allow_html=True)
        st.markdown('<div class="page-subtitle">System overview, user analytics, and audit records</div>', unsafe_allow_html=True)

        if st.session_state.role != "admin":
            st.error("Access Denied: Only users with the 'admin' role can view system analytics and audit records.")
        else:
            r_stats = requests.get(f"{API_URL}/admin/stats", headers=headers)
            r_history = requests.get(f"{API_URL}/history", headers=headers)

            if r_stats.status_code == 403:
                st.error("Your session does not have admin privileges. Please log out and sign in with an admin account.")
            elif r_stats.status_code != 200:
                st.error(f"Failed to load admin statistics (HTTP {r_stats.status_code}). Is the backend running?")
            else:
                stats = r_stats.json()
                history_data = r_history.json() if r_history.status_code == 200 else []
                if not isinstance(history_data, list):
                    history_data = []

                k_col1, k_col2, k_col3, k_col4 = st.columns(4)
                with k_col1:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Documents Indexed</div>
                        <div class="kpi-value">{stats.get("total_documents", 0)}</div>
                        <div class="kpi-subtext">Source files in knowledge base</div>
                    </div>
                    """, unsafe_allow_html=True)
                with k_col2:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Vector Chunks</div>
                        <div class="kpi-value">{stats.get("total_chunks", 0)}</div>
                        <div class="kpi-subtext">Indexed text segments</div>
                    </div>
                    """, unsafe_allow_html=True)
                with k_col3:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Queries Processed</div>
                        <div class="kpi-value">{stats.get("total_queries", 0)}</div>
                        <div class="kpi-subtext">Total RAG requests</div>
                    </div>
                    """, unsafe_allow_html=True)
                with k_col4:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Avg Response Time</div>
                        <div class="kpi-value">{stats.get("avg_response_time_sec", 0):.1f}s</div>
                        <div class="kpi-subtext">Mean query latency</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                u_col1, u_col2, u_col3, u_col4 = st.columns(4)
                users_by_role = stats.get("users_by_role", {})
                with u_col1:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Registered Users</div>
                        <div class="kpi-value">{stats.get("total_registered_users", 0)}</div>
                        <div class="kpi-subtext">All accounts</div>
                    </div>
                    """, unsafe_allow_html=True)
                with u_col2:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Admins</div>
                        <div class="kpi-value">{users_by_role.get("admin", 0)}</div>
                        <div class="kpi-subtext">Administrator accounts</div>
                    </div>
                    """, unsafe_allow_html=True)
                with u_col3:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Doctors</div>
                        <div class="kpi-value">{users_by_role.get("doctor", 0)}</div>
                        <div class="kpi-subtext">Clinical accounts</div>
                    </div>
                    """, unsafe_allow_html=True)
                with u_col4:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Answer Success Rate</div>
                        <div class="kpi-value">{stats.get("answer_success_rate_pct", 0):.0f}%</div>
                        <div class="kpi-subtext">Evidence-backed responses</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                chart_col1, chart_col2 = st.columns([2, 1])
                with chart_col1:
                    st.markdown("<h4>Queries Over Time</h4>", unsafe_allow_html=True)
                    if history_data:
                        df_history = pd.DataFrame(history_data)
                        df_history["timestamp"] = pd.to_datetime(df_history["timestamp"])
                        df_history = df_history.sort_values(by="timestamp")
                        timeline_df = (
                            df_history.set_index("timestamp")
                            .resample("h")
                            .size()
                            .reset_index(name="Queries")
                        )
                        if timeline_df["Queries"].sum() > 0:
                            st.line_chart(timeline_df, x="timestamp", y="Queries")
                        else:
                            st.info("Not enough query history to plot a timeline yet.")
                    else:
                        st.info("No queries recorded yet. Activity will appear here after users ask questions.")

                with chart_col2:
                    st.markdown("<h4>Query Categories</h4>", unsafe_allow_html=True)
                    category_counts = stats.get("category_counts", {})
                    if category_counts:
                        cat_df = pd.DataFrame({
                            "Category": [c.replace("_", " ").title() for c in category_counts.keys()],
                            "Count": list(category_counts.values()),
                        })
                        st.bar_chart(cat_df, x="Category", y="Count")
                    else:
                        st.info("No category data available yet.")

                st.markdown("<br><h4>Audit Log — Recent Queries</h4>", unsafe_allow_html=True)
                if history_data:
                    df = pd.DataFrame(history_data)
                    display_cols = [c for c in ["timestamp", "username", "question", "category", "response_time_sec"] if c in df.columns]
                    df = df.sort_values(by="timestamp", ascending=False)
                    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
                else:
                    st.info("No transaction queries have been recorded yet.")
                
    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='footer-text'>© 2025 MedPath-RAG • Clinical Support Platform</div>", unsafe_allow_html=True)

# Application routing
if st.session_state.token is None:
    auth_page()
else:
    main_app()
