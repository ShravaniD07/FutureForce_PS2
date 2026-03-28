import gradio as gr
from groq import Groq
import base64
from PIL import Image
import io
import json
import random
import datetime

# ─── CONFIG ───────────────────────────────────────────────
client = Groq(api_key="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")

CARBON_SAVED = {
    "Plastic": 0.5, "Paper": 0.3, "Metal": 1.2,
    "Glass": 0.8, "Organic": 0.2, "Electronic": 2.0, "Other": 0.1
}

DISPOSAL = {
    "Plastic":    ("♻️ BLUE BIN",    "Rinse clean before binning. Check the resin code (1–7) stamped on the bottom.", "#2196F3"),
    "Paper":      ("♻️ BLUE BIN",    "Must be dry and clean. Greasy or wet paper → green bin. Flatten cardboard first!", "#2196F3"),
    "Metal":      ("♻️ BLUE BIN",    "Rinse cans and tins thoroughly. Aluminium foil is recyclable if clean.", "#2196F3"),
    "Glass":      ("🟢 GREEN BIN",   "Rinse bottles and jars. Remove lids separately. No broken glass here!", "#4CAF50"),
    "Organic":    ("🟤 BROWN BIN",   "Perfect for composting! Food scraps, fruit peels, garden waste.", "#795548"),
    "Electronic": ("⚠️ E-WASTE",     "NEVER in regular bins! Drop at nearest e-waste centre (bbmp.gov.in).", "#FF5722"),
    "Other":      ("🗑️ BLACK BIN",   "Cannot be recycled. Try to reduce this waste next time!", "#607D8B"),
}

RESIN_INFO = {
    "1": ("PET",  "✅ Widely recyclable", "Water bottles, soft drink bottles", "#4CAF50"),
    "2": ("HDPE", "✅ Widely recyclable", "Milk jugs, shampoo bottles",        "#4CAF50"),
    "3": ("PVC",  "⚠️ Rarely recyclable", "Pipes, cables — check locally",     "#FF9800"),
    "4": ("LDPE", "⚠️ Check locally",     "Plastic bags, squeezable bottles",  "#FF9800"),
    "5": ("PP",   "✅ Often recyclable",  "Yoghurt cups, medicine bottles",    "#4CAF50"),
    "6": ("PS",   "❌ Rarely recyclable", "Styrofoam, disposable cups",        "#f44336"),
    "7": ("Other","⚠️ Check locally",     "Mixed or layered plastics",         "#FF9800"),
}

ECO_TIPS = [
    "🌊 Every tonne of recycled paper saves 17 trees and 26,000 litres of water!",
    "⚡ Recycling one aluminium can saves enough energy to run a TV for 3 hours!",
    "🌍 Glass is 100% recyclable and can be recycled endlessly without quality loss!",
    "🌱 Composting food waste reduces methane — a gas 25x more potent than CO₂!",
    "💧 Recycling 1 plastic bottle saves enough energy to power a light bulb for 6 hours!",
    "🏭 Recycling steel uses 75% less energy than making it from raw materials!",
    "🌿 India generates 62 million tonnes of waste annually — only 20% is processed!",
    "🐋 8 million tonnes of plastic enter our oceans every year. You can help stop this!",
]

TREE_EQUIVALENT = 0.021

state = {
    "carbon": 0.0, "count": 0, "history": [],
    "category_counts": {"Plastic":0,"Paper":0,"Metal":0,"Glass":0,"Organic":0,"Electronic":0,"Other":0},
    "session_start": datetime.datetime.now().strftime("%H:%M")
}

def get_badge(count):
    if count >= 20: return ("🏆 ECO CHAMPION", "#FFD700")
    if count >= 10: return ("🥇 GREEN HERO",   "#C0C0C0")
    if count >= 5:  return ("🥈 RECYCLER PRO", "#CD7F32")
    if count >= 1:  return ("🥉 ECO STARTER",  "#4CAF50")
    return ("📦 Scan Your First Item!", "#607D8B")

def get_impact(carbon_kg):
    trees = carbon_kg / (TREE_EQUIVALENT * 365)
    km    = carbon_kg / 0.21
    bulb  = carbon_kg / 0.006
    return trees, km, bulb

