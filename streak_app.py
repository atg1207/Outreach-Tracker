import streamlit as st
import pandas as pd
import datetime
import os
import calendar

# --------------------------------------------------------------------------------
# PAGE CONFIG - WIDE LAYOUT
# --------------------------------------------------------------------------------
st.set_page_config(page_title="Daily Streak Tracker", layout="wide")

DATA_FILE = "streak_data.csv"

# --------------------------------------------------------------------------------
# CSS for Dark Theme, Glowing Progress Bars, and Tick-Mark Calendar
# --------------------------------------------------------------------------------
CSS = """
<style>
/* Main page container for a website-like look */
.main-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0.5rem 1rem;
}

/* Dark background, green accents */
body {
    background-color: #2C2F33;
    color: #EAEAEA;
    font-family: "Segoe UI", "Helvetica Neue", sans-serif;
    font-size: 15px;
    margin: 0;
    padding: 0;
}

/* Headings in bright green */
h1, h2, h3 {
    color: #37BD73;
    margin-top: 0.4rem;
    margin-bottom: 0.4rem;
}

/* Buttons in green */
.stButton>button {
    background-color: #37BD73;
    color: #ffffff;
    border-radius: 5px;
    font-size: 0.9rem;
    padding: 0.4em 1em;
    border: none;
    margin: 0.2em 0;
    transition: background-color 0.3s ease;
}
.stButton>button:hover {
    background-color: #2EA75F;
    cursor: pointer;
}

/* Section containers */
.section {
    background: #3A3F44;
    border-radius: 6px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

/* Glowing progress bars */
.stProgress > div > div {
    background-color: #37BD73 !important;
    box-shadow: 0 0 6px rgba(55, 189, 115, 0.6);
    animation: pulse 1.5s infinite;
    transition: width 0.5s ease !important;
}
@keyframes pulse {
  0% {
    transform: scale(1);
    box-shadow: 0 0 6px #37BD73;
  }
  50% {
    transform: scale(1.03);
    box-shadow: 0 0 14px #37BD73;
  }
  100% {
    transform: scale(1);
    box-shadow: 0 0 6px #37BD73;
  }
}

/* Calendar styling */
.calendar-container {
    background: #3A3F44;
    padding: 0.75rem 1rem;
    border-radius: 6px;
    margin-bottom: 0.75rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
}
.calendar-table {
    width: 100%;
    border-collapse: collapse;
    text-align: center;
}
.calendar-table th {
    padding: 6px;
    font-weight: 600;
    color: #37BD73;
}
.calendar-table td {
    padding: 0.8rem;
    margin: 4px;
    border-radius: 4px;
}
/* Blank slot in calendar */
.empty-day {
    background-color: transparent;
}
/* Normal day (<10 outreaches) */
.empty-cell {
    background-color: #3A3F44;
    color: #EAEAEA;
}
/* Filled day (>=10 outreaches) with tick mark */
.filled-cell {
    position: relative;
    background-color: #37BD73;
    animation: daypulse 2s infinite;
    color: #ffffff;
    font-weight: bold;
}
.filled-cell .day-num {
    font-size: 1.0em;
}
.filled-cell .checkmark {
    margin-left: 0.3em;
    font-size: 1.2em;
    color: #fff;
}
@keyframes daypulse {
  0%   { transform: scale(1);   box-shadow: 0 0 6px #37BD73; }
  50%  { transform: scale(1.05); box-shadow: 0 0 14px #37BD73; }
  100% { transform: scale(1);   box-shadow: 0 0 6px #37BD73; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# --------------------------------------------------------------------------------
# 1. DATA LOADING / SAVING
# --------------------------------------------------------------------------------
def load_data():
    try:
        return pd.read_csv(DATA_FILE)
    except (pd.errors.EmptyDataError, FileNotFoundError):
        return pd.DataFrame(columns=["date", "count"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def init_data():
    """Load data into session_state if not already present, ensure today's row exists."""
    if "data" not in st.session_state:
        st.session_state["data"] = load_data()

    today_str = datetime.date.today().isoformat()
    if today_str not in st.session_state["data"]["date"].values:
        new_row = {"date": today_str, "count": 0}
        st.session_state["data"] = pd.concat(
            [st.session_state["data"], pd.DataFrame([new_row])],
            ignore_index=True
        )

    if "today" not in st.session_state:
        st.session_state["today"] = today_str

    if "count" not in st.session_state:
        df = st.session_state["data"]
        idx = df.index[df["date"] == st.session_state["today"]][0]
        st.session_state["count"] = int(df.at[idx, "count"])

def compute_weekly_count(df):
    """Sum the last 7 days' outreach."""
    return df.tail(7)["count"].sum()

