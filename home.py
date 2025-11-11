import streamlit as st
import tensorflow as tf
import numpy as np
import cv2
import tempfile
import os
import json
from datetime import datetime
import plotly.express as px
import pandas as pd

STATS_FILE = "stats.json"
HISTORY_FILE = "prediction_history.json"

# Load stats
def load_stats():
    if not os.path.exists(STATS_FILE):
        return {"real": 0, "deepfake": 0, "total": 0}
    with open(STATS_FILE, "r") as f:
        return json.load(f)

# Update stats
def update_stats(prediction_is_fake):
    stats = load_stats()
    stats["total"] += 1
    stats["deepfake"] += int(prediction_is_fake)
    stats["real"] += int(not prediction_is_fake)
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f)

# Save prediction history
def save_prediction_history(result):
    data = {"timestamp": datetime.now().isoformat(), "result": result}
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    history.append(data)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

# Load prediction history
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)

# Extract frames
def extract_frames(video_path, frame_count=10):
    cap = cv2.VideoCapture(video_path)
    frames = []
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, total_frames // frame_count)

    for i in range(0, total_frames, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if ret:
            frame = cv2.resize(frame, (224, 224))
            frame = frame / 255.0
            frames.append(frame)
        if len(frames) >= frame_count:
            break
    cap.release()
    return np.array(frames)

# Display overall stats
def display_stats():
    stats = load_stats()
    real = stats["real"]
    fake = stats["deepfake"]
    total = stats["total"]

    col1, col2, col3 = st.columns(3)
    col1.metric("🧾 Total Videos", total)
    col2.metric("✅ Real", real)
    col3.metric("❌ Deepfake", fake)

    if total == 0:
        st.info("No predictions yet.")
        return

    labels = ['Real', 'Deepfake']
    values = [real, fake]

    fig = px.pie(
        names=labels,
        values=values,
        color=labels,
        color_discrete_map={'Real': '#1abc9c', 'Deepfake': '#e74c3c'},
        title='Prediction Distribution (Overall)',
        hole=0.4
    )
    fig.update_traces(textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

# Animated chart over time
def display_interactive_pie_chart():
    history = load_history()
    if not history:
        st.info("No prediction history yet.")
        return

    df = pd.DataFrame(history)
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df = df.dropna(subset=['timestamp'])  # remove invalid timestamps

    if df.empty:
        st.info("No valid prediction timestamps found.")
        return

    df['date'] = df['timestamp'].dt.date
    df['result'] = df['result'].apply(lambda x: 'Deepfake' if x else 'Real')

    unique_dates = sorted(df['date'].unique())

    if len(unique_dates) == 0:
        st.info("Not enough data for time-series visualization.")
        return
    elif len(unique_dates) == 1:
        selected_date = unique_dates[0]
        st.write(f"Only one prediction date available: **{selected_date}**")
    else:
        selected_date = st.select_slider(
            "📆 Select Date for Prediction Analysis",
            options=unique_dates,
            value=unique_dates[-1]
        )

    filtered_df = df[df['date'] == selected_date]
    counts = filtered_df['result'].value_counts().reset_index()
    counts.columns = ['result', 'count']

    fig = px.pie(
        counts,
        names='result',
        values='count',
        color='result',
        color_discrete_map={'Real': '#1abc9c', 'Deepfake': '#e74c3c'},
        title=f'Prediction Distribution on {selected_date}',
        hole=0.4
    )
    fig.update_traces(textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)
# Main app
def main():
    st.set_page_config(page_title="Video Deepfake Detector", page_icon="🎥")

    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        st.warning("Please log in first.")
        st.stop()

    # Header
    col1, col2 = st.columns([20, 5])
    with col1:
        st.title("🔐 Video Deepfake Detector")
    with col2:
        if st.button("Logout ❌"):
            st.session_state.clear()
            st.rerun()

    st.write(f"Hello, **{st.session_state['username']}**! Upload a video to detect deepfakes.")
    model = tf.keras.models.load_model("deepfake_detection_model_updated4.h5")

    uploaded_file = st.file_uploader("📤 Upload a video", type=["mp4", "avi", "mov"])

    if uploaded_file:
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.read())

        st.video(temp_path)

        if st.button("🚀 Detect"):
            with st.spinner("Processing..."):
                frames = extract_frames(temp_path)

                if frames.shape[0] < 10:
                    st.error("Not enough frames for prediction.")
                    return

                frames = np.expand_dims(frames, axis=0)
                prediction = model.predict(frames)[0]

                is_fake = prediction[0] > 0.5
                result = "🚨 Deepfake ❌" if is_fake else "✅ Real Video"
                confidence = float(prediction[0]) * 100
                st.success(f"Prediction: {result} (Confidence: {confidence:.2f}%)")

                update_stats(is_fake)
                save_prediction_history(bool(is_fake))
                st.toast("📊 Stats Updated!")

    st.markdown("## 📊 Overall Statistics")
    display_stats()

    st.markdown("## 📈 Animated Prediction Distribution Over Time")
    display_interactive_pie_chart()

    # CSS Styling
    st.markdown("""
        <style>
        .stApp {
            background-image: url('https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1650&q=80');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }

        .stApp::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            height: 100%;
            width: 100%;
            background-color: rgba(0, 0, 0, 0.8);
            z-index: 0;
        }

        .main > div {
            background: rgba(0, 0, 0, 0.55);
            backdrop-filter: blur(14px);
            border-radius: 20px;
            padding: 3rem 2rem;
            margin: 3rem auto;
            max-width: 1000px;
            box-shadow: 0 0 25px rgba(255, 255, 255, 0.08);
        }

        h1, h2, h3, h4, h5 {
            color: #f0f0f0 !important;
            text-align: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        .stTextInput>div>div>input, .stPasswordInput>div>div>input {
            background-color: rgba(255,255,255,0.1);
            border: 1px solid #ccc;
            border-radius: 12px;
            color: white;
            padding: 10px;
        }

        .stButton>button {
            background: linear-gradient(135deg, #3f5efb, #fc466b);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 10px 20px;
            font-size: 16px;
            margin-top: 10px;
        }

        .stButton>button:hover {
            background: linear-gradient(135deg, #fc466b, #3f5efb);
            color: white;
            transform: scale(1.02);
        }

        .stCheckbox>div {
            color: white;
        }

        .stMetricLabel, .stMetricValue {
            color: white !important;
        }

        .css-1v0mbdj {
            color: white;
        }

        .css-1aumxhk {
            background-color: rgba(255,255,255,0.05);
            border-radius: 10px;
        }

        footer {
            visibility: hidden;
        }
        </style>
    """, unsafe_allow_html=True)

# Run the app
if __name__ == "__main__":
    main()
