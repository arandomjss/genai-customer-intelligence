"""Streamlit decision-support dashboard for saved pipeline outputs."""

from __future__ import annotations

import json
import html
import re
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
AGGREGATION_PATH = ROOT / "data" / "processed" / "product_intelligence" / "full_sample_1889_canonical.json"
RECOMMENDATION_PATH = ROOT / "data" / "processed" / "product_intelligence" / "decision_support_1889.json"
EXTRACTION_PATH = ROOT / "data" / "processed" / "extraction_runs" / "full_sample.jsonl"


@st.cache_data
def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@st.cache_data
def load_extractions(path: Path):
    records = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record.get("status") == "SUCCESS":
            records[record["review_id"]] = record
    return records


def render_table(frame: pd.DataFrame, empty_message: str | None = None) -> None:
    """Render a theme-aware, scrollable HTML table instead of Streamlit's white dataframe iframe."""
    if frame.empty:
        st.info(empty_message or "No records are available.")
        return
    headers = "".join(f"<th>{html.escape(str(column))}</th>" for column in frame.columns)
    body = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(value))}</td>" for value in row) + "</tr>"
        for row in frame.fillna("").itertuples(index=False, name=None)
    )
    st.markdown(f'<div class="table-shell"><table><thead><tr>{headers}</tr></thead><tbody>{body}</tbody></table></div>', unsafe_allow_html=True)


def render_sentiment_bars(frame: pd.DataFrame) -> None:
    """Render labels as normal HTML, so long aspect names can never vanish from chart axes."""
    maximum = max(1, int(frame[["positive", "negative", "neutral"]].sum(axis=1).max()))
    rows = []
    for item in frame.itertuples(index=False):
        positive, negative, neutral = int(item.positive), int(item.negative), int(item.neutral)
        total = positive + negative + neutral
        segments = "".join([
            f'<span class="segment positive" style="width:{positive / maximum * 100:.2f}%"></span>' if positive else "",
            f'<span class="segment negative" style="width:{negative / maximum * 100:.2f}%"></span>' if negative else "",
            f'<span class="segment neutral" style="width:{neutral / maximum * 100:.2f}%"></span>' if neutral else "",
        ])
        label = html.escape(str(item.aspect))
        rows.append(f'<div class="sentiment-row"><div class="sentiment-label" title="{label}">{label}</div><div class="sentiment-track">{segments}</div><div class="sentiment-total">{total}</div></div>')
    st.markdown('<div class="sentiment-bars">' + ''.join(rows) + '<div class="sentiment-legend"><span><i class="positive"></i>Positive</span><span><i class="negative"></i>Negative</span><span><i class="neutral"></i>Neutral</span><small>Total mentions</small></div></div>', unsafe_allow_html=True)


def render_recommendation(recommendation: dict) -> None:
    """Present recommendation details as scannable decision-support content."""
    priority = str(recommendation["priority"]).lower()
    action = html.escape(str(recommendation["suggested_action"]))
    rationale = html.escape(str(recommendation["confidence_rationale"]))
    limitation = html.escape(str(recommendation["limitation"]))
    support = (
        f'{recommendation["negative_review_count"]}/{recommendation["review_count"]} reviews '
        f'({recommendation["support_rate"]:.1%}) · {recommendation["negative_mentions"]} negative mentions'
    )
    st.markdown(
        f'<div class="recommendation-action"><span class="priority-badge {priority}">{priority} priority</span>'
        f'<strong>Suggested next step</strong><p>{action}</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="recommendation-support"><strong>Evidence strength</strong><br>{support}<br>'
        f'<span>{rationale}</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="recommendation-limit"><strong>Interpret carefully:</strong> {limitation}</div>', unsafe_allow_html=True)
    st.markdown("<div class='evidence-heading'>Example supporting reviews</div>", unsafe_allow_html=True)
    for evidence in recommendation["evidence"]:
        review_id = html.escape(str(evidence["review_id"]))
        excerpt = html.escape(str(evidence["evidence"]))
        st.markdown(f'<div class="evidence-item"><code>{review_id}</code><span>{excerpt}</span></div>', unsafe_allow_html=True)


