"""Global look & feel for the Streamlit app."""

APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
    letter-spacing: 0.3px;
}

/* hero banner */
.mc-hero {
    background: linear-gradient(135deg, #1a1206 0%, #3d2c0e 55%, #6b4e1d 100%);
    border: 1px solid #d4af3766;
    border-radius: 18px;
    padding: 2.2rem 2.6rem;
    margin-bottom: 1.4rem;
}
.mc-hero h1 {
    color: #f0e6c8;
    margin: 0 0 .4rem 0;
    font-size: 2.1rem;
}
.mc-hero p {
    color: #d9c48a;
    margin: 0;
    font-size: 1.02rem;
}

/* stat cards */
.mc-stat {
    background: #ffffff0d;
    border: 1px solid #d4af3733;
    border-radius: 14px;
    padding: 1.1rem 1.3rem;
    text-align: center;
}
.mc-stat .value {
    font-size: 1.9rem;
    font-weight: 700;
    color: #d4af37;
}
.mc-stat .label {
    font-size: .82rem;
    letter-spacing: .08em;
    text-transform: uppercase;
    opacity: .75;
}

/* project cards */
.mc-card {
    border: 1px solid #d4af3740;
    border-radius: 14px;
    padding: 1rem 1.2rem;
    margin-bottom: .8rem;
    background: #ffffff08;
}
.mc-card .title { font-weight: 600; font-size: 1.05rem; }
.mc-card .meta  { font-size: .85rem; opacity: .7; }

/* pill badge */
.mc-badge {
    display: inline-block;
    padding: .15rem .7rem;
    border-radius: 999px;
    border: 1px solid #d4af3766;
    color: #d4af37;
    font-size: .78rem;
    margin-right: .4rem;
}

/* primary buttons a touch more luxurious */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #b8860b, #d4af37);
    color: #1a1206;
    font-weight: 600;
    border: none;
    border-radius: 10px;
}
.stDownloadButton > button {
    border-radius: 10px;
}
</style>
"""


def hero(title: str, tagline: str) -> str:
    return f'<div class="mc-hero"><h1>{title}</h1><p>{tagline}</p></div>'


def stat_card(value: str, label: str) -> str:
    return f'<div class="mc-stat"><div class="value">{value}</div><div class="label">{label}</div></div>'