# --------------------------------------------------------------------------------
# 2. BUILD & DISPLAY A MONTHLY CALENDAR WITH A TICK FOR >=10
# --------------------------------------------------------------------------------
def render_monthly_calendar(df):
    """
    Creates an HTML table for the current month.
    If a day has >=10 outreaches, we show a green, pulsing background plus a checkmark (tick).
    """
    # Current month/year
    now = datetime.date.today()
    year, month = now.year, now.month

    # Convert DataFrame to a dict for quick lookups: { 'YYYY-MM-DD': count }
    counts = {}
    for _, row in df.iterrows():
        counts[row['date']] = row['count']

    # Generate the matrix for the current month
    cal = calendar.monthcalendar(year, month)
    day_names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

    # Start building the HTML
    html = """
    <div class="calendar-container">
      <h2>📅 Monthly Calendar</h2>
      <table class="calendar-table">
        <thead>
          <tr>"""
    for dn in day_names:
        html += f"<th>{dn}</th>"
    html += "</tr></thead><tbody>"

    # Fill in weeks
    for week in cal:
        html += "<tr>"
        for day in week:
            if day == 0:
                # No date in this slot
                html += "<td class='empty-day'></td>"
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                day_count = counts.get(date_str, 0)

                if day_count >= 10:
                    # Day with tick
                    html += (
                        f"<td class='filled-cell'>"
                        f"<span class='day-num'>{day}</span>"
                        f"<span class='checkmark'>✓</span>"
                        f"</td>"
                    )
                else:
                    # Normal day
                    html += f"<td class='empty-cell'>{day}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    html += "<p style='margin-top: 0.75rem;'>Hit 10+ outreaches to light up that day with a checkmark!</p>"
    html += "</div>"
    return html

# --------------------------------------------------------------------------------
# 3. CALLBACKS FOR + / - OUTREACH
# --------------------------------------------------------------------------------
def add_outreach(row_idx: int):
    df = st.session_state["data"]
    df.at[row_idx, "count"] += 1

    # If today's row, update session state
    if df.at[row_idx, "date"] == st.session_state["today"]:
        st.session_state["count"] = df.at[row_idx, "count"]
        if st.session_state["count"] == 10:
            st.balloons()
    save_data(df)

def remove_outreach(row_idx: int):
    df = st.session_state["data"]
    if df.at[row_idx, "count"] > 0:
        df.at[row_idx, "count"] -= 1
        if df.at[row_idx, "date"] == st.session_state["today"]:
            st.session_state["count"] = df.at[row_idx, "count"]
        save_data(df)
    else:
        st.warning("Count is already 0. Can't remove more.")

# --------------------------------------------------------------------------------
# 4. MAIN APP
# --------------------------------------------------------------------------------
def main():
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.title("🚀 Daily Streak Tracker 🚀")

    init_data()
    df = st.session_state["data"]

    # Row: Today’s progress (left) | Weekly progress (right)
    col1, col2 = st.columns(2, gap="large")

    # --- A. TODAY'S PROGRESS ---
    with col1:
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.subheader("✨ Today’s Progress")
        today_count = st.session_state["count"]
        today_str = st.session_state["today"]

        st.write(f"**Date**: {today_str}")
        st.write(f"**Daily Outreach**: {today_count}/10")

        # Motivational message
        if today_count == 0:
            st.info("You haven't started yet today. Let's go!")
        elif 1 <= today_count < 5:
            st.info("Good start, keep going!")
        elif 5 <= today_count < 10:
            st.info("More than halfway there—stay on it!")
        else:
            st.success("You've reached or passed the daily goal—awesome job!")

        daily_progress = min(today_count, 10) / 10
        st.progress(daily_progress)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- B. WEEKLY PROGRESS ---
    with col2:
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.subheader("📅 Weekly Progress")
        weekly_count = compute_weekly_count(df)

        st.write(f"**Weekly Outreach**: {weekly_count}/100")

        if weekly_count < 50:
            st.info("Keep stacking those outreaches for the week!")
        elif 50 <= weekly_count < 100:
            st.info("You've crossed halfway—keep pushing to 100!")
        else:
            st.success("You smashed the weekly goal of 100!")

        weekly_progress = min(weekly_count, 100) / 100
        st.progress(weekly_progress)

        if 75 <= weekly_count < 100:
            st.snow()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- C. ALL DAYS (+ / -) ---
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("🗓️ All Days Overview")
    st.write("Use the **-** and **+** buttons to remove or add outreaches for each day.")

    for i, row in df.iterrows():
        date_str = row["date"]
        count_val = row["count"]
        cols = st.columns([1.6, 1, 1, 1])
        with cols[0]:
            st.write(f"**{date_str}**")
        with cols[1]:
            st.button("−", key=f"minus_{i}", on_click=remove_outreach, args=(i,))
        with cols[2]:
            st.write(f"**{count_val}**")
        with cols[3]:
            st.button("+", key=f"plus_{i}", on_click=add_outreach, args=(i,))
    st.markdown('</div>', unsafe_allow_html=True)

    # --- D. PAST 7 DAYS & STREAK ---
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("⏳ Past 7 Days Activity")

    last_7_days = df.tail(7)
    st.table(last_7_days)

    # Calculate consecutive streak of >=10
    consecutive_streak = 0
    for _, day_row in df.iloc[::-1].iterrows():
        if day_row["count"] >= 10:
            consecutive_streak += 1
        else:
            break
    st.write(f"**Current Streak:** {consecutive_streak} days")

    if consecutive_streak > 0 and st.session_state["count"] >= 10:
        st.success("Keep the streak alive! Great job!")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- E. MONTHLY CALENDAR WITH CHECKMARK ---
    cal_html = render_monthly_calendar(df)
    st.markdown(cal_html, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # end main-container

if __name__ == "__main__":
    main()
