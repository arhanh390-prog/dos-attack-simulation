import streamlit as st
import time
import random

# --- Page Configuration ---
st.set_page_config(
    page_title="DoS Attack Simulation",
    page_icon="🛡️",
    layout="wide"
)

# --- Server & Simulation Parameters ---
SERVER_CAPACITY = 20  # Max requests server can handle at once
REQUEST_PROCESSING_TIME = 0.05  # Time to process one request
ATTACK_STRENGTH = 5       # Number of fake requests per attacker "click"

# --- Session State Initialization ---
# This function initializes all the variables we need to keep track of.
def init_session_state():
    if 'server_load' not in st.session_state:
        st.session_state.server_load = 0
    if 'attacker_active' not in st.session_state:
        st.session_state.attacker_active = False
    if 'server_logs' not in st.session_state:
        st.session_state.server_logs = []
    if 'user_message' not in st.session_state:
        st.session_state.user_message = ""
    if 'server_status' not in st.session_state:
        st.session_state.server_status = "✅ Idle"
    if 'attack_running' not in st.session_state:
        st.session_state.attack_running = False

init_session_state()

# --- Helper Functions ---

def add_log(log_message, log_type="info"):
    """Adds a new message to the server logs."""
    timestamp = time.strftime("%H:%M:%S")
    color = "gray"
    if log_type == "attack":
        color = "red"
    elif log_type == "user":
        color = "blue"
    elif log_type == "server":
        color = "green"
    
    st.session_state.server_logs.insert(0, f"[{timestamp}] <span style='color:{color};'>{log_message}</span>")
    # Keep logs from getting too long
    if len(st.session_state.server_logs) > 20:
        st.session_state.server_logs.pop()

def process_server_load():
    """Simulates the server processing its request queue."""
    if st.session_state.server_load > 0:
        # Server processes some requests
        processed = max(1, int(st.session_state.server_load * 0.1)) # Process 10% of load
        st.session_state.server_load = max(0, st.session_state.server_load - processed)
        
        if st.session_state.server_load == 0:
            add_log("Server load cleared. Back to Idle.", "server")
            st.session_state.server_status = "✅ Idle"

# --- Main App Layout ---
st.title("🛡️ Denial of Service (DoS) Attack Simulation")
st.markdown("This is an educational simulation to demonstrate how a DoS attack works. No real network traffic is generated.")
st.markdown("---")

# --- UI Columns ---
col_attacker, col_server, col_user = st.columns(3, gap="large")

# --- 1. Attacker Column ---
with col_attacker:
    st.header("🥷 Attacker")
    st.markdown("The attacker floods the server with fake requests to overwhelm it.")
    
    st.session_state.attack_running = st.toggle("Activate Attack Bot", value=st.session_state.attack_running)
    
    if st.session_state.attack_running:
        st.warning("Attack in Progress!")
        # Simulate a continuous flood of requests
        fake_requests = random.randint(1, ATTACK_STRENGTH)
        if st.session_state.server_load + fake_requests <= SERVER_CAPACITY * 1.5: # Allow some over-capacity
            st.session_state.server_load += fake_requests
            add_log(f"Injected {fake_requests} fake requests.", "attack")
        else:
            add_log("Server max capacity reached. Dropping packets.", "attack")
        
        # This line is no longer needed, server column handles status display
        # st.session_state.server_status = "🔥 UNDER ATTACK" 
    else:
        st.info("Attacker is Idle.")
        # This logic is now handled by the server column
        # if st.session_state.server_status == "🔥 UNDER ATTACK" and st.session_state.server_load == 0:
        #      st.session_state.server_status = "✅ Idle"


# --- 2. Server Column ---
with col_server:
    st.header(f"🖥️ Server (Capacity: {SERVER_CAPACITY})")
    
    # Server Status & Load
    load_percent = min(1.0, st.session_state.server_load / SERVER_CAPACITY)
    
    # --- UPDATED STATUS LOGIC ---
    # Check for attack status FIRST
    if st.session_state.attack_running:
        st.session_state.server_status = "🔥 UNDER ATTACK"
        st.error(f"Status: {st.session_state.server_status}")
    # If no attack, then check load
    elif load_percent > 0.8:
        st.session_state.server_status = "🆘 Overloaded"
        st.error(f"Status: {st.session_state.server_status}")
    elif load_percent > 0.5:
        st.session_state.server_status = "⚠️ High Load"
        st.warning(f"Status: {st.session_state.server_status}")
    else:
        st.session_state.server_status = "✅ Stable" if st.session_state.server_load > 0 else "✅ Idle"
        st.success(f"Status: {st.session_state.server_status}")
    # --- END UPDATED STATUS LOGIC ---


    st.markdown(f"**Current Load:** `{st.session_state.server_load}` / `{SERVER_CAPACITY}`")
    st.progress(load_percent)

    # Server Logs
    st.subheader("Server Logs")
    log_placeholder = st.empty()
    with log_placeholder.container(height=300):
        for log in st.session_state.server_logs:
            st.markdown(log, unsafe_allow_html=True)

# --- 3. Authentic User Column ---
with col_user:
    st.header("👤 Authentic User")
    st.markdown("The user is just trying to log in, but the server might be too busy.")
    
    with st.form("login_form"):
        st.text_input("Login ID", value="user@example.com", disabled=True)
        st.text_input("Password", value="••••••••", type="password", disabled=True)
        login_button = st.form_submit_button("Attempt Login")

    if login_button:
        # Check if server has capacity for one more request
        if st.session_state.server_load + 1 <= SERVER_CAPACITY:
            st.session_state.server_load += 1
            add_log("Processing valid login request...", "user")
            st.session_state.user_message = "Logging in... server is processing."
            
            # Simulate processing time
            time.sleep(REQUEST_PROCESSING_TIME * 5) # Give login a bit more time
            
            # Check if server *still* has capacity (it might have filled up)
            if st.session_state.server_load > SERVER_CAPACITY:
                 st.session_state.user_message = "❌ Login Failed! Server timed out (Error 503)."
                 add_log("Login request timed out due to high load.", "server")
            else:
                st.session_state.user_message = "✅ Login Successful! Welcome."
                add_log("Login successful.", "user")
            
            # User logs out, freeing up the slot
            st.session_state.server_load = max(0, st.session_state.server_load - 1)

        else:
            # Server is at full capacity
            add_log("Connection attempt from user failed. Server busy.", "server")
            st.session_state.user_message = "❌ Login Failed! Server is too busy (Error 503)."
            
    # Display the user's status message
    if "Successful" in st.session_state.user_message:
        st.success(st.session_state.user_message)
    elif "Failed" in st.session_state.user_message:
        st.error(st.session_state.user_message)
    else:
        st.info(st.session_state.user_message)

# --- Simulation Loop Control ---

# Simulate the server processing its queue
process_server_load()

# Add a small delay and rerun to create the "live" effect
time.sleep(0.5)
st.rerun()
