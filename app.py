"""Streamlit entry point for the IT Helpdesk application."""
import logging
import math
import time
from html import escape
import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload
from config import APP_ENV
from database.connection import SessionLocal, init_db
from database.models import Category, Notification, Ticket, User
from database.seed import seed
from services.auth_service import authenticate, register_user
from services.comment_service import add_comment, ticket_activity
from services.category_service import list_categories, save_category, set_category_active
from services.ticket_service import assign_ticket, count_tickets, create_ticket, list_tickets, update_status
from services.report_service import report_tickets
from utils.constants import TRANSITIONS
from services.user_service import create_agent, list_users, set_user_active
from utils.constants import PRIORITIES, Role, TicketStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
st.set_page_config(page_title="IT Helpdesk", page_icon="🎫", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root { --ink:#17263d; --muted:#718198; --line:#e5ebf3; --paper:#ffffff; --canvas:#f5f7fb; --blue:#315eea; --blue-soft:#edf2ff; --teal:#0f9b8e; --shadow:0 12px 36px rgba(29,49,82,.07); }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; color:var(--ink); }
.stApp { background:var(--canvas); }
.block-container { padding:2.1rem 2.4rem 3rem; max-width:1480px; }
h1,h2,h3 { font-family:'Manrope',sans-serif; color:var(--ink)!important; letter-spacing:-.035em; }
h1 { font-size:2.05rem!important; font-weight:750!important; margin-bottom:.25rem!important; }
h2 { font-size:1.35rem!important; font-weight:700!important; }
h3 { font-size:1.05rem!important; font-weight:700!important; }
p, label, [data-testid="stCaptionContainer"] { color:var(--muted); }
.eyebrow { color:#617696; text-transform:uppercase; letter-spacing:.14em; font-size:.72rem; font-weight:700; margin:0 0 .45rem; }
.page-intro { color:var(--muted); margin:.1rem 0 1.25rem; font-size:.98rem; }
[data-testid="stSidebar"] { background:#101d33; border-right:1px solid #1e2e48; }
[data-testid="stSidebar"] * { color:#d6dfed; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#a8b8cf; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { padding:.38rem .55rem; border-radius:9px; font-weight:550; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background:#1c2c46; color:#fff; }
[data-testid="stSidebar"] [data-testid="stRadio"] [aria-checked="true"] + div { color:#fff; }
[data-testid="stSidebar"] button { background:#1c2c46; border:1px solid #31445f; color:#fff; }
.brand-lockup { display:flex; align-items:center; gap:.72rem; padding:.25rem .2rem 1.3rem; }
.brand-mark { width:2.45rem; height:2.45rem; border-radius:12px; display:grid; place-items:center; color:#fff; font-size:1.2rem; background:linear-gradient(145deg,#5683ff,#315eea); box-shadow:0 6px 18px #315eea55; }
.brand-name { color:#fff; font-family:'Manrope',sans-serif; font-weight:750; font-size:1rem; line-height:1.1; }
.brand-sub { color:#94a6c1; font-size:.68rem; letter-spacing:.1em; text-transform:uppercase; margin-top:.25rem; }
.profile-card { display:flex; align-items:center; gap:.7rem; padding:.85rem; margin:.25rem 0 1.25rem; background:#192941; border:1px solid #293c57; border-radius:13px; }
.profile-avatar { width:2.1rem; height:2.1rem; flex:0 0 2.1rem; display:grid; place-items:center; border-radius:10px; background:#294777; color:#dce8ff; font-size:.76rem; font-weight:750; }
.profile-name { color:#fff; font-weight:650; font-size:.9rem; }
.profile-role { color:#9eb0ca; font-size:.76rem; margin-top:.18rem; }
[data-testid="stMetric"] { background:var(--paper); border:1px solid var(--line); padding:1.05rem 1.2rem; border-radius:14px; box-shadow:0 3px 12px rgba(28,48,78,.025); min-height:112px; }
[data-testid="stMetricLabel"] { color:var(--muted)!important; font-size:.79rem!important; font-weight:600!important; }
[data-testid="stMetricValue"] { color:var(--ink)!important; font-family:'Manrope',sans-serif; font-size:1.8rem!important; font-weight:750!important; }
[data-testid="stMetricDelta"] { font-size:.75rem!important; }
[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:12px; overflow:hidden; background:#fff; }
[data-testid="stDataFrame"] [role="columnheader"] { background:#f7f9fc!important; color:#65758d!important; font-size:.74rem!important; font-weight:700!important; text-transform:uppercase; letter-spacing:.04em; }
[data-testid="stForm"] { background:#fff; padding:1.2rem 1.35rem; border:1px solid var(--line); border-radius:15px; box-shadow:var(--shadow); }
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, [data-testid="stSelectbox"] > div > div { border-radius:9px; background:#fff!important; color:var(--ink)!important; border-color:#d7e0eb!important; }
[data-testid="stTextInput"] [data-baseweb="input"] { background:#fff!important; border-color:#d7e0eb!important; }
[data-testid="stTextInput"] button { background:#fff!important; color:#64748b!important; border:0!important; }
[data-testid="stTextInput"] input::placeholder, [data-testid="stTextArea"] textarea::placeholder { color:#8997aa!important; }
div.stButton > button, div.stFormSubmitButton > button { border-radius:9px; font-weight:650; transition:all .15s ease; }
div[data-testid="stButton"] button[kind="primary"], div[data-testid="stFormSubmitButton"] button[kind="primary"] { background:#315eea!important; color:#fff!important; border-color:#315eea!important; box-shadow:0 4px 12px #315eea2c; }
div[data-testid="stButton"] button[kind="primary"] *, div[data-testid="stFormSubmitButton"] button[kind="primary"] * { color:#fff!important; }
[data-testid="stTabs"] [role="tab"] { font-weight:650; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { color:#315eea!important; }
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background:#315eea!important; }
[data-testid="stExpander"] { border:1px solid var(--line); border-radius:12px; background:#fff; }
[data-testid="stPlotlyChart"] { padding:.55rem .65rem; border:1px solid var(--line); border-radius:14px; background:#fff; box-shadow:0 3px 12px rgba(28,48,78,.025); }
.login-hero { min-height:590px; height:100%; padding:2.5rem; border-radius:24px; color:#fff; background:radial-gradient(circle at 85% 6%,#547bf0 0,transparent 27%),linear-gradient(145deg,#172944 0%,#203e68 55%,#315eea 130%); box-shadow:0 22px 60px rgba(28,50,84,.18); display:flex; flex-direction:column; justify-content:space-between; }
.login-hero * { color:#fff; }
.hero-kicker { color:#b6caff; text-transform:uppercase; letter-spacing:.16em; font-size:.72rem; font-weight:700; }
.hero-title { max-width:520px; margin:3.1rem 0 .9rem; font:750 2.65rem/1.12 'Manrope',sans-serif; letter-spacing:-.05em; }
.hero-copy { max-width:450px; color:#d0dbee; font-size:1.02rem; line-height:1.65; }
.hero-points { margin-top:2rem; display:grid; gap:.75rem; }
.hero-point { display:flex; align-items:center; gap:.7rem; color:#e8eef8; font-size:.91rem; }
.hero-check { width:1.45rem; height:1.45rem; border-radius:50%; display:grid; place-items:center; background:#ffffff1d; color:#b9f4e8; font-size:.8rem; }
.hero-foot { padding-top:1.5rem; border-top:1px solid #ffffff27; color:#c1cfe2; font-size:.78rem; }
.login-panel h2 { margin-bottom:.25rem!important; }
.badge { display:inline-block; padding:.3rem .62rem; border-radius:999px; font-size:.76rem; line-height:1.25; font-weight:700; white-space:nowrap; border:1px solid transparent; }
.badge-open { color:#2457bd; background:#edf4ff; border-color:#dce9ff; }
.badge-progress { color:#a85b07; background:#fff4e5; border-color:#ffe6c5; }
.badge-waiting { color:#7240aa; background:#f5edff; border-color:#e9dcff; }
.badge-resolved { color:#14744a; background:#e9f8f0; border-color:#d0f0df; }
.badge-closed { color:#5c6879; background:#f0f2f5; border-color:#e4e7eb; }
.badge-critical { color:#b4232b; background:#fff0f0; border-color:#ffd8d8; }
.badge-high { color:#bb5a15; background:#fff4e9; border-color:#ffdfc3; }
.badge-medium { color:#315daf; background:#eff4ff; border-color:#dae6ff; }
.badge-low { color:#526173; background:#f2f5f8; border-color:#e3e9ef; }
.ticket-heading { display:flex; align-items:center; flex-wrap:wrap; gap:.65rem; margin:.5rem 0 .85rem; }
.ticket-number { color:#62738a; font:700 .8rem 'DM Sans',sans-serif; letter-spacing:.04em; }
.ticket-description { color:#33445d; white-space:pre-wrap; line-height:1.65; }
.detail-meta { display:flex; flex-wrap:wrap; gap:.55rem; margin-top:.85rem; }
.meta-chip { padding:.36rem .65rem; background:#f4f7fb; border:1px solid #e8edf4; border-radius:8px; color:#586b84; font-size:.77rem; }
.activity-row { padding:.7rem 0; border-bottom:1px solid #edf0f5; color:#52637a; font-size:.87rem; }
.activity-row:last-child { border-bottom:0; }
.empty-state { text-align:center; padding:2.4rem 1rem; border:1px dashed #d5deea; border-radius:14px; background:#fff; color:#718198; }
.empty-state strong { display:block; margin:.5rem 0 .3rem; color:#263750; font-size:1rem; }
.empty-icon { color:#8fa2bd; font-size:1.6rem; }
.section-topline { display:flex; justify-content:space-between; align-items:end; gap:1rem; margin:1.65rem 0 .75rem; }
.section-topline p { margin:0; font-size:.84rem; }
.comment-card { padding:.85rem 1rem; margin:.6rem 0; border:1px solid #e9eef5; border-radius:11px; background:#fbfcfe; }
.mini-label { color:#8090a4; text-transform:uppercase; font-size:.68rem; font-weight:700; letter-spacing:.08em; }
@media (max-width: 900px) { .block-container { padding:1.35rem 1.1rem 2.5rem; } .login-hero { min-height:400px; padding:1.7rem; } .hero-title { font-size:2.15rem; margin-top:2rem; } }
@media (max-width: 600px) { h1 { font-size:1.65rem!important; } .login-hero { min-height:330px; } .hero-title { font-size:1.85rem; } }
</style>
""", unsafe_allow_html=True)


def init_app():
    try:
        seed()
    except Exception as exc:
        logger.exception("Database initialization failed")
        st.error("Could not connect to the database. Check DATABASE_URL and database availability.")
        if APP_ENV == "development":
            st.caption("For local evaluation, SQLite is used when DATABASE_URL is not set.")
        st.stop()


def flash_error(exc):
    logger.info("User operation rejected: %s", exc)
    st.error(str(exc))


def login_screen():
    hero, form_column = st.columns([1.08, .92], gap="large")
    with hero:
        st.markdown("""
        <section class="login-hero">
          <div>
            <div class="brand-lockup"><div class="brand-mark">✦</div><div><div class="brand-name">Northstar Service Desk</div><div class="brand-sub">IT support workspace</div></div></div>
            <div class="hero-kicker">A clearer way to get support</div>
            <div class="hero-title">Help your team get back to what matters.</div>
            <div class="hero-copy">One place to report technical issues, follow progress, and work with IT support from first message to resolution.</div>
            <div class="hero-points">
              <div class="hero-point"><span class="hero-check">✓</span> Track every request with a clear status</div>
              <div class="hero-point"><span class="hero-check">✓</span> Keep troubleshooting and updates together</div>
              <div class="hero-point"><span class="hero-check">✓</span> Give support teams a shared view of the queue</div>
            </div>
          </div>
          <div class="hero-foot">Secure access for employees, IT support, and administrators</div>
        </section>
        """, unsafe_allow_html=True)
    with form_column:
        st.markdown('<p class="eyebrow">WELCOME BACK</p>', unsafe_allow_html=True)
        st.subheader("Sign in to your workspace")
        st.caption("Use your work email to continue.")
        login, signup = st.tabs(["Sign in", "Create employee account"])
        with login:
            with st.form("login_form"):
                email = st.text_input("Work email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
            if submitted:
                try:
                    with SessionLocal() as session:
                        user = authenticate(session, email, password)
                        st.session_state.user_id = user.user_id
                        st.session_state.last_activity = time.time()
                        st.rerun()
                except (ValueError, PermissionError) as exc:
                    flash_error(exc)
        with signup:
            with st.form("signup_form"):
                name = st.text_input("Full name")
                email = st.text_input("Work email", key="reg_email")
                password = st.text_input("Password", type="password", key="reg_password", help="At least 10 characters with a letter and a number")
                submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)
            if submitted:
                try:
                    with SessionLocal() as session:
                        user = register_user(session, name, email, password)
                        st.session_state.user_id = user.user_id
                        st.session_state.last_activity = time.time()
                        st.success("Account created.")
                        st.rerun()
                except ValueError as exc:
                    flash_error(exc)


STATUS_STYLES = {
    "Open": "background-color:#edf4ff;color:#2457bd;font-weight:700;border-radius:999px;",
    "In Progress": "background-color:#fff4e5;color:#a85b07;font-weight:700;border-radius:999px;",
    "Waiting for Employee": "background-color:#f5edff;color:#7240aa;font-weight:700;border-radius:999px;",
    "Resolved": "background-color:#e9f8f0;color:#14744a;font-weight:700;border-radius:999px;",
    "Closed": "background-color:#f0f2f5;color:#5c6879;font-weight:700;border-radius:999px;",
}
PRIORITY_STYLES = {
    "Critical": "color:#b4232b;font-weight:750;",
    "High": "color:#bb5a15;font-weight:700;",
    "Medium": "color:#315daf;font-weight:650;",
    "Low": "color:#526173;font-weight:600;",
}


def status_badge(status):
    badge_class = {"Open": "open", "In Progress": "progress", "Waiting for Employee": "waiting", "Resolved": "resolved", "Closed": "closed"}.get(status, "closed")
    return f'<span class="badge badge-{badge_class}">{escape(status)}</span>'


def priority_badge(priority):
    badge_class = {"Critical": "critical", "High": "high", "Medium": "medium", "Low": "low"}.get(priority, "low")
    return f'<span class="badge badge-{badge_class}">{escape(priority)}</span>'


def ticket_table(tickets):
    rows = [{"Ticket": t.ticket_number, "Title": t.title, "Category": t.category.category_name,
             "Priority": t.priority, "Status": t.status,
             "Assigned agent": t.assignee.full_name if t.assignee else "Unassigned",
             "Created": t.created_at.strftime("%d %b %Y") if t.created_at else ""} for t in tickets]
    if rows:
        frame = pd.DataFrame(rows)
        styled = frame.style.map(lambda v: STATUS_STYLES.get(v, ""), subset=["Status"]).map(lambda v: PRIORITY_STYLES.get(v, ""), subset=["Priority"])
        st.dataframe(styled, use_container_width=True, hide_index=True, height=min(440, 42 * len(frame) + 40),
                     column_config={"Ticket": st.column_config.TextColumn("Ticket ID", width="small"),
                                    "Title": st.column_config.TextColumn("Issue", width="large"),
                                    "Category": st.column_config.TextColumn("Category", width="medium"),
                                    "Priority": st.column_config.TextColumn("Priority", width="small"),
                                    "Status": st.column_config.TextColumn("Status", width="medium"),
                                    "Assigned agent": st.column_config.TextColumn("Assigned to", width="medium"),
                                    "Created": st.column_config.TextColumn("Created", width="small")})
    else:
        st.markdown('<div class="empty-state"><div class="empty-icon">⌕</div><strong>No tickets found</strong><div>Try adjusting your filters or create a new support request.</div></div>', unsafe_allow_html=True)


def dashboard(user, tickets):
    st.markdown(f'<p class="eyebrow">{user.role.upper()} WORKSPACE</p>', unsafe_allow_html=True)
    first_name = escape(user.full_name.split()[0])
    st.title(f"Good to see you, {first_name}")
    dashboard_copy = {
        Role.EMPLOYEE.value: "A quick look at your support requests and latest updates.",
        Role.AGENT.value: "Your assigned queue, priorities, and employee follow-ups.",
        Role.ADMIN.value: "Support operations at a glance across your organization.",
    }
    st.markdown(f'<p class="page-intro">{dashboard_copy.get(user.role, "Your IT support workspace.")}</p>', unsafe_allow_html=True)
    if user.role == Role.ADMIN.value:
        with SessionLocal() as session:
            employee_count = session.scalar(select(func.count()).select_from(User).where(User.role == Role.EMPLOYEE.value)) or 0
            agent_count = session.scalar(select(func.count()).select_from(User).where(User.role == Role.AGENT.value)) or 0
        values = [employee_count, agent_count, len(tickets), sum(t.status == "Open" for t in tickets), sum(t.status == "Resolved" for t in tickets)]
        labels = ["Employees", "Agents", "Total tickets", "Open tickets", "Resolved tickets"]
    elif user.role == Role.EMPLOYEE.value:
        values = [len(tickets), sum(t.status == "Open" for t in tickets), sum(t.status == "In Progress" for t in tickets), sum(t.status == "Resolved" for t in tickets)]
        labels = ["Total tickets", "Open", "In progress", "Resolved"]
    else:
        values = [len(tickets), sum(t.status == "Open" for t in tickets), sum(t.priority == "Critical" for t in tickets), sum(t.status == "Waiting for Employee" for t in tickets)]
        labels = ["Assigned tickets" if user.role == Role.AGENT.value else "Total tickets", "Open", "Critical", "Waiting"]
    cols = st.columns(len(labels))
    for col, label, value in zip(cols, labels, values):
        col.metric(label, value)
    st.markdown('<div class="section-topline"><div><p class="eyebrow">LATEST ACTIVITY</p><h3>Recent tickets</h3></div><p>Your latest 8 requests</p></div>', unsafe_allow_html=True)
    ticket_table(tickets[:8])
    if user.role == Role.ADMIN.value and tickets:
        data = pd.DataFrame([{"Category": t.category.category_name, "Priority": t.priority,
                              "Agent": t.assignee.full_name if t.assignee else "Unassigned"} for t in tickets])
        left, right = st.columns(2)
        left.plotly_chart(style_figure(px.histogram(data, x="Category", color="Priority", barmode="group", title="Recent 50 tickets by category and priority")), use_container_width=True, config={"displayModeBar": False, "responsive": True})
        right.plotly_chart(style_figure(px.bar(data.groupby("Agent", as_index=False).size(), x="Agent", y="size", title="Agent workload · recent 50 tickets", labels={"size": "Tickets"})), use_container_width=True, config={"displayModeBar": False, "responsive": True})


def style_figure(figure):
    figure.update_layout(
        template="plotly_white", font_family="DM Sans, sans-serif", font_color="#465873",
        title_font_family="Manrope, sans-serif", title_font_size=15, title_font_color="#20314a",
        paper_bgcolor="rgba(255,255,255,0)", plot_bgcolor="rgba(255,255,255,0)",
        margin={"l": 18, "r": 18, "t": 52, "b": 20},
        colorway=["#315eea", "#12a594", "#f0a149", "#8b6bd6", "#d75b68", "#64748b"],
        legend_title_text="",
    )
    figure.update_xaxes(showgrid=False, linecolor="#e8edf4", tickfont_color="#708099")
    figure.update_yaxes(gridcolor="#edf1f6", zeroline=False, tickfont_color="#708099")
    return figure


def ticket_detail(session, user, ticket):
    with st.container(border=True):
        st.markdown(f'<div class="ticket-heading"><span class="ticket-number">{escape(ticket.ticket_number)}</span>{status_badge(ticket.status)}{priority_badge(ticket.priority)}</div>', unsafe_allow_html=True)
        st.markdown(f"### {escape(ticket.title)}")
        st.markdown(f'<div class="ticket-description">{escape(ticket.description)}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="detail-meta"><span class="meta-chip">{escape(ticket.category.category_name)}</span>'
            f'<span class="meta-chip">Opened by {escape(ticket.creator.full_name)}</span>'
            f'<span class="meta-chip">Assigned to {escape(ticket.assignee.full_name if ticket.assignee else "Unassigned")}</span>'
            f'<span class="meta-chip">Created {ticket.created_at:%d %b %Y}</span>'
            f'<span class="meta-chip">Updated {ticket.updated_at:%d %b %Y}</span></div>', unsafe_allow_html=True)
    comments, history = ticket_activity(session, user, ticket.ticket_id)
    with st.expander("Activity history", expanded=False):
        for item in history:
            st.markdown(
                f'<div class="activity-row"><span class="mini-label">{item.changed_at:%d %b %Y · %H:%M}</span><br>'
                f'<strong>{escape(item.actor.full_name)}</strong> · {escape(item.event_type)}'
                f'<br>{escape(item.old_value or "—")} <span style="color:#9aa8ba">→</span> {escape(item.new_value or "—")}</div>',
                unsafe_allow_html=True)
    with st.expander(f"Comments ({len(comments)})", expanded=True):
        for comment in comments:
            with st.container(border=True):
                st.markdown(f'**{escape(comment.user.full_name)}** <span class="mini-label">· {comment.created_at:%d %b %Y at %H:%M}</span>', unsafe_allow_html=True)
                st.write(comment.comment_text)
        if ticket.status != "Closed":
            with st.form(f"comment_{ticket.ticket_id}"):
                body = st.text_area("Add a comment", max_chars=5000)
                if st.form_submit_button("Post comment"):
                    try:
                        add_comment(session, user, ticket.ticket_id, body)
                        st.success("Comment added.")
                        st.rerun()
                    except (ValueError, PermissionError) as exc:
                        flash_error(exc)
    permitted = sorted(TRANSITIONS.get(ticket.status, set())) if user.role in (Role.AGENT.value, Role.ADMIN.value) else (["In Progress"] if ticket.status == "Resolved" else [])
    if permitted:
        cols = st.columns([1, 3])
        with cols[0]:
            next_status = st.selectbox("Update status", permitted, key=f"status_{ticket.ticket_id}")
            if st.button("Save status", key=f"save_status_{ticket.ticket_id}"):
                try:
                    update_status(session, user, ticket.ticket_id, next_status)
                    st.success("Ticket status updated.")
                    st.rerun()
                except (ValueError, PermissionError) as exc:
                    flash_error(exc)


def create_ticket_view(user):
    st.markdown('<p class="eyebrow">EMPLOYEE SUPPORT</p>', unsafe_allow_html=True)
    st.title("Create a support ticket")
    st.markdown('<p class="page-intro">Tell us what is happening. Your request will be routed to the IT support team.</p>', unsafe_allow_html=True)
    with SessionLocal() as session:
        categories = list(session.scalars(select(Category).where(Category.is_active.is_(True)).order_by(Category.category_name)))
        with st.form("new_ticket"):
            title = st.text_input("What do you need help with?", max_chars=180)
            description = st.text_area("Describe the issue", height=160, max_chars=10000, help="Include what happened, when it started, and any steps already tried.")
            a, b = st.columns(2)
            category = a.selectbox("Category", categories, format_func=lambda x: x.category_name) if categories else None
            priority = b.selectbox("Priority", PRIORITIES, index=2)
            submitted = st.form_submit_button("Submit ticket", type="primary")
        if submitted:
            try:
                if not category:
                    raise ValueError("No ticket categories are available.")
                ticket = create_ticket(session, user, title, description, category.category_id, priority)
                st.success(f"Ticket {ticket.ticket_number} was submitted.")
            except (ValueError, PermissionError) as exc:
                flash_error(exc)


def tickets_view(user):
    st.markdown('<p class="eyebrow">SERVICE REQUESTS</p>', unsafe_allow_html=True)
    st.title("Ticket queue" if user.role != Role.EMPLOYEE.value else "My tickets")
    st.markdown('<p class="page-intro">Search, filter, and open a request to view its full activity.</p>', unsafe_allow_html=True)
    with SessionLocal() as session:
        try:
            c1, c2, c3 = st.columns(3)
            search = c1.text_input("Search tickets", placeholder="Ticket number or title")
            status = c2.selectbox("Status", ["All"] + [s.value for s in TicketStatus])
            priority = c3.selectbox("Priority", ["All"] + list(PRIORITIES))
            selected_status = None if status == "All" else status
            selected_priority = None if priority == "All" else priority
            total = count_tickets(session, user, search=search, status=selected_status, priority=selected_priority)
            page_size = 50
            pages = max(1, math.ceil(total / page_size))
            page = st.selectbox("Page", range(1, pages + 1), format_func=lambda value: f"Page {value} of {pages}")
            tickets = list_tickets(session, user, limit=page_size, offset=(page - 1) * page_size,
                                   search=search, status=selected_status, priority=selected_priority)
        except (ValueError, PermissionError) as exc:
            flash_error(exc)
            return
        st.caption(f"Showing {len(tickets)} of {total:,} matching tickets")
        ticket_table(tickets)
        if tickets:
            selected = st.selectbox("Open ticket details", tickets, format_func=lambda t: f"{t.ticket_number} — {t.title}", key="detail_select")
            if user.role == Role.ADMIN.value:
                agents = list(session.scalars(select(User).where(User.role == Role.AGENT.value, User.is_active.is_(True)).order_by(User.full_name)))
                names = ["Unassigned"] + [f"{a.full_name} ({a.email})" for a in agents]
                current_index = next((i + 1 for i, a in enumerate(agents) if a.user_id == selected.assigned_to), 0)
                choice = st.selectbox("Assign agent", names, index=current_index, key=f"assign_{selected.ticket_id}")
                if st.button("Save assignment", key=f"assignsave_{selected.ticket_id}"):
                    try:
                        chosen = agents[names.index(choice) - 1] if choice != "Unassigned" else None
                        assign_ticket(session, user, selected.ticket_id, chosen.user_id if chosen else None)
                        st.success("Assignment saved.")
                        st.rerun()
                    except (ValueError, PermissionError) as exc:
                        flash_error(exc)
            ticket_detail(session, user, selected)


def user_management(user):
    st.markdown('<p class="eyebrow">ADMINISTRATION</p>', unsafe_allow_html=True)
    st.title("People and access")
    st.markdown('<p class="page-intro">Manage employee and support agent accounts.</p>', unsafe_allow_html=True)
    with SessionLocal() as session:
        users = list_users(session, user)
        with st.expander("Create support agent"):
            with st.form("new_agent"):
                name = st.text_input("Agent full name")
                email = st.text_input("Agent email")
                password = st.text_input("Temporary password", type="password")
                if st.form_submit_button("Create agent"):
                    try:
                        create_agent(session, user, name, email, password)
                        st.success("Support agent created.")
                        st.rerun()
                    except (ValueError, PermissionError) as exc:
                        flash_error(exc)
        for account in users:
            c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
            c1.markdown(f"**{escape(account.full_name)}**")
            c2.caption(account.email)
            account_state = '<span class="badge badge-resolved">Active</span>' if account.is_active else '<span class="badge badge-closed">Inactive</span>'
            c3.markdown(f"{escape(account.role)} &nbsp; {account_state}", unsafe_allow_html=True)
            if account.user_id != user.user_id and c4.button("Deactivate" if account.is_active else "Activate", key=f"active_{account.user_id}"):
                try:
                    set_user_active(session, user, account.user_id, not account.is_active)
                    st.rerun()
                except (ValueError, PermissionError) as exc:
                    flash_error(exc)


def reports(user):
    st.markdown('<p class="eyebrow">OPERATIONS INSIGHTS</p>', unsafe_allow_html=True)
    st.title("Support analytics")
    st.markdown('<p class="page-intro">Trends across ticket volume, priority, workload, and resolution time.</p>', unsafe_allow_html=True)
    with SessionLocal() as session:
        try:
            tickets = report_tickets(session, user)
        except PermissionError as exc:
            flash_error(exc)
            return
        df = pd.DataFrame([{"Ticket": t.ticket_number, "Category": t.category.category_name, "Priority": t.priority, "Status": t.status,
                            "Agent": t.assignee.full_name if t.assignee else "Unassigned", "Created": t.created_at,
                            "Resolution hours": (t.resolved_at - t.created_at).total_seconds() / 3600 if t.resolved_at and t.created_at else None} for t in tickets])
        if df.empty:
            st.info("Analytics will appear when tickets have been submitted.")
            return
        average_resolution = df["Resolution hours"].dropna().mean()
        metric_values = [len(df), int((df["Status"] == "Open").sum()), int((df["Status"] == "Resolved").sum()),
                         f"{average_resolution:.1f}h" if pd.notna(average_resolution) else "—"]
        metric_labels = ["Tickets in scope", "Open", "Resolved", "Avg. resolution time"]
        metric_cols = st.columns(4)
        for column, label, value in zip(metric_cols, metric_labels, metric_values):
            column.metric(label, value)
        st.markdown('<div class="section-topline"><div><p class="eyebrow">TICKET MIX</p><h3>Volume and workload</h3></div></div>', unsafe_allow_html=True)
        a, b = st.columns(2)
        a.plotly_chart(style_figure(px.histogram(df, x="Category", color="Status", title="Tickets by category and status", barmode="group")), use_container_width=True, config={"displayModeBar": False, "responsive": True})
        b.plotly_chart(style_figure(px.pie(df, names="Priority", title="Ticket priority mix", hole=.58)), use_container_width=True, config={"displayModeBar": False, "responsive": True})
        c, d = st.columns(2)
        c.plotly_chart(style_figure(px.bar(df.groupby("Agent", as_index=False).size(), x="Agent", y="size", title="Agent workload", labels={"size": "Assigned tickets"})), use_container_width=True, config={"displayModeBar": False, "responsive": True})
        resolved = df.dropna(subset=["Resolution hours"])
        if not resolved.empty:
            d.plotly_chart(style_figure(px.box(resolved, x="Category", y="Resolution hours", title="Resolution time by category", points=False)), use_container_width=True, config={"displayModeBar": False, "responsive": True})
        else:
            with d:
                st.info("Resolution time charts appear after tickets have been resolved.")
        st.download_button("Download CSV report", df.to_csv(index=False).encode("utf-8"), "helpdesk_ticket_report.csv", "text/csv", type="primary")


def categories_admin(user):
    st.markdown('<p class="eyebrow">CONFIGURATION</p>', unsafe_allow_html=True)
    st.title("Ticket categories")
    st.markdown('<p class="page-intro">Keep the request catalog organized for employees and support teams.</p>', unsafe_allow_html=True)
    with SessionLocal() as session:
        categories = list_categories(session, user)
        for category in categories:
            c1, c2, c3 = st.columns([2, 4, 1])
            c1.write(category.category_name)
            c2.write(category.description)
            if c3.button("Deactivate" if category.is_active else "Activate", key=f"cat_{category.category_id}"):
                set_category_active(session, user, category.category_id, not category.is_active)
                st.rerun()
        with st.form("add_category"):
            name = st.text_input("New category")
            desc = st.text_input("Description")
            if st.form_submit_button("Add category"):
                try:
                    save_category(session, user, name, desc)
                    st.success("Category added.")
                    st.rerun()
                except (ValueError, PermissionError) as exc:
                    flash_error(exc)


def notifications_view(user):
    st.markdown('<p class="eyebrow">INBOX</p>', unsafe_allow_html=True)
    st.title("Notifications")
    st.markdown('<p class="page-intro">Updates about assignments, comments, and ticket status changes.</p>', unsafe_allow_html=True)
    with SessionLocal() as session:
        items = list(session.scalars(select(Notification).where(Notification.user_id == user.user_id).order_by(Notification.created_at.desc()).limit(100)))
        if not items:
            st.info("You’re all caught up.")
        for item in items:
            col1, col2 = st.columns([6, 1])
            marker = "🔔" if not item.is_read else "✓"
            col1.markdown(f"{marker} **{escape(item.message)}**" if not item.is_read else f"✓ {escape(item.message)}")
            col1.caption(item.created_at.strftime("%d %b %Y %H:%M"))
            if not item.is_read and col2.button("Mark read", key=f"read_{item.notification_id}"):
                item.is_read = True
                session.commit()
                st.rerun()


def main():
    init_app()
    user_id = st.session_state.get("user_id")
    if not user_id:
        login_screen()
        return
    last_activity = st.session_state.get("last_activity", 0)
    if time.time() - last_activity > 30 * 60:
        st.session_state.clear()
        st.info("Your session expired due to inactivity. Please sign in again.")
        login_screen()
        return
    st.session_state.last_activity = time.time()
    with SessionLocal() as session:
        user = session.get(User, user_id)
        if not user or not user.is_active:
            st.session_state.clear()
            st.warning("Your account is unavailable. Please sign in again.")
            st.rerun()
        user_data = {"user_id": user.user_id, "full_name": user.full_name, "email": user.email, "role": user.role, "is_active": user.is_active}
    user = User(**user_data)
    with SessionLocal() as session:
        unread = session.scalar(select(func.count()).select_from(Notification).where(Notification.user_id == user.user_id, Notification.is_read.is_(False))) or 0
    initials = "".join(part[0] for part in user.full_name.split()[:2]).upper()
    st.sidebar.markdown(
        '<div class="brand-lockup"><div class="brand-mark">✦</div><div><div class="brand-name">Northstar</div><div class="brand-sub">Service desk</div></div></div>'
        f'<div class="profile-card"><div class="profile-avatar">{escape(initials)}</div><div><div class="profile-name">{escape(user.full_name)}</div><div class="profile-role">{escape(user.role)}</div></div></div>',
        unsafe_allow_html=True)
    nav = ["Overview", "Create ticket", "Tickets", f"Notifications ({unread})"]
    if user.role == Role.ADMIN.value:
        nav += ["People and access", "Categories", "Analytics & reports"]
    elif user.role == Role.AGENT.value:
        nav += ["Analytics & reports"]
    nav_icons = {"Overview": "◫", "Create ticket": "+", "Tickets": "▤", "People and access": "♙", "Categories": "▦", "Analytics & reports": "⌁"}
    page = st.sidebar.radio("Workspace", nav, label_visibility="collapsed",
                            format_func=lambda item: f"{nav_icons.get(item.split(' (')[0], '◷')}   {item}")
    if st.sidebar.button("Sign out", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    if page == "Overview":
        with SessionLocal() as session:
            dashboard(user, list_tickets(session, user))
    elif page == "Create ticket":
        create_ticket_view(user)
    elif page == "Tickets":
        tickets_view(user)
    elif page.startswith("Notifications"):
        notifications_view(user)
    elif page == "People and access":
        user_management(user)
    elif page == "Categories":
        categories_admin(user)
    elif page == "Analytics & reports":
        reports(user)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Unhandled application error")
        st.error("Something went wrong while loading the application. Please try again.")
