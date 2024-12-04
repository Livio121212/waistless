import streamlit as st
from datetime import datetime, timedelta
import json
from .recipe_config import CACHE_DURATION

def initialize_cache():
    """Initialize cache in session state"""
    if "api_cache" not in st.session_state:
        st.session_state["api_cache"] = {}
    if "last_cache_cleanup" not in st.session_state:
        st.session_state["last_cache_cleanup"] = datetime.now()

def cleanup_cache():
    """Remove expired cache entries"""
    current_time = datetime.now()
    if current_time - st.session_state["last_cache_cleanup"] > timedelta(hours=1):
        expired = []
        for key, (timestamp, _) in st.session_state["api_cache"].items():
            if current_time - timestamp > timedelta(hours=CACHE_DURATION):
                expired.append(key)
        for key in expired:
            del st.session_state["api_cache"][key]
        st.session_state["last_cache_cleanup"] = current_time

def get_cache_key(ingredients, params):
    """Generate a cache key from ingredients and parameters"""
    return f"{'-'.join(sorted(ingredients))}-{json.dumps(params, sort_keys=True)}"

def get_cached_recipes(cache_key):
    """Get recipes from cache if available"""
    if cache_key in st.session_state["api_cache"]:
        timestamp, cached_data = st.session_state["api_cache"][cache_key]
        if datetime.now() - timestamp <= timedelta(hours=CACHE_DURATION):
            return cached_data
    return None

def cache_recipes(cache_key, data):
    """Cache recipe data"""
    st.session_state["api_cache"][cache_key] = (datetime.now(), data)