def format_review_text(value: object) -> str:
    """Turn source HTML break tags into readable line breaks for the UI only."""
    text = html.unescape(str(value or ""))
    text = re.sub(r"<\s*br\s*/?\s*>", "\n", text, flags=re.IGNORECASE)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def aspect_chart(frame: pd.DataFrame, theme: dict[str, str]) -> alt.Chart:
    chart_data = frame.melt(id_vars="aspect", value_vars=["positive", "negative", "neutral"], var_name="sentiment", value_name="mentions")
    return (
        alt.Chart(chart_data)
        .mark_bar()
        .encode(
            y=alt.Y("aspect:N", sort=alt.EncodingSortField(field="mentions", op="sum", order="descending"), title=None, axis=alt.Axis(labelLimit=210, labelPadding=9)),
            x=alt.X("sum(mentions):Q", title="Extracted sentiment mentions"),
            color=alt.Color("sentiment:N", scale=alt.Scale(domain=["positive", "negative", "neutral"], range=["#16A34A", "#DC2626", "#718096"]), legend=alt.Legend(title=None, orient="bottom")),
            tooltip=["aspect:N", "sentiment:N", "mentions:Q"],
        )
        .properties(height=max(340, len(frame) * 30))
        .configure(background=theme["surface"])
        .configure_view(stroke=theme["border"], fill=theme["surface"])
        .configure_axis(labelColor=theme["muted"], titleColor=theme["muted"], gridColor=theme["border"], domainColor=theme["border"], tickColor=theme["border"])
        .configure_legend(labelColor=theme["muted"])
    )


