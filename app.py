import re
import whisper
import tempfile
import streamlit as st
import pickle
import plotly.graph_objects as go
import pandas as pd
import json
import os

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="Spam Email Classifier",
    page_icon="📧",
    layout="centered"
)

# =========================
# DARK / LIGHT MODE
# =========================

theme = st.sidebar.selectbox(
    "Choose Theme",
    ["Dark", "Light"]
)

if theme == "Dark":

    bg_color = "#0E1117"
    text_color = "white"

else:

    bg_color = "white"
    text_color = "black"

# =========================
# CUSTOM CSS
# =========================

st.markdown(f"""
<style>

.main {{
    background-color: {bg_color};
    color: {text_color};
}}

.title {{
    text-align: center;
    font-size: 45px;
    font-weight: bold;
    color: #00FFAA;
}}

.result-spam {{
    background-color: #ff4b4b;
    padding: 20px;
    border-radius: 10px;
    color: white;
    text-align: center;
    font-size: 20px;
}}

.result-safe {{
    background-color: #00c853;
    padding: 20px;
    border-radius: 10px;
    color: white;
    text-align: center;
    font-size: 20px;
}}

.stButton button {{
    width: 100%;
    height: 50px;
    border-radius: 10px;
    background-color: #00FFAA;
    color: black;
    font-size: 18px;
}}

</style>
""", unsafe_allow_html=True)

# =========================
# LOAD MODEL
# =========================

model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))
whisper_model = whisper.load_model(
    "base"
)


# =========================
# USER DATABASE
# =========================

USER_FILE = "users.json"

if not os.path.exists(USER_FILE):

    with open(USER_FILE, "w") as f:

        json.dump({}, f)

with open(USER_FILE, "r") as f:

    users = json.load(f)

# =========================
# SESSION STATES
# =========================

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False

if "history" not in st.session_state:

    st.session_state.history = []

if "spam_count" not in st.session_state:

    st.session_state.spam_count = 0

if "safe_count" not in st.session_state:

    st.session_state.safe_count = 0

# =========================
# LOGIN / SIGNUP
# =========================

st.sidebar.title("Account")

menu = st.sidebar.selectbox(
    "Menu",
    ["Login", "Signup"]
)

# =========================
# SIGNUP
# =========================

if menu == "Signup":

    st.sidebar.subheader("Create Account")

    new_username = st.sidebar.text_input(
        "Username"
    )

    new_password = st.sidebar.text_input(
        "Password",
        type="password"
    )

    if st.sidebar.button("Signup"):

        if new_username in users:

            st.sidebar.error(
                "Username already exists"
            )

        else:

            users[new_username] = {

                "password": new_password,

                "history": [],

                "spam_count": 0,

                "safe_count": 0
            }

            with open(USER_FILE, "w") as f:

                json.dump(users, f)

            st.sidebar.success(
                "Signup successful"
            )

# =========================
# LOGIN
# =========================

if menu == "Login":

    st.sidebar.subheader("Login")

    username = st.sidebar.text_input(
        "Username"
    )

    password = st.sidebar.text_input(
        "Password",
        type="password"
    )

    if st.sidebar.button("Login"):

        if (
            username in users
            and
            users[username]["password"] == password
        ):

            st.session_state.logged_in = True

            st.session_state.username = username

            st.session_state.history = (
                users[username]["history"]
            )

            st.session_state.spam_count = (
                users[username]["spam_count"]
            )

            st.session_state.safe_count = (
                users[username]["safe_count"]
            )

            st.sidebar.success(
                f"Welcome {username}"
            )

        else:

            st.sidebar.error(
                "Invalid credentials"
            )

# =========================
# LOGOUT
# =========================

if st.sidebar.button("Logout"):

    st.session_state.logged_in = False

    st.sidebar.success("Logged out")

# =========================
# USER STATUS
# =========================

if st.session_state.logged_in:

    st.success(
        f"Logged in as {st.session_state.username}"
    )

else:

    st.info(
        "Using as Guest User"
    )

# =========================
# DASHBOARD
# =========================

total_predictions = (
    st.session_state.spam_count
    + st.session_state.safe_count
)

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Total",
        total_predictions
    )

with col2:

    st.metric(
        "Spam",
        st.session_state.spam_count
    )

with col3:

    st.metric(
        "Safe",
        st.session_state.safe_count
    )

