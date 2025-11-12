import streamlit as st
import time
import random
import pandas as pd

# --- Page Configuration ---
st.set_page_config(
    page_title="DDoS Attack Simulation",
    page_icon="🛡️",
    layout="wide"
)

# --- Server & Simulation Parameters ---
BASE_SERVER_CAPACITY = 20  # Max requests server can handle at once
REQUEST_PROCESSING_TIME = 0.05  # Time to process one request
ATTACK_STRENGTH = 3       # Number of fake requests per bot
RATE_LIMIT_PER_TICK = 10  # Max requests "from attacker" allowed per tick if rate limiting is on

# --- Session State Initialization ---
def init_session_state():
    defaults = {
        'server_load': 0,
        'server_capacity': BASE_SERVER_CAPACITY,
        'server_logs': [],
        'user_message': "",
        'server_status': "✅ Idle",
        'attack_running': False,
        'num_bots': 1,
        'rate_limiting_enabled': False,
        'auto_scaling_enabled': False,
        'attacker_blocked': False,
        'attack_type': "Volume Flood",
        'load_history': pd.DataFrame(columns=['Time', 'Server Load', 'Capacity']),
        'simulation_time': 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- Helper Functions ---

def add_log(log_message, log_type="info"):
    """Adds a new message to the server logs."""
    timestamp = time.strftime("%H:%M:%S")
    color_map = {
        "attack": "red",
        "user": "blue",
        "server": "green",
        "defense": "orange",
        "info": "gray"
    }
    color = color_map.get(log_type, "gray")
    
    st.session_state.server_logs.insert(0, f"[{timestamp}] <span style='color:{color};'>{log_message}</span>")
    if len(st.session_state.server_logs) > 20:
        st.session_state.server_logs.pop()

def process_server_load():
    """Simulates the server processing its request queue and auto-scaling."""
    
    # 1. Process existing load
    if st.session_state.server_load > 0:
        # Simplified: Normal processing, 10% of load per tick
        processed = max(1, int(st.session_state.server_load * 0.1)) # Process 10%
        st.session_state.server_load = max(0, st.session_state.server_load - processed)
        
        if st.session_state.server_load == 0 and not st.session_state.attack_running:
            add_log("Server load cleared. Back to Idle.", "server")

    # 2. Handle Auto-Scaling
    if st.session_state.auto_scaling_enabled:
        load_percent = st.session_state.server_load / st.session_state.server_capacity
        
        # Scale Up
        if load_percent > 0.9:
            new_capacity = st.session_state.server_capacity + BASE_SERVER_CAPACITY
            st.session_state.server_capacity = new_capacity
            add_log(f"Auto-scaling UP! New capacity: {new_capacity}", "server")
        
        # Scale Down
        elif load_percent < 0.3 and st.session_state.server_capacity > BASE_SERVER_CAPACITY:
            # Only scale down if load is low and we're not at base capacity
            new_capacity = max(BASE_SERVER_CAPACITY, st.session_state.server_capacity - BASE_SERVER_CAPACITY)
            st.session_state.server_capacity = new_capacity
            add_log(f"Auto-scaling DOWN. New capacity: {new_capacity}", "server")

# --- Main App Layout ---
st.title("🛡️ Distributed Denial of Service (DDoS) Simulation")
st.markdown("This educational simulation demonstrates how a DDoS attack works and the effect of common defenses.")
st.markdown("---")

# --- UI Columns ---
col_attacker, col_server, col_user = st.columns(3, gap="large")

# --- 1. Attacker Column ---
with col_attacker:
    st.header("🥷 Attacker (Botnet)")
    st.markdown("The attacker uses a botnet to flood the server with fake requests.")
    
    st.session_state.attack_type = st.selectbox("Attack Type", ["Volume Flood", "Slow Connection Attack"])
    st.session_state.num_bots = st.slider("Number of Bots", min_value=1, max_value=100, value=st.session_state.num_bots)
    st.session_state.attack_running = st.toggle("Activate Attack Botnet", value=st.session_state.attack_running)
    
    if st.session_state.attacker_blocked:
        st.error("ATTACK FAILED: Your IP has been blocked by the server's firewall.")
        st.session_state.attack_running = False
    
    elif st.session_state.attack_running:
        st.warning("Attack in Progress!")
        
        # 1. Calculate total requests from botnet
        if st.session_state.attack_type == "Volume Flood":
            fake_requests = random.randint(1, ATTACK_STRENGTH) * st.session_state.num_bots
            add_log(f"Botnet injecting {fake_requests} 'Volume' requests.", "attack")
        else: # Slow Connection Attack
            # Each "slow" bot consumes more server resources (e.g., 10 units)
            load_impact_per_bot = 10 
            fake_requests = st.session_state.num_bots * load_impact_per_bot
            add_log(f"Botnet initiating {st.session_state.num_bots} 'Slow' requests, consuming {fake_requests} load units.", "attack")

        # 2. Check for Rate Limiting
        accepted_requests = fake_requests
        if st.session_state.rate_limiting_enabled:
            accepted_requests = min(fake_requests, RATE_LIMIT_PER_TICK)
            blocked_requests = fake_requests - accepted_requests
            if blocked_requests > 0:
                add_log(f"Rate limiter blocked {blocked_requests} requests.", "defense")
        
        # 3. Add accepted requests to server load
        if st.session_state.server_load + accepted_requests <= st.session_state.server_capacity * 1.5: # Allow some over-capacity
            st.session_state.server_load += accepted_requests
        else:
            add_log("Server max capacity reached. Dropping packets.", "server")
    
    else:
        st.info("Attacker is Idle.")
        # Removed 'Reset Block' button from here, moved 'Unblock' to server column


# --- 2. Server & Defenses Column ---
with col_server:
    st.header(f"🖥️ Server & Defenses")
    
    # Server Status & Load
    load_percent = min(1.0, st.session_state.server_load / st.session_state.server_capacity)
    
    # --- UPDATED STATUS LOGIC ---
    if st.session_state.attack_running:
        st.session_state.server_status = "🔥 UNDER ATTACK"
        st.error(f"Status: {st.session_state.server_status}")
    elif load_percent > 0.9:
        st.session_state.server_status = "🆘 Overloaded"
        st.error(f"Status: {st.session_state.server_status}")
    elif load_percent > 0.5:
        st.session_state.server_status = "⚠️ High Load"
        st.warning(f"Status: {st.session_state.server_status}")
    else:
        st.session_state.server_status = "✅ Stable" if st.session_state.server_load > 0 else "✅ Idle"
        st.success(f"Status: {st.session_state.server_status}")

    st.markdown(f"**Current Load:** `{st.session_state.server_load}` / `{st.session_state.server_capacity}`")
    st.progress(load_percent)

    # Live Chart
    st.subheader("Live Load Monitor")
    new_data = pd.DataFrame({
        'Time': [st.session_state.simulation_time], 
        'Server Load': [st.session_state.server_load], 
        'Capacity': [st.session_state.server_capacity]
    })
    st.session_state.load_history = pd.concat([st.session_state.load_history, new_data], ignore_index=True)
    # Keep history from getting too long
    if len(st.session_state.load_history) > 50:
        st.session_state.load_history = st.session_state.load_history.iloc[-50:]
    
    st.line_chart(st.session_state.load_history.set_index('Time'))

    # Defense Panel
    st.subheader("🛡️ Defense Panel")
    st.session_state.rate_limiting_enabled = st.toggle("Enable Rate Limiting (Firewall)", value=st.session_state.rate_limiting_enabled)
    st.session_state.auto_scaling_enabled = st.toggle("Enable Cloud Auto-Scaling", value=st.session_state.auto_scaling_enabled)
    
    # Only show 'Block' button if not already blocked
    if not st.session_state.attacker_blocked:
        if st.button("🚨 BLOCK ATTACKER IP 🚨"):
            st.session_state.attacker_blocked = True
            add_log("Firewall rule added: Attacker IP BLOCKED.", "defense")
    
    # Only show 'Unblock' button if blocked
    if st.session_state.attacker_blocked:
        if st.button("🟢 UNBLOCK ATTACKER IP 🟢"):
            st.session_state.attacker_blocked = False
            add_log("Firewall rule removed: Attacker IP UNBLOCKED.", "defense")

# --- 3. Authentic User Column ---
with col_user:
    st.header("👤 Authentic User")
    st.markdown("The user is just trying to log in, but the server might be too busy.")
    
    with st.form("login_form"):
        st.text_input("Login ID", value="user@example.com", disabled=True)
        st.text_input("Password", value="••••••••", type="password", disabled=True)
        login_button = st.form_submit_button("Attempt Login")

    if login_button:
        # Check if server has capacity
        if st.session_state.server_load + 1 <= st.session_state.server_capacity:
            st.session_state.server_load += 1
            add_log("Processing valid login request...", "user")
            st.session_state.user_message = "Logging in... server is processing."
            
            # Simulate processing time
            time.sleep(REQUEST_PROCESSING_TIME * 5) # Give login a bit more time
            
            # Check if server *still* has capacity (it might have filled up)
            if st.session_state.server_load > st.session_state.server_capacity:
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

    # Server Logs
    st.subheader("Server Logs")
    log_placeholder = st.empty()
    with log_placeholder.container(height=300):
        for log in st.session_state.server_logs:
            st.markdown(log, unsafe_allow_html=True)


# --- Simulation Loop Control ---

# Simulate the server processing its queue
process_server_load()

# Increment simulation time for the chart
st.session_state.simulation_time += 1

# Add a small delay and rerun to create the "live" effect
time.sleep(0.5)
st.rerun()