def analyze_waste(image):
    if image is None:
        return (make_placeholder_html("📷 Capture or upload an image to begin!"),
                make_stats_html(), make_history_html(), make_impact_html(), make_chart_html(),
                make_tip_html(random.choice(ECO_TIPS)))

    img = Image.fromarray(image)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode()

    try:
        resp = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role":"user","content":[
                {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}},
                {"type":"text","text":"""You are an expert waste classification AI for India's Swachh Bharat mission.
Examine the image carefully. Look for ANY numbers printed or moulded on plastic items (resin codes 1-7 inside recycling triangle).

Reply ONLY with a valid JSON object, no markdown:
{
  "item": "specific item name",
  "category": "Plastic or Paper or Metal or Glass or Organic or Electronic or Other",
  "resin_code": "1-7 ONLY if you can clearly see a recycling number on the plastic, else null",
  "confidence": "High or Medium or Low",
  "condition": "Clean or Dirty or Mixed",
  "recyclable": true or false,
  "tip": "one specific actionable Indian disposal tip under 20 words",
  "fun_fact": "one surprising environmental fact about this item under 20 words"
}"""}
            ]}],
            max_tokens=350
        )

        raw    = resp.choices[0].message.content.strip().replace("```json","").replace("```","").strip()
        result = json.loads(raw)

        cat        = result.get("category","Other")
        item       = result.get("item","Unknown Item")
        resin      = str(result.get("resin_code","")).strip() if result.get("resin_code") else None
        conf       = result.get("confidence","Medium")
        cond       = result.get("condition","Unknown")
        recyclable = result.get("recyclable", True)
        tip        = result.get("tip","Dispose responsibly.")
        fun_fact   = result.get("fun_fact","")

        carbon = CARBON_SAVED.get(cat, 0.1)
        state["carbon"] += carbon
        state["count"]  += 1
        state["category_counts"][cat] = state["category_counts"].get(cat, 0) + 1
        state["history"].insert(0, {"item":item,"category":cat,"carbon":carbon,
                                     "time":datetime.datetime.now().strftime("%H:%M")})
        if len(state["history"]) > 6:
            state["history"] = state["history"][:6]

        bin_label, bin_tip, bin_color = DISPOSAL.get(cat, DISPOSAL["Other"])

        # Resin code block
        resin_html = ""
        if resin and resin in RESIN_INFO and cat == "Plastic":
            code, status, examples, rcolor = RESIN_INFO[resin]
            resin_html = f"""
            <div style="background:linear-gradient(135deg,rgba(255,215,0,0.1),rgba(255,215,0,0.05));
                        border:2px solid #FFD700;border-radius:12px;padding:16px;margin:12px 0;">
                <div style="display:flex;align-items:center;gap:14px;">
                    <div style="background:#FFD700;border-radius:50%;min-width:52px;height:52px;
                                display:flex;align-items:center;justify-content:center;
                                font-size:26px;font-weight:900;color:#000;">{resin}</div>
                    <div>
                        <div style="color:#FFD700;font-size:15px;font-weight:800;">Resin Code {resin} — {code}</div>
                        <div style="color:{rcolor};font-size:13px;font-weight:600;margin-top:2px;">{status}</div>
                        <div style="color:#aaa;font-size:11px;margin-top:2px;">{examples}</div>
                    </div>
                </div>
            </div>"""
        elif cat == "Plastic" and not resin:
            resin_html = """
            <div style="background:rgba(255,255,255,0.03);border:1px dashed #333;border-radius:10px;
                        padding:10px;margin:10px 0;text-align:center;">
                <span style="color:#555;font-size:12px;">🔍 Flip the bottle over to see the ♻️ number (1–7)</span>
            </div>"""

        conf_color  = {"High":"#4CAF50","Medium":"#FF9800","Low":"#f44336"}.get(conf,"#FF9800")
        cond_color  = {"Clean":"#4CAF50","Dirty":"#f44336","Mixed":"#FF9800"}.get(cond,"#FF9800")
        rec_badge   = f'<span style="background:{"rgba(76,175,80,0.2)" if recyclable else "rgba(244,67,54,0.2)"};color:{"#4CAF50" if recyclable else "#f44336"};padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;">{"✅ RECYCLABLE" if recyclable else "❌ NOT RECYCLABLE"}</span>'
        cat_icons   = {"Plastic":"🧴","Paper":"📄","Metal":"🥫","Glass":"🫙","Organic":"🌿","Electronic":"💻","Other":"🗑️"}

        result_html = f"""
        <div style="font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#0d1117,#1a1a2e);
                    border-radius:16px;padding:20px;border:2px solid {bin_color};color:white;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
                <div style="background:{bin_color}22;border:2px solid {bin_color};border-radius:50%;
                            width:54px;height:54px;display:flex;align-items:center;justify-content:center;font-size:26px;">
                    {cat_icons.get(cat,"♻️")}
                </div>
                <div style="flex:1;">
                    <div style="font-size:20px;font-weight:800;color:white;">{item}</div>
                    <div style="display:flex;gap:8px;margin-top:4px;flex-wrap:wrap;align-items:center;">
                        {rec_badge}
                        <span style="color:{conf_color};font-size:11px;">● {conf}</span>
                        <span style="color:{cond_color};font-size:11px;">| {cond}</span>
                    </div>
                </div>
            </div>
            <div style="background:rgba(255,255,255,0.05);border-left:4px solid {bin_color};
                        border-radius:8px;padding:14px;margin-bottom:10px;">
                <div style="font-size:17px;font-weight:700;color:{bin_color};">{bin_label}</div>
                <div style="font-size:13px;color:#ddd;margin-top:5px;">{bin_tip}</div>
            </div>
            {resin_html}
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px;">
                <div style="background:rgba(0,188,212,0.08);border:1px solid rgba(0,188,212,0.2);border-radius:8px;padding:10px;">
                    <div style="font-size:10px;color:#00BCD4;letter-spacing:1px;margin-bottom:4px;">💡 DISPOSAL TIP</div>
                    <div style="font-size:12px;color:#ddd;">{tip}</div>
                </div>
                <div style="background:rgba(76,175,80,0.08);border:1px solid rgba(76,175,80,0.2);border-radius:8px;padding:10px;">
                    <div style="font-size:10px;color:#4CAF50;letter-spacing:1px;margin-bottom:4px;">🌍 FUN FACT</div>
                    <div style="font-size:12px;color:#ddd;">{fun_fact}</div>
                </div>
            </div>
            <div style="background:rgba(76,175,80,0.15);border-radius:8px;padding:10px;text-align:center;
                        border:1px solid rgba(76,175,80,0.3);">
                <span style="color:#4CAF50;font-weight:700;font-size:15px;">🌱 +{carbon:.1f} kg CO₂ saved by sorting correctly!</span>
            </div>
        </div>"""

        return (result_html, make_stats_html(), make_history_html(),
                make_impact_html(), make_chart_html(), make_tip_html(random.choice(ECO_TIPS)))

    except Exception as e:
        return (make_error_html(str(e)[:200]),
                make_stats_html(), make_history_html(), make_impact_html(), make_chart_html(),
                make_tip_html("Try again with a clearer image in good lighting!"))