# =========================
# TITLE
# =========================

st.markdown(
    '<p class="title">📧 Spam Email Classifier</p>',
    unsafe_allow_html=True
)
# =========================
# INPUT
# =========================

# Text input
input_sms = st.text_area(
    "Enter Message"
)

# ============================
# PREDICTION
# ============================

if st.button("Predict Message"):

    # Transform input text
    transformed_sms = vectorizer.transform([input_sms])

    # Predict message
    prediction = model.predict(transformed_sms)[0]

    # Prediction probability
    probability = model.predict_proba(transformed_sms)[0]

    safe_prob = probability[0] * 100
    spam_prob = probability[1] * 100

    # Result text
    result = "Spam" if prediction == 1 else "Safe"

    # ============================
    # Counters
    # ============================

    if prediction == 1:
        st.session_state.spam_count += 1
    else:
        st.session_state.safe_count += 1

    # ============================
    # Spam Keywords
    # ============================

    spam_keywords = [
        "free",
        "winner",
        "cash",
        "offer",
        "money",
        "urgent",
        "click",
        "password"
    ]

    # ============================
    # Phishing Keywords
    # ============================

    phishing_keywords = [
        "password",
        "otp",
        "bank",
        "credit card",
        "verify account",
        "login",
        "security alert",
        "click link",
        "urgent",
        "bitcoin",
        "wallet",
        "gift card",
        "claim reward",
        "free money"
    ]

    detected_words = []
    phishing_detected = []

    # ============================
    # Detect Spam Words
    # ============================

    for word in spam_keywords:

        if word in input_sms.lower():

            detected_words.append(word)

    # ============================
    # Detect Phishing Words
    # ============================

    for word in phishing_keywords:

        if word in input_sms.lower():

            phishing_detected.append(word)

            # URL Detection
urls = re.findall(
    r'(https?://\S+|www\.\S+)',
    input_sms
)

if len(urls) > 0:

    st.warning(
        "🔗 URL Detected in Message"
    )

    st.write(urls)
    # Suspicious short links
shorteners = [

    "bit.ly",
    "tinyurl",
    "goo.gl",
    "t.co",
    "rb.gy"
]

for short in shorteners:

    if short in input_sms.lower():

        st.error(
            f"🚨 Suspicious Short URL Detected: {short}"
        )
    # Fake login detection
fake_words = [

    "login",
    "verify",
    "account",
    "password",
    "bank"
]

fake_count = 0

for word in fake_words:

    if word in input_sms.lower():

        fake_count += 1