def comparison_chart(frame: pd.DataFrame, theme: dict[str, str]) -> alt.Chart:
    chart_data = frame.melt(id_vars="product", value_vars=["positive supporting reviews", "negative supporting reviews"], var_name="sentiment", value_name="reviews")
    return (
        alt.Chart(chart_data)
        .mark_bar()
        .encode(
            x=alt.X("product:N", title=None, axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("reviews:Q", title="Supporting reviews"),
            xOffset="sentiment:N",
            color=alt.Color("sentiment:N", scale=alt.Scale(domain=["positive supporting reviews", "negative supporting reviews"], range=["#16A34A", "#DC2626"]), legend=alt.Legend(title=None, orient="bottom")),
            tooltip=["product:N", "sentiment:N", "reviews:Q"],
        )
        .properties(height=350)
        .configure(background=theme["surface"])
        .configure_view(stroke=theme["border"], fill=theme["surface"])
        .configure_axis(labelColor=theme["muted"], titleColor=theme["muted"], gridColor=theme["border"], domainColor=theme["border"], tickColor=theme["border"])
        .configure_legend(labelColor=theme["muted"])
    )


st.set_page_config(page_title="Customer Intelligence", layout="wide")
with st.sidebar:
    st.markdown("### Display")
    theme_mode = st.selectbox("Theme", ["Light", "Dark"], label_visibility="collapsed")

theme = {
    "Light": {
        "background": "#F4F7FB", "surface": "#FFFFFF", "surface_muted": "#F8FAFC",
        "text": "#10213D", "muted": "#5C6B82", "border": "#D7E0EB",
        "primary": "#4F46E5", "primary_soft": "#EEF2FF", "sidebar": "#EEF3F8",
        "table_header": "#EAF0F7", "notice": "#E6F0FF",
    },
    "Dark": {
        "background": "#0B1220", "surface": "#111C2E", "surface_muted": "#16243A",
        "text": "#E6EDF7", "muted": "#AAB8CC", "border": "#2A3A53",
        "primary": "#A5B4FC", "primary_soft": "#1E2850", "sidebar": "#0E192A",
        "table_header": "#1B2A42", "notice": "#152B4A",
    },
}[theme_mode]

st.markdown(f"""
<style>
    .stApp, [data-testid="stAppViewContainer"] {{background: {theme['background']}; color: {theme['text']};}}
    [data-testid="stHeader"], [data-testid="stToolbar"] {{background: {theme['background']} !important; color: {theme['text']} !important; border-bottom: 1px solid {theme['border']};}}
    [data-testid="stHeader"] * {{color: {theme['text']} !important;}}
    .block-container {{max-width: 1400px; padding-top: 2rem; padding-bottom: 3rem;}}
    section[data-testid="stSidebar"] {{background: {theme['sidebar']}; border-right: 1px solid {theme['border']};}}
    section[data-testid="stSidebar"] * {{color: {theme['text']};}}
    .hero {{background: linear-gradient(115deg, #1e1b4b, #4338ca 55%, #0f766e); border-radius: 20px; color: #fff; padding: 2rem 2.25rem; margin-bottom: 1.4rem; box-shadow: 0 14px 32px rgba(15, 23, 42, .18);}}
    .hero h1 {{font-size: 2.2rem; margin: 0 0 .35rem 0; color: #fff;}}
    .hero p {{font-size: 1rem; margin: 0; opacity: .9; color: #fff;}}
    .eyebrow {{font-size: .75rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; opacity: .8; margin-bottom: .5rem;}}
    h1, h2, h3, p, label, [data-testid="stMarkdownContainer"] {{color: {theme['text']};}}
    [data-testid="stMetric"] {{background: {theme['surface']}; border: 1px solid {theme['border']}; border-radius: 14px; padding: .85rem 1rem; box-shadow: 0 3px 8px rgba(15, 23, 42, .05);}}
    [data-testid="stMetricLabel"] {{font-size: .78rem; text-transform: uppercase; letter-spacing: .04em; color: {theme['muted']};}}
    [data-testid="stMetricValue"] {{color: {theme['text']};}}
    [data-testid="stVerticalBlockBorderWrapper"] {{background: {theme['surface']}; border-color: {theme['border']}; border-radius: 16px;}}
    [data-baseweb="tab-list"] {{gap: .4rem; border-bottom: 1px solid {theme['border']}; padding-bottom: .45rem;}}
    button[data-baseweb="tab"] {{border: 1px solid transparent; border-radius: 9px; color: {theme['muted']}; padding: .4rem .8rem; background: transparent;}}
    button[data-baseweb="tab"][aria-selected="true"] {{background: {theme['primary_soft']}; color: {theme['primary']}; border-color: {theme['primary']}; font-weight: 650;}}
    button[data-baseweb="tab"]:hover {{background: {theme['surface_muted']}; color: {theme['text']};}}
    [data-testid="stExpander"] {{background: {theme['surface']}; border: 1px solid {theme['border']}; border-radius: 12px;}}
    [data-testid="stAlert"] {{background: {theme['notice']}; color: {theme['text']}; border: 1px solid {theme['border']}; border-radius: 12px;}}
    .section-note {{color: {theme['muted']}; font-size: .9rem; margin-top: -.4rem; margin-bottom: .85rem;}}
    section[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"],
    section[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    section[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div > div {{background-color: {theme['surface']} !important; border-color: {theme['border']} !important;}}
    section[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] input,
    section[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] span {{color: {theme['text']} !important; -webkit-text-fill-color: {theme['text']} !important; background-color: transparent !important;}}
    section[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] svg {{fill: {theme['muted']} !important; color: {theme['muted']} !important;}}
    [data-baseweb="popover"], [data-baseweb="menu"] {{background: {theme['surface']} !important; color: {theme['text']} !important;}}
    .table-shell {{max-height: 330px; overflow: auto; border: 1px solid {theme['border']}; border-radius: 12px; background: {theme['surface']};}}
    .table-shell table {{width: 100%; border-collapse: collapse; font-size: .9rem;}}
    .table-shell th {{position: sticky; top: 0; z-index: 1; background: {theme['table_header']}; color: {theme['muted']}; text-align: left; font-weight: 700; padding: .7rem .75rem;}}
    .table-shell td {{color: {theme['text']}; border-top: 1px solid {theme['border']}; padding: .7rem .75rem; vertical-align: top; line-height: 1.35;}}
    .table-shell tr:nth-child(even) td {{background: {theme['surface_muted']};}}
    .sentiment-bars {{border: 1px solid {theme['border']}; border-radius: 12px; background: {theme['surface']}; padding: .8rem; overflow: hidden;}}
    .sentiment-row {{width: 100%; display: grid; grid-template-columns: minmax(88px, .9fr) minmax(110px, 2fr) 22px; align-items: center; gap: .45rem; margin: .42rem 0;}}
    .sentiment-label {{color: {theme['text']}; font-size: .82rem; line-height: 1.15; overflow-wrap: anywhere; min-width: 0;}}
    .sentiment-track {{display: flex; min-width: 0; min-height: 16px; background: {theme['surface_muted']}; border-radius: 5px; overflow: hidden; border: 1px solid {theme['border']};}}
    .segment {{min-width: 0; display: inline-block;}}
    .segment.positive, .sentiment-legend i.positive {{background: #16A34A;}}
    .segment.negative, .sentiment-legend i.negative {{background: #DC2626;}}
    .segment.neutral, .sentiment-legend i.neutral {{background: #718096;}}
    .sentiment-total {{color: {theme['muted']}; font-size: .72rem; text-align: right; font-variant-numeric: tabular-nums;}}
    .sentiment-legend {{display: flex; flex-wrap: wrap; gap: .7rem; align-items: center; color: {theme['muted']}; font-size: .75rem; margin-top: .8rem; padding-top: .65rem; border-top: 1px solid {theme['border']};}}
    .sentiment-legend span {{display: inline-flex; gap: .4rem; align-items: center;}}
    .sentiment-legend i {{display: inline-block; width: 10px; height: 10px; border-radius: 2px;}}
    .sentiment-legend small {{margin-left: auto; color: {theme['muted']}; font-size: .7rem; white-space: nowrap;}}
    .recommendation-action {{border-left: 4px solid {theme['primary']}; background: {theme['primary_soft']}; border-radius: 0 10px 10px 0; padding: .85rem 1rem; margin: .25rem 0 .8rem;}}
    .recommendation-action strong {{display: block; color: {theme['text']}; margin-top: .45rem; font-size: .82rem; text-transform: uppercase; letter-spacing: .04em;}}
    .recommendation-action p {{margin: .25rem 0 0; font-size: 1rem; font-weight: 650; color: {theme['text']};}}
    .priority-badge {{display: inline-block; border-radius: 999px; padding: .2rem .55rem; font-size: .72rem; font-weight: 750; letter-spacing: .04em; text-transform: uppercase; background: {theme['table_header']}; color: {theme['muted']};}}
    .priority-badge.high {{background: #FEE2E2; color: #B91C1C;}}
    .priority-badge.medium {{background: #FEF3C7; color: #92400E;}}
    .priority-badge.low {{background: #DCFCE7; color: #166534;}}
    .recommendation-support {{padding: .8rem 1rem; border: 1px solid {theme['border']}; border-radius: 10px; color: {theme['text']}; background: {theme['surface_muted']}; line-height: 1.5;}}
    .recommendation-support strong {{color: {theme['primary']};}}
    .recommendation-support span {{color: {theme['muted']}; font-size: .88rem;}}
    .recommendation-limit {{margin: .75rem 0; padding: .65rem .85rem; border-radius: 8px; color: {theme['muted']}; background: {theme['notice']}; font-size: .88rem;}}
    .evidence-heading {{font-size: .8rem; font-weight: 750; color: {theme['muted']}; text-transform: uppercase; letter-spacing: .04em; margin: 1rem 0 .4rem;}}
    .evidence-item {{display: flex; gap: .65rem; align-items: flex-start; padding: .55rem .65rem; margin: .35rem 0; border-left: 3px solid #16A34A; background: {theme['surface_muted']}; border-radius: 0 7px 7px 0;}}
    .evidence-item code {{color: #047857; white-space: nowrap; font-size: .78rem;}}
    .evidence-item span {{color: {theme['text']}; line-height: 1.35;}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="eyebrow">E-commerce reviews · Decision support</div>
  <h1>Customer Intelligence</h1>
  <p>Trace product feedback from high-level patterns to the original review evidence.</p>
</div>
""", unsafe_allow_html=True)

if not AGGREGATION_PATH.exists() or not RECOMMENDATION_PATH.exists() or not EXTRACTION_PATH.exists():
    st.error("Decision-support files are missing. Run the aggregation and recommendation commands first.")
    st.stop()

products = load_json(AGGREGATION_PATH)
recommendations = {item["parent_asin"]: item for item in load_json(RECOMMENDATION_PATH)}
extractions = load_extractions(EXTRACTION_PATH)
with st.sidebar:
    st.header("Analysis controls")
    st.caption("Select a product to inspect its extracted customer feedback.")
    selected_id = st.selectbox("Product", [product["parent_asin"] for product in products])
    st.divider()
    st.caption("Interim analysis: counts reflect valid extracted reviews available in the current dataset, not all source reviews.")
product = next(item for item in products if item["parent_asin"] == selected_id)
decision = recommendations[selected_id]

rows = []
for aspect in product["aspects"]:
    counts = aspect["sentiment_counts"]
    rows.append({"aspect": aspect["aspect"], "positive": counts.get("positive", 0), "negative": counts.get("negative", 0), "neutral": counts.get("neutral", 0)})
aspect_frame = pd.DataFrame(rows).sort_values(["negative", "positive"], ascending=False)

negative_aspects = aspect_frame[aspect_frame["negative"] > 0]
top_concern = negative_aspects.iloc[0] if not negative_aspects.empty else None
high_priority = sum(item["priority"] == "high" for item in decision["recommendations"])

st.subheader(f"Product {selected_id}")
metric_one, metric_two, metric_three = st.columns(3)
metric_one.metric("Valid extracted reviews", product["review_count"])
metric_two.metric("High-priority investigations", high_priority)
metric_three.metric("Top concern", top_concern["aspect"] if top_concern is not None else "No repeated concern", f"{int(top_concern['negative'])} negative mentions" if top_concern is not None else None)
st.write(decision["summary"])

overview_tab, recommendations_tab, evidence_tab, comparison_tab = st.tabs(["Overview", "Recommendations", "Evidence", "Compare products"])

with overview_tab:
    left, right = st.columns((1.25, 1), gap="large")
    with left:
        with st.container(border=True):
            st.subheader("Aspect sentiment")
            st.markdown("<div class='section-note'>Top 15 aspects, based on extracted sentiment mentions.</div>", unsafe_allow_html=True)
            render_sentiment_bars(aspect_frame.head(15))
    with right:
        with st.container(border=True):
            st.subheader("Recurring customer issues")
            render_table(pd.DataFrame(product["top_customer_issues"]), "No customer issues were extracted for this product.")
            st.divider()
            st.subheader("Feature requests")
            requests = pd.DataFrame(product["top_feature_requests"])
            render_table(requests, "No explicit feature requests were extracted for this product.")

with recommendations_tab:
    with st.container(border=True):
        st.subheader("Recommended investigations")
        st.markdown("<div class='section-note'>Recommendations are deterministic suggestions based on evidence-linked review patterns. They do not establish root cause.</div>", unsafe_allow_html=True)
        if not decision["recommendations"]:
            st.info("No negative aspect pattern currently meets the recommendation criteria.")
        for recommendation in decision["recommendations"]:
            with st.expander(f"{recommendation['priority'].upper()} · {recommendation['finding']} · {recommendation['negative_review_count']} supporting reviews", expanded=True):
                render_recommendation(recommendation)

with evidence_tab:
    with st.container(border=True):
        st.subheader("Evidence traceability")
        st.markdown("<div class='section-note'>Original model labels remain visible after canonicalization.</div>", unsafe_allow_html=True)
        evidence_rows = []
        for aspect in product["aspects"]:
            for evidence in aspect["evidence"]:
                evidence_rows.append({"aspect": aspect["aspect"], "original label": evidence.get("original_aspect", aspect["aspect"]), **evidence})
        evidence_frame = pd.DataFrame(evidence_rows)
        if evidence_frame.empty:
            st.info("No evidence records are available for this product.")
        else:
            search_term = st.text_input("Search evidence", placeholder="Search aspect, original label, review ID, or evidence text")
            filter_left, filter_right = st.columns(2)
            with filter_left:
                aspect_filter = st.multiselect("Canonical aspect", sorted(evidence_frame["aspect"].dropna().unique()))
            with filter_right:
                sentiment_filter = st.multiselect("Sentiment", sorted(evidence_frame["sentiment"].dropna().unique()))
            filtered_evidence = evidence_frame.copy()
            if aspect_filter:
                filtered_evidence = filtered_evidence[filtered_evidence["aspect"].isin(aspect_filter)]
            if sentiment_filter:
                filtered_evidence = filtered_evidence[filtered_evidence["sentiment"].isin(sentiment_filter)]
            if search_term.strip():
                search_text = filtered_evidence.fillna("").astype(str).agg(" ".join, axis=1).str.lower()
                filtered_evidence = filtered_evidence[search_text.str.contains(search_term.strip().lower(), regex=False)]
            st.caption(f"Showing {len(filtered_evidence)} of {len(evidence_frame)} evidence records.")
            render_table(filtered_evidence, "No evidence records match the current search and filters.")
    with st.container(border=True):
        st.subheader("Review trace")
        review_ids = sorted(review_id for review_id, record in extractions.items() if record["parent_asin"] == selected_id)
        if review_ids:
            selected_review_id = st.selectbox("Review ID", review_ids)
            selected_review = extractions[selected_review_id]
            st.caption(f"Rating: {selected_review.get('rating', 'unknown')}")
            st.info(format_review_text(selected_review["review_text"]))

with comparison_tab:
    with st.container(border=True):
        st.subheader("Cross-product comparison")
        st.markdown("<div class='section-note'>By default, only aspects supported by at least two reviews in at least two products are shown. This avoids over-interpreting one-off mentions.</div>", unsafe_allow_html=True)
        sparse_aspects = st.checkbox("Include sparse or single-product aspects", value=False)
        aspect_support: dict[str, dict[str, int]] = {}
        for item in products:
            for aspect in item["aspects"]:
                review_counts = aspect.get("sentiment_review_counts", {})
                support_count = sum(review_counts.values())
                aspect_support.setdefault(aspect["aspect"], {})[item["parent_asin"]] = support_count
        if sparse_aspects:
            comparable_aspects = sorted(aspect_support)
        else:
            comparable_aspects = sorted(
                aspect_name
                for aspect_name, product_support in aspect_support.items()
                if sum(count >= 2 for count in product_support.values()) >= 2
            )
        if not comparable_aspects:
            st.info("No aspects meet the shared-support threshold. Enable sparse aspects to inspect all extracted labels.")
            st.stop()
        comparison_aspect = st.selectbox("Aspect to compare", comparable_aspects)
        comparison_rows = []
        for item in products:
            match = next((aspect for aspect in item["aspects"] if aspect["aspect"] == comparison_aspect), None)
            negative_reviews = match.get("sentiment_review_counts", {}).get("negative", 0) if match else 0
            positive_reviews = match.get("sentiment_review_counts", {}).get("positive", 0) if match else 0
            comparison_rows.append({"product": item["parent_asin"], "valid reviews": item["review_count"], "positive supporting reviews": positive_reviews, "negative supporting reviews": negative_reviews, "negative review rate": negative_reviews / item["review_count"]})
        comparison = pd.DataFrame(comparison_rows).sort_values("negative review rate", ascending=False)
        st.altair_chart(comparison_chart(comparison, theme), width="stretch")
        render_table(comparison, "No comparison data is available.")