def make_stats_html():
    count = state["count"]; carbon = state["carbon"]
    badge, badge_color = get_badge(count)
    next_t   = 1 if count==0 else 5 if count<5 else 10 if count<10 else 20
    progress = min(100, int((count/next_t)*100))
    return f"""
    <div style="font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#0d1117,#1a1a2e);
                border-radius:16px;padding:18px;color:white;">
        <div style="text-align:center;margin-bottom:14px;">
            <div style="font-size:22px;font-weight:900;color:{badge_color};">{badge}</div>
            <div style="font-size:10px;color:#555;letter-spacing:2px;">YOUR ECO RANK</div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px;">
            <div style="background:rgba(76,175,80,0.1);border:1px solid rgba(76,175,80,0.3);border-radius:10px;padding:12px;text-align:center;">
                <div style="font-size:26px;font-weight:800;color:#4CAF50;">{count}</div>
                <div style="font-size:11px;color:#888;">Items Sorted</div>
            </div>
            <div style="background:rgba(0,188,212,0.1);border:1px solid rgba(0,188,212,0.3);border-radius:10px;padding:12px;text-align:center;">
                <div style="font-size:26px;font-weight:800;color:#00BCD4;">{carbon:.2f}</div>
                <div style="font-size:11px;color:#888;">kg CO₂ Saved</div>
            </div>
        </div>
        <div style="margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;font-size:11px;color:#555;margin-bottom:5px;">
                <span>Next badge</span><span>{count}/{next_t}</span>
            </div>
            <div style="background:rgba(255,255,255,0.07);border-radius:20px;height:8px;">
                <div style="background:linear-gradient(90deg,#4CAF50,#00BCD4);border-radius:20px;height:8px;width:{progress}%;"></div>
            </div>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:12px;padding-top:8px;border-top:1px solid rgba(255,255,255,0.05);">
            <span style="color:{'#4CAF50' if count>=1  else '#333'};">🥉 1+</span>
            <span style="color:{'#4CAF50' if count>=5  else '#333'};">🥈 5+</span>
            <span style="color:{'#4CAF50' if count>=10 else '#333'};">🥇 10+</span>
            <span style="color:{'#4CAF50' if count>=20 else '#333'};">🏆 20+</span>
        </div>
    </div>"""


