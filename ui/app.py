#!/usr/bin/env python3
"""
Minimal Streamlit UI for Local RAG System.
"""

import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")
DEFAULT_USERNAME = os.getenv("STREAMLIT_DEFAULT_USER", "admin")
DEFAULT_PASSWORD = os.getenv("STREAMLIT_DEFAULT_PASSWORD", "")

st.set_page_config(
    page_title="Local RAG",
    page_icon="🔍",
    layout="centered"
)

def check_health():
    try:
        resp = requests.get(f"{API_URL}/health", timeout=5)
        return resp.json() if resp.status_code == 200 else None
    except:
        return None

def login(username, password):
    try:
        resp = requests.post(
            f"{API_URL}/token",
            json={"username": username, "password": password},
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
    except:
        pass
    return None

def query_rag(query, token):
    try:
        resp = requests.post(
            f"{API_URL}/query",
            json={"question": query},
            headers={"Authorization": f"Bearer {token}"},
            timeout=120
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        return {"error": str(e)}
    return {"error": "Request failed"}

# Initialize session state
if "token" not in st.session_state:
    st.session_state.token = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

st.title("🔍 Local RAG System")

# Health check
health = check_health()
if health:
    st.success(f"✓ API Healthy | {health.get('documents_count', 0)} documents | Model: {health.get('model', 'N/A')}")
else:
    st.error("✗ API not available")

# Login form
if not st.session_state.logged_in:
    with st.form("login"):
        st.subheader("Login")
        username = st.text_input("Username", value=DEFAULT_USERNAME)
        password = st.text_input("Password", type="password", value=DEFAULT_PASSWORD)
        submitted = st.form_submit_button("Enter")
        if submitted:
            token = login(username, password)
            if token:
                st.session_state.token = token
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials")
else:
    st.success(f"Logged in as: admin")
    
    # Query form
    st.subheader("Ask a question")
    question = st.text_area("Your question:", placeholder="What would you like to know?", height=100)
    
    if st.button("Search", type="primary"):
        if question:
            with st.spinner("Searching..."):
                result = query_rag(question, st.session_state.token)
            
            if "error" in result:
                st.error(result["error"])
            else:
                st.subheader("Answer")
                st.write(result.get("answer", "No answer"))
                
                sources = result.get("sources", [])
                if sources:
                    st.subheader("Sources")
                    for i, src in enumerate(sources[:3], 1):
                        with st.expander(f"Source {i}"):
                            st.write(src.get("content", "")[:500])
        else:
            st.warning("Please enter a question")
    else:
        st.info("Ask a question above")