if fake_count >= 3:

    st.error(
        "🚨 Possible Fake Login / Phishing Page"
    )
    

    # ============================
    # Phishing Warning
    # ============================

    if len(phishing_detected) > 0:

        st.warning(
            "⚠ Possible Phishing Attempt Detected"
        )

        st.write("Detected phishing words:")

        st.write(phishing_detected)

    # ============================
    # Suspicious Domains
    # ============================

    suspicious_domains = [
        ".xyz",
        ".ru",
        ".tk",
        ".top",
        ".click"
    ]

    for domain in suspicious_domains:

        if domain in input_sms.lower():

            st.error(
                f"🚨 Suspicious domain detected: {domain}"
            )

    # ============================
    # Final Result
    # ============================

    if prediction == 1:

        st.markdown(
            f"""
            <div class="result-spam">

                🔥 Spam Message

                <br><br>

                Spam Probability: {spam_prob:.2f}%

            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            f"""
            <div class="result-safe">

                ✅ Safe Message

                <br><br>

                Safe Probability: {safe_prob:.2f}%

            </div>
            """,
            unsafe_allow_html=True
        )

    # ============================
    # Detected Spam Words
    # ============================

    if len(detected_words) > 0:

        st.write("Detected spam words:")

        st.write(detected_words)
        
    # Bar Chart
    fig = go.Figure(
        data=[
            go.Bar(
                x=["Safe", "Spam"],
                y=[safe_prob, spam_prob]
            )
        ]
    )

    st.plotly_chart(fig)

    # Pie Chart
    pie_fig = go.Figure(
        data=[
            go.Pie(
                labels=["Safe", "Spam"],
                values=[safe_prob, spam_prob],
                hole=0.4
            )
        ]
    )

    st.plotly_chart(pie_fig)

    # Download Report
    report = (
        "Spam Email Report\n"
        "==================\n\n"
        f"Message:\n{input_sms}\n\n"
        f"Prediction:\n{result}\n"
    )

    st.download_button(
        label="📥 Download Report",
        data=report,
        file_name="spam_report.txt",
        mime="text/plain"
    )

    # Save History
    st.session_state.history.append({

        "message": input_sms,

        "result": result
    })

    # Save User Data
    if st.session_state.logged_in:

        username = st.session_state.username

        users[username]["history"] = (
            st.session_state.history
        )

        users[username]["spam_count"] = (
            st.session_state.spam_count
        )

        users[username]["safe_count"] = (
            st.session_state.safe_count
        )

        with open(USER_FILE, "w") as f:

            json.dump(users, f)
            
# Voice Upload
st.subheader("🎤 Upload Voice Message")

audio_file = st.file_uploader(
    "Upload Audio File",
    type=["mp3", "wav", "m4a"],
    key="audio_uploader"
)

if audio_file is not None:

    st.audio(audio_file)

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".wav"
    ) as temp_audio:

        temp_audio.write(
            audio_file.read()
        )

        temp_audio_path = temp_audio.name

    result = whisper_model.transcribe(
        temp_audio_path
    )

    input_sms = result["text"]

    st.success(
        "Voice converted to text"
    )

    st.text_area(
        "Converted Text",
        input_sms,
        height=150
    )

# File uploader
uploaded_file = st.file_uploader(
    "Upload File",
    type=["txt", "csv", "xlsx"],
    key="text_uploader"
)

# Read uploaded file
if uploaded_file is not None:

    # TXT FILE
    if uploaded_file is not None and uploaded_file.name.endswith(".txt"):

        input_sms = uploaded_file.read().decode(
            "utf-8"
        )

        st.text_area(
            "File Content",
            input_sms,
            height=200
        )

    # CSV FILE
    elif uploaded_file is not None and uploaded_file.name.endswith(".csv"):

        df = pd.read_csv(uploaded_file)

        st.write("CSV Preview")

        st.dataframe(df)

        input_sms = " ".join(
            df.astype(str).values.flatten()
        )

    # EXCEL FILE
    # EXCEL FILE
elif uploaded_file is not None and uploaded_file.name.endswith(".xlsx"):

    df = pd.read_excel(uploaded_file)

    st.write("Excel Preview")

    st.dataframe(df)

    # Check message column
    if "message" in df.columns:

        predictions = []

        probabilities = []

        # Predict every row
        for msg in df["message"]:

            transformed = vectorizer.transform(
                [str(msg)]
            )

            pred = model.predict(
                transformed
            )[0]

            prob = model.predict_proba(
                transformed
            )[0]

            predictions.append(
                "Spam" if pred == 1 else "Safe"
            )

            probabilities.append(
                round(max(prob) * 100, 2)
            )

        # Add results to dataframe
        df["Prediction"] = predictions

        df["Confidence"] = probabilities

        st.subheader(
            "Prediction Results"
        )

        st.dataframe(df)

        # Download CSV
        csv = df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "📥 Download Results CSV",
            csv,
            "prediction_results.csv",
            "text/csv"
        )

    else:

        st.error(
            "Excel file must contain 'message' column"
        )

# =========================
# DOWNLOAD CSV
# =========================

if st.session_state.history:

    history_df = pd.DataFrame(
        st.session_state.history
    )

    csv = history_df.to_csv(
        index=False
    )

    st.download_button(
        label="📊 Download CSV",
        data=csv,
        file_name="history.csv",
        mime="text/csv"
    )

# =========================
# CLEAR HISTORY
# =========================

if st.button("🧹 Clear History"):

    st.session_state.history = []

    st.session_state.spam_count = 0

    st.session_state.safe_count = 0

    if st.session_state.logged_in:

        username = st.session_state.username

        users[username]["history"] = []

        users[username]["spam_count"] = 0

        users[username]["safe_count"] = 0

        with open(USER_FILE, "w") as f:

            json.dump(users, f)

    st.success(
        "History Cleared"
    )

# =========================
# HISTORY
# =========================

st.subheader("Prediction History")

for item in st.session_state.history[::-1]:

    st.write(
        f"Message: {item['message']}"
    )

    st.write(
        f"Result: {item['result']}"
    )

    st.write("---")