def make_history_html():
    icons = {"Plastic":"🧴","Paper":"📄","Metal":"🥫","Glass":"🫙","Organic":"🌿","Electronic":"💻","Other":"🗑️"}
    if not state["history"]:
        return """<div style="background:#0d1117;border-radius:12px;padding:16px;color:#444;text-align:center;font-family:'Segoe UI',sans-serif;font-size:13px;">No scans yet</div>"""
    rows = "".join(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
                    padding:7px 0;border-bottom:1px solid rgba(255,255,255,0.04);">
            <span style="font-size:13px;">{icons.get(h['category'],'♻️')} {h['item']}</span>
            <div style="text-align:right;">
                <div style="color:#4CAF50;font-size:12px;">+{h['carbon']:.1f}kg CO₂</div>
                <div style="color:#444;font-size:10px;">{h['time']}</div>
            </div>
        </div>""" for h in state["history"])
    return f"""<div style="font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#0d1117,#1a1a2e);border-radius:12px;padding:14px;color:white;">
        <div style="font-size:10px;color:#555;letter-spacing:2px;margin-bottom:8px;">📋 RECENT SCANS</div>{rows}</div>"""


def make_impact_html():
    carbon = state["carbon"]
    trees, km, bulb = get_impact(carbon)
    return f"""
    <div style="font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#0a1f0a,#0d1117);
                border:1px solid rgba(76,175,80,0.2);border-radius:14px;padding:16px;color:white;margin-top:10px;">
        <div style="font-size:10px;color:#4CAF50;letter-spacing:2px;margin-bottom:12px;">🌍 YOUR REAL-WORLD IMPACT</div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;text-align:center;">
            <div style="background:rgba(76,175,80,0.08);border-radius:10px;padding:10px;">
                <div style="font-size:20px;">🌳</div>
                <div style="font-size:18px;font-weight:800;color:#4CAF50;">{trees:.3f}</div>
                <div style="font-size:10px;color:#666;">Trees saved</div>
            </div>
            <div style="background:rgba(33,150,243,0.08);border-radius:10px;padding:10px;">
                <div style="font-size:20px;">🚗</div>
                <div style="font-size:18px;font-weight:800;color:#2196F3;">{km:.1f}</div>
                <div style="font-size:10px;color:#666;">km avoided</div>
            </div>
            <div style="background:rgba(255,193,7,0.08);border-radius:10px;padding:10px;">
                <div style="font-size:20px;">💡</div>
                <div style="font-size:18px;font-weight:800;color:#FFC107;">{bulb:.0f}</div>
                <div style="font-size:10px;color:#666;">hrs powered</div>
            </div>
        </div>
    </div>"""


def make_chart_html():
    counts = state["category_counts"]
    total  = max(sum(counts.values()), 1)
    colors = {"Plastic":"#2196F3","Paper":"#FF9800","Metal":"#9E9E9E",
              "Glass":"#4CAF50","Organic":"#795548","Electronic":"#FF5722","Other":"#607D8B"}
    bars = ""
    for cat, cnt in sorted(counts.items(), key=lambda x: -x[1]):
        if cnt == 0: continue
        pct = int((cnt/total)*100)
        bars += f"""
        <div style="margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;font-size:11px;color:#888;margin-bottom:3px;">
                <span>{cat}</span><span>{cnt}</span>
            </div>
            <div style="background:rgba(255,255,255,0.06);border-radius:20px;height:8px;">
                <div style="background:{colors.get(cat,'#4CAF50')};border-radius:20px;height:8px;width:{pct}%;"></div>
            </div>
        </div>"""
    if not bars:
        bars = "<div style='color:#333;text-align:center;padding:8px;font-size:12px;'>Scan items to see breakdown</div>"
    return f"""<div style="font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#0d1117,#1a1a2e);
                           border-radius:14px;padding:14px;color:white;margin-top:10px;">
        <div style="font-size:10px;color:#888;letter-spacing:2px;margin-bottom:10px;">📊 CATEGORY BREAKDOWN</div>{bars}</div>"""


def make_placeholder_html(msg):
    return f"""<div style="font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#0d1117,#1a1a2e);
                           border-radius:16px;padding:50px 20px;color:#444;text-align:center;border:2px dashed #222;">
        <div style="font-size:48px;margin-bottom:12px;">♻️</div>
        <div style="font-size:14px;">{msg}</div>
    </div>"""

def make_error_html(msg):
    return f"""<div style="font-family:'Segoe UI',sans-serif;background:#1a0000;border-radius:16px;
                           padding:20px;color:#f44336;border:2px solid #f44336;">
        ❌ {msg}<br><br><span style="color:#888;font-size:12px;">Try again with better lighting.</span></div>"""

def make_tip_html(tip):
    return f"""<div style="padding:12px;color:#4CAF50;font-family:'Segoe UI',sans-serif;
                           background:rgba(76,175,80,0.06);border:1px solid rgba(76,175,80,0.2);
                           border-radius:10px;font-size:13px;margin-top:8px;">🌱 {tip}</div>"""

def reset_all():
    state["carbon"] = 0.0; state["count"] = 0; state["history"] = []
    state["category_counts"] = {k:0 for k in state["category_counts"]}
    state["session_start"] = datetime.datetime.now().strftime("%H:%M")
    return (make_placeholder_html("🔄 Reset! Ready to scan!"),
            make_stats_html(), make_history_html(), make_impact_html(), make_chart_html(),
            make_tip_html(random.choice(ECO_TIPS)))


CSS = """
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;800;900&display=swap');
body, .gradio-container {
    background: linear-gradient(135deg,#040a04 0%,#050d0f 50%,#040a04 100%) !important;
    font-family: 'Space Grotesk', sans-serif !important;
}
.gr-button-primary {
    background: linear-gradient(135deg,#4CAF50,#00BCD4) !important;
    border: none !important; font-weight: 800 !important; font-size: 16px !important;
    border-radius: 12px !important; padding: 14px !important; letter-spacing: 1px !important;
    transition: all 0.3s !important; box-shadow: 0 4px 20px rgba(76,175,80,0.35) !important;
}
.gr-button-primary:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 30px rgba(76,175,80,0.5) !important; }
.gr-button-secondary {
    background: rgba(255,255,255,0.04) !important; border: 1px solid rgba(255,255,255,0.1) !important;
    color: #888 !important; border-radius: 12px !important;
}
.gr-box, .gr-panel { background: transparent !important; border: none !important; }
label { color: #555 !important; font-size: 11px !important; letter-spacing: 2px !important; text-transform: uppercase !important; }
"""

with gr.Blocks(css=CSS, title="🌍 Smart Bin | SYNAPSE 3.0") as app:

    gr.HTML("""
    <div style="text-align:center;padding:28px 20px 10px;font-family:'Space Grotesk',sans-serif;">
        <div style="font-size:11px;letter-spacing:5px;color:#4CAF50;margin-bottom:10px;">SYNAPSE 3.0 × AICVS × GDG CUMMINS</div>
        <h1 style="font-size:48px;font-weight:900;margin:0;line-height:1;
                   background:linear-gradient(135deg,#4CAF50 0%,#00BCD4 50%,#8BC34A 100%);
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent;">🌍 SMART BIN</h1>
        <p style="color:#555;font-size:13px;margin-top:10px;letter-spacing:2px;">AI-POWERED CIRCULAR ECONOMY · COMPUTER VISION WASTE ASSISTANT</p>
        <div style="display:flex;justify-content:center;gap:10px;margin-top:12px;flex-wrap:wrap;">
            <span style="background:rgba(76,175,80,0.12);border:1px solid rgba(76,175,80,0.4);border-radius:20px;padding:4px 12px;font-size:11px;color:#4CAF50;">♻️ 7 Categories</span>
            <span style="background:rgba(0,188,212,0.12);border:1px solid rgba(0,188,212,0.4);border-radius:20px;padding:4px 12px;font-size:11px;color:#00BCD4;">🔢 Resin Code 1–7</span>
            <span style="background:rgba(255,215,0,0.12);border:1px solid rgba(255,215,0,0.4);border-radius:20px;padding:4px 12px;font-size:11px;color:#FFD700;">🏆 Live Gamification</span>
            <span style="background:rgba(255,87,34,0.12);border:1px solid rgba(255,87,34,0.4);border-radius:20px;padding:4px 12px;font-size:11px;color:#FF5722;">📊 Real-Time Impact</span>
            <span style="background:rgba(139,195,74,0.12);border:1px solid rgba(139,195,74,0.4);border-radius:20px;padding:4px 12px;font-size:11px;color:#8BC34A;">📷 Live Webcam</span>
        </div>
    </div>""")

    with gr.Row(equal_height=False):
        with gr.Column(scale=1):
            webcam    = gr.Image(sources=["webcam","upload"], label="📷 POINT CAMERA AT WASTE ITEM", type="numpy", height=300)
            scan_btn  = gr.Button("🔍  SCAN & CLASSIFY", variant="primary", size="lg")
            reset_btn = gr.Button("🔄  Reset Score", variant="secondary")
            tip_out   = gr.HTML(make_tip_html(random.choice(ECO_TIPS)))

        with gr.Column(scale=1):
            result_html = gr.HTML(make_placeholder_html("📷 Capture a waste item to begin!"))
            impact_html = gr.HTML(make_impact_html())

        with gr.Column(scale=1):
            stats_html   = gr.HTML(make_stats_html())
            chart_html   = gr.HTML(make_chart_html())
            history_html = gr.HTML(make_history_html())

    gr.HTML("""
    <div style="font-family:'Space Grotesk',sans-serif;margin-top:16px;background:rgba(255,255,255,0.02);
                border:1px solid rgba(255,255,255,0.06);border-radius:16px;padding:18px;">
        <div style="font-size:10px;color:#555;letter-spacing:3px;margin-bottom:12px;">🗂️ INDIA BIN REFERENCE GUIDE</div>
        <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;text-align:center;">
            <div style="background:rgba(33,150,243,0.08);border:1px solid rgba(33,150,243,0.3);border-radius:10px;padding:12px;">
                <div style="font-size:18px;">♻️</div><div style="color:#2196F3;font-weight:700;font-size:12px;margin-top:4px;">BLUE</div>
                <div style="color:#555;font-size:10px;margin-top:3px;">Plastic · Paper · Metal</div></div>
            <div style="background:rgba(76,175,80,0.08);border:1px solid rgba(76,175,80,0.3);border-radius:10px;padding:12px;">
                <div style="font-size:18px;">🫙</div><div style="color:#4CAF50;font-weight:700;font-size:12px;margin-top:4px;">GREEN</div>
                <div style="color:#555;font-size:10px;margin-top:3px;">Glass items</div></div>
            <div style="background:rgba(121,85,72,0.08);border:1px solid rgba(121,85,72,0.3);border-radius:10px;padding:12px;">
                <div style="font-size:18px;">🌿</div><div style="color:#795548;font-weight:700;font-size:12px;margin-top:4px;">BROWN</div>
                <div style="color:#555;font-size:10px;margin-top:3px;">Organic · Food</div></div>
            <div style="background:rgba(255,87,34,0.08);border:1px solid rgba(255,87,34,0.3);border-radius:10px;padding:12px;">
                <div style="font-size:18px;">💻</div><div style="color:#FF5722;font-weight:700;font-size:12px;margin-top:4px;">E-WASTE</div>
                <div style="color:#555;font-size:10px;margin-top:3px;">Collection centres</div></div>
            <div style="background:rgba(96,125,139,0.08);border:1px solid rgba(96,125,139,0.3);border-radius:10px;padding:12px;">
                <div style="font-size:18px;">🗑️</div><div style="color:#607D8B;font-weight:700;font-size:12px;margin-top:4px;">BLACK</div>
                <div style="color:#555;font-size:10px;margin-top:3px;">General waste</div></div>
        </div>
        <div style="margin-top:14px;padding-top:14px;border-top:1px solid rgba(255,255,255,0.04);">
            <div style="font-size:10px;color:#555;letter-spacing:3px;margin-bottom:10px;">🔢 PLASTIC RESIN CODE GUIDE — HOLD BOTTLE UPSIDE DOWN TO THE CAMERA!</div>
            <div style="display:grid;grid-template-columns:repeat(7,1fr);gap:6px;text-align:center;">
                <div style="background:rgba(76,175,80,0.08);border:1px solid rgba(76,175,80,0.2);border-radius:8px;padding:8px;">
                    <div style="color:#FFD700;font-weight:900;font-size:18px;">1</div><div style="color:#4CAF50;font-size:9px;">PET ✅</div></div>
                <div style="background:rgba(76,175,80,0.08);border:1px solid rgba(76,175,80,0.2);border-radius:8px;padding:8px;">
                    <div style="color:#FFD700;font-weight:900;font-size:18px;">2</div><div style="color:#4CAF50;font-size:9px;">HDPE ✅</div></div>
                <div style="background:rgba(255,152,0,0.08);border:1px solid rgba(255,152,0,0.2);border-radius:8px;padding:8px;">
                    <div style="color:#FFD700;font-weight:900;font-size:18px;">3</div><div style="color:#FF9800;font-size:9px;">PVC ⚠️</div></div>
                <div style="background:rgba(255,152,0,0.08);border:1px solid rgba(255,152,0,0.2);border-radius:8px;padding:8px;">
                    <div style="color:#FFD700;font-weight:900;font-size:18px;">4</div><div style="color:#FF9800;font-size:9px;">LDPE ⚠️</div></div>
                <div style="background:rgba(76,175,80,0.08);border:1px solid rgba(76,175,80,0.2);border-radius:8px;padding:8px;">
                    <div style="color:#FFD700;font-weight:900;font-size:18px;">5</div><div style="color:#4CAF50;font-size:9px;">PP ✅</div></div>
                <div style="background:rgba(244,67,54,0.08);border:1px solid rgba(244,67,54,0.2);border-radius:8px;padding:8px;">
                    <div style="color:#FFD700;font-weight:900;font-size:18px;">6</div><div style="color:#f44336;font-size:9px;">PS ❌</div></div>
                <div style="background:rgba(255,152,0,0.08);border:1px solid rgba(255,152,0,0.2);border-radius:8px;padding:8px;">
                    <div style="color:#FFD700;font-weight:900;font-size:18px;">7</div><div style="color:#FF9800;font-size:9px;">Other ⚠️</div></div>
            </div>
        </div>
    </div>""")

    gr.HTML("""<div style="text-align:center;padding:18px;color:#333;font-size:11px;letter-spacing:2px;font-family:'Space Grotesk',sans-serif;">
        BUILT WITH ❤️ FOR SYNAPSE 3.0 · AICVS × GDG CUMMINS · POWERED BY GROQ LLAMA 4 AI
    </div>""")

    outs = [result_html, stats_html, history_html, impact_html, chart_html, tip_out]
    scan_btn.click(fn=analyze_waste, inputs=[webcam], outputs=outs)
    reset_btn.click(fn=reset_all, inputs=[], outputs=outs)

app.launch(share=False)
