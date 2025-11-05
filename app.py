import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# ------------------------------
# File Setup
# ------------------------------
DATA_DIR = "./mood_data"
DATA_FILE = os.path.join(DATA_DIR, "mood_log.csv")
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

os.makedirs(DATA_DIR, exist_ok=True)

# ------------------------------
# Utility Functions
# ------------------------------
def load_data():
    """Load existing mood entries from CSV."""
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, parse_dates=["timestamp"])
            return df
        except Exception:
            return pd.DataFrame(columns=["timestamp", "mood", "tags", "notes"])
    else:
        return pd.DataFrame(columns=["timestamp", "mood", "tags", "notes"])


def save_data(df: pd.DataFrame):
    """Save mood entries to CSV."""
    df.to_csv(DATA_FILE, index=False)


def add_entry(mood: int, tags: str, notes: str):
    """Add a new mood entry."""
    df = load_data()
    now = datetime.now().strftime(DATE_FORMAT)
    new = {"timestamp": now, "mood": mood, "tags": tags, "notes": notes}
    df = pd.concat([pd.DataFrame([new]), df], ignore_index=True)
    save_data(df)
    return df


def delete_entry(index: int):
    """Delete a mood entry by index."""
    df = load_data()
    if 0 <= index < len(df):
        df = df.drop(df.index[index]).reset_index(drop=True)
        save_data(df)
    return df


# ------------------------------
# Streamlit UI
# ------------------------------
st.set_page_config(page_title="Mood Tracker", page_icon="😊", layout="centered")
st.title("🧠 Mood Tracker")
st.write("Track your mood, add notes, and visualize emotional trends over time!")

# Sidebar - Add entry form
st.sidebar.header("Add a Mood Entry")
with st.sidebar.form(key='mood_form'):
    mood = st.slider("How are you feeling today? (1 = Low, 10 = High)", 1, 10, 7)
    tags = st.text_input("Tags (comma-separated)", placeholder="e.g. work, study, family")
    notes = st.text_area("Notes (optional)")
    submit = st.form_submit_button("Add Entry")

if submit:
    add_entry(mood, tags, notes)
    st.sidebar.success("✅ Entry added successfully!")

# Load Data
df = load_data()

# If no data
if df.empty:
    st.info("No entries yet. Use the sidebar to add your first mood record!")
else:
    df['timestamp'] = pd.to_datetime(df['timestamp'], format=DATE_FORMAT)

    # Filter Section
    st.subheader("Your Mood Entries")
    col1, col2 = st.columns([2, 1])
    with col1:
        min_date = df['timestamp'].min().date()
        max_date = df['timestamp'].max().date()
        date_range = st.date_input("Filter by Date Range", (min_date, max_date))
    with col2:
        tag_filter = st.text_input("Filter by Tag", placeholder="Type a tag...")

    filtered = df.copy()
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        filtered = filtered[(filtered['timestamp'].dt.date >= start.date()) & (filtered['timestamp'].dt.date <= end.date())]
    if tag_filter:
        filtered = filtered[filtered['tags'].str.contains(tag_filter, case=False, na=False)]

    # Display entries
    st.write(f"Showing {len(filtered)} entries")
    st.download_button("📥 Download Filtered CSV", data=filtered.to_csv(index=False), file_name="mood_filtered.csv", mime="text/csv")

    st.markdown("---")
    for i, row in filtered.reset_index().iterrows():
        idx = int(row['index'])
        with st.expander(f"{row['timestamp'].strftime('%Y-%m-%d %H:%M')} — Mood: {row['mood']}"):
            st.write(f"**Tags:** {row['tags']}")
            st.write(f"**Notes:** {row['notes']}")
            if st.button(f"🗑️ Delete Entry (index {idx})", key=f"del_{idx}"):
                delete_entry(idx)
                st.experimental_rerun()

    # ------------------------------
    # Charts & Visualizations
    # ------------------------------
    st.markdown("---")
    st.subheader("📈 Mood Trend Over Time")
    fig, ax = plt.subplots()
    df_sorted = df.sort_values('timestamp')
    ax.plot(df_sorted['timestamp'], df_sorted['mood'], marker='o', color='blue')
    ax.set_xlabel("Date")
    ax.set_ylabel("Mood (1–10)")
    ax.set_title("Mood Trend")
    ax.grid(True)
    st.pyplot(fig)

    st.subheader("📅 Daily Average Mood")
    daily = df.copy()
    daily['date'] = daily['timestamp'].dt.date
    daily_avg = daily.groupby('date')['mood'].mean().reset_index()
    st.line_chart(daily_avg.set_index('date'))

    st.subheader("🏷️ Most Common Tags")
    tags_all = df['tags'].dropna().astype(str).str.split(',')
    tags_flat = [t.strip().lower() for sublist in tags_all for t in sublist if t.strip()]
    if tags_flat:
        tag_counts = pd.Series(tags_flat).value_counts().head(15)
        st.bar_chart(tag_counts)
    else:
        st.write("No tags available yet.")

# ------------------------------
# Footer
# ------------------------------
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    if not df.empty:
        st.download_button("💾 Export All Data", data=df.to_csv(index=False), file_name="mood_data.csv", mime="text/csv")
with col2:
    if st.button("⚠️ Clear All Data"):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
            st.success("All mood data cleared!")
            st.experimental_rerun()

st.sidebar.markdown("---")
st.sidebar.write("💡 *Tip:* Use short tags like `work`, `study`, or `health` to filter easily.")
