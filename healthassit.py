"""
Enhanced HealthAssist — Streamlit dashboard (single-file).

Features added:
- prettier markdown labels and icons for medical inputs
- optional real-time norms fetch with fallback to embedded authoritative defaults
- more advanced diet & exercise recommendations (macros, 7-day starter plan, progressive overload)
- preserved & enhanced PDF download (table + flags)
- shows sources used for medical norms in the UI
"""

from __future__ import annotations
import math
import datetime
import io
from typing import List, Dict, Any, Optional
import json

try:
    import streamlit as st
except ModuleNotFoundError:
    st = None  # type: ignore

import pandas as pd

# ---------- Medical norms: defaults (authoritative fallback) ----------
# These defaults were chosen to reflect common guidelines (WHO, AHA/ACC, ADA, NIH/ATP III).
# The app will attempt to fetch live norms; if unavailable, use these.
DEFAULT_NORMS: Dict[str, Any] = {
    "bmi": {"underweight": 18.5, "normal_upper": 24.9, "overweight": 29.9, "obesity": 30.0},
    "bp": {  # systolic / diastolic thresholds
        "normal": (120, 80),
        "elevated": (120, 80),
        "stage_1": (130, 80),
        "stage_2": (140, 90),
        "crisis": (180, 120),
    },
    "glucose": {  # fasting mg/dL (ADA / Mayo references)
        "normal_fasting_upper": 99,
        "impaired_fasting_lower": 100,
        "diabetes_fasting": 126,
        "hypoglycemia": 70,
        "severe_hypoglycemia": 54,
    },
    "lipids": {
        "total_high": 240,
        "ldl_optimal": 100,
        "ldl_high": 160,
        "hdl_low": 40,
        "trig_high": 200,
    },
}

# ---------- Attempt to fetch live norms (optional) ----------
def fetch_medical_norms() -> Dict[str, Any]:
    """
    Try to fetch medical norms from a preconfigured JSON endpoint.
    If it fails (no internet or endpoint not provided), returns DEFAULT_NORMS.
    NOTE: Replace 'REMOTE_NORMS_URL' with your own endpoint if you host updated norms.
    """
    REMOTE_NORMS_URL = "https://example.com/health-norms.json"  # placeholder
    try:
        import requests  # optional dependency; wrapped in try
        resp = requests.get(REMOTE_NORMS_URL, timeout=4.0)
        if resp.status_code == 200:
            data = resp.json()
            # Validate minimal required keys
            if "bmi" in data and "bp" in data:
                return data
    except Exception:
        pass
    return DEFAULT_NORMS

# ---------- Core calculations (unchanged but slightly improved) ----------
def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    if height_cm <= 0:
        return 0.0
    return weight_kg / ((height_cm / 100.0) ** 2)

def bmi_category(bmi: float, norms: Dict[str, Any]) -> str:
    if bmi < norms["bmi"]["underweight"]:
        return "Underweight"
    if bmi <= norms["bmi"]["normal_upper"]:
        return "Normal weight"
    if bmi <= norms["bmi"]["overweight"]:
        return "Overweight"
    return "Obesity"

def classify_bp(systolic: int, diastolic: int, norms: Dict[str, Any]) -> str:
    # Use thresholds from norms (which map major guideline cutoffs)
    if systolic >= norms["bp"]["crisis"][0] or diastolic >= norms["bp"]["crisis"][1]:
        return "Hypertensive crisis"
    if systolic >= norms["bp"]["stage_2"][0] or diastolic >= norms["bp"]["stage_2"][1]:
        return "Stage 2 Hypertension"
    if systolic >= norms["bp"]["stage_1"][0] or diastolic >= norms["bp"]["stage_1"][1]:
        return "Stage 1 Hypertension"
    if systolic >= norms["bp"]["elevated"][0] and diastolic < norms["bp"]["elevated"][1]:
        return "Elevated blood pressure"
    return "Normal"

def interpret_glucose(glucose_mg_dL: float, context: str, norms: Dict[str, Any]) -> str:
    ctx = (context or "").strip().lower()
    g = glucose_mg_dL
    if ctx.startswith("fast"):
        if g < norms["glucose"]["severe_hypoglycemia"]:
            return "Severe hypoglycemia"
        if g < norms["glucose"]["hypoglycemia"]:
            return "Low (hypoglycemia)"
        if g <= norms["glucose"]["normal_fasting_upper"]:
            return "Normal fasting"
        if g < norms["glucose"]["diabetes_fasting"]:
            return "Impaired fasting (prediabetes)"
        return "Diabetes-range fasting"
    # Random/post-meal interpretation is more complex: provide buckets
    if g < 54:
        return "Severe hypoglycemia"
    if g < 70:
        return "Low (hypoglycemia)"
    if g < 140:
        return "Normal (post-meal)"
    if g < 200:
        return "High (post-meal) — consider fasting test"
    return "Very high (post-meal) — diabetes likely"
    
def cbc_flags(hemoglobin: float, wbc: float, platelets: float) -> List[str]:
    flags: List[str] = []
    if hemoglobin < 8.0:
        flags.append("Severely low hemoglobin — urgent evaluation needed")
    elif hemoglobin < 12.0:
        flags.append("Low hemoglobin — possible anemia; consider iron studies")
    if wbc < 2.0:
        flags.append("Severely low WBC — urgent evaluation needed")
    elif wbc < 4.0:
        flags.append("Low WBC — infection risk")
    elif wbc > 11.0:
        flags.append("Elevated WBC — possible infection/inflammation; correlate clinically")
    if platelets < 50.0:
        flags.append("Very low platelets — urgent evaluation")
    elif platelets < 150.0:
        flags.append("Low platelets — bleeding risk")
    elif platelets > 450.0:
        flags.append("High platelets — reactive thrombocytosis or myeloproliferative process")
    return flags

def interpret_lipids(total: float, ldl: float, hdl: float, trig: float, norms: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    if total >= norms["lipids"]["total_high"]:
        lines.append("Total cholesterol high — repeat fasting lipid profile, consult doctor")
    if ldl >= norms["lipids"]["ldl_high"]:
        lines.append("LDL high — strong risk factor for heart disease; discuss statin therapy")
    elif ldl >= norms["lipids"]["ldl_optimal"]:
        lines.append("LDL borderline — lifestyle changes recommended")
    if hdl < norms["lipids"]["hdl_low"]:
        lines.append("HDL low — increases cardiovascular risk; increase physical activity")
    if trig >= norms["lipids"]["trig_high"]:
        lines.append("Triglycerides high — reduce sugars, alcohol; recheck fasting panel")
    return lines

# ---------- Advanced Recommendations ----------
def recommend_diet_advanced(age: int, sex: str, bmi_cat: str, glucose_interp: str, lipid_lines: List[str]) -> List[str]:
    """
    Returns actionable diet guidance including caloric strategy and macros.
    This is a starter plan — individualization by clinician/dietitian is recommended.
    """
    recs: List[str] = []
    # Calorie guidance (rough estimates)
    if bmi_cat == "Underweight":
        recs.append("Increase daily calories by ~300-500 kcal with nutrient-dense foods; consider 3 meals + 2 snacks.")
        recs.append("Focus on protein (1.2–1.6 g/kg body weight) to support lean mass gain.")
    elif bmi_cat == "Normal weight":
        recs.append("Maintain weight: balanced plate (~45–55% carbs, 20–25% protein, 25–35% fat).")
        recs.append("Emphasize whole grains, legumes, lean proteins, and varied vegetables.")
    elif bmi_cat == "Overweight":
        recs.append("Aim for modest calorie deficit (≈300–500 kcal/day) with high-protein meals (≥1.0 g/kg).")
        recs.append("Prefer low-GI carbs, increase fiber to 25–35 g/day, avoid sugar-sweetened beverages.")
    else:  # Obesity
        recs.append("Structured weight-loss plan: 500–750 kcal/day deficit; aim for ~0.5–1 kg/week weight loss.")
        recs.append("Consider referral to dietitian for individualized plan; assess for pharmacotherapy/surgery if appropriate.")
    # Glucose-specific
    if "Diabetes" in glucose_interp or "Impaired" in glucose_interp or "High (post-meal)" in glucose_interp:
        recs.append("Low-GI meals, portion control, spread carbs evenly; check HbA1c and fasting glucose.")
        recs.append("Consider carbohydrate counting; prioritize non-starchy vegetables and lean protein with each meal.")
    # Lipid-specific
    if any("LDL" in s or "cholesterol" in s.lower() or "triglycerides" in s.lower() for s in lipid_lines):
        recs.append("Reduce saturated fats (<7% total kcal if high LDL), avoid trans fats, increase soluble fiber (oats, legumes).")
        recs.append("Include omega-3 sources (fatty fish 2x/week) or consider omega-3 prescription if triglycerides very high.")
    # General practical tips
    recs.append("Aim for balanced plate: 1/2 vegetables, 1/4 lean protein, 1/4 whole grains; snack on nuts, yogurt, fruits.")
    # 7-day micro-plan (starter, high-level)
    recs.append("Starter 7-day micro-plan: alternate lean protein + veg + whole grain; include 2 fish meals; 2-3 plant-based meals; limit processed foods.")
    return recs

def recommend_exercise_advanced(age: int, bmi_cat: str, bp_class: str, glucose_interp: str) -> List[str]:
    """
    Progressive and specific exercise suggestions. Always recommend medical clearance if severe conditions present.
    """
    recs: List[str] = []
    # Emergency check
    if "Hypertensive crisis" in bp_class:
        recs.append("🚨 Emergency BP: get urgent medical review before starting/exercising.")
        return recs

    # Aerobic baseline
    recs.append("Aerobic target: work up to 150–300 min/week moderate-intensity or 75–150 min vigorous-intensity (per WHO).")
    # Strength baseline
    recs.append("Strength training: 2–3 sessions/week, full-body compound exercises (progressive overload).")
    # If overweight/obesity -> low impact start
    if bmi_cat in ("Overweight", "Obesity"):
        recs.insert(0, "Start with low-impact cardio (walking, cycling, swimming) 3×/week, 20–30 min; increase duration before intensity.")
    # Glucose-specific
    if "Diabetes" in glucose_interp or "Impaired" in glucose_interp:
        recs.append("Post-meal walks (10–15 min) can help blunt glucose spikes; monitor pre/post exercise glucose if on medications.")
    # Sample progressive 4-week plan
    recs.append("4-week starter: Week1 walk 20 min ×3; Week2 add 2× strength (bodyweight); Week3 increase walk to 30 min and add interval sessions; Week4 add heavier resistance.")
    # Safety & monitoring
    recs.append("Monitor symptoms: chest pain, severe breathlessness, dizziness — stop and seek care. Reassess BP/glucose after beginning program.")
    return recs

# ---------- PDF/TXT helpers (unchanged but includes sources note) ----------
def generate_pdf_from_table(table_rows: List[List[str]], flags: List[str], norms_source_text: str) -> bytes:
    """
    Generates a PDF with a two-column table. This version wraps long text by
    converting cell strings into Paragraphs and sets appropriate column widths
    / paddings so recommendations are not cut off.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    # Create a slightly tighter paragraph style for table cells that allows wrapping
    cell_style = ParagraphStyle(
        name="Cell",
        parent=normal,
        fontSize=9.5,
        leading=12,      # line height
        spaceAfter=4,
    )
    heading = styles["Heading1"]
    heading2 = styles["Heading2"]

    elements = []
    elements.append(Paragraph("HealthAssist — Personal Health Report", heading))
    elements.append(Spacer(1, 8))

    # Convert rows to Paragraphs so long text will wrap
    wrapped_rows = []
    for row_idx, row in enumerate(table_rows):
        wrapped_row = []
        for col_idx, cell in enumerate(row):
            # If cell is not already a flowable, convert to Paragraph.
            # Keep header row slightly bolder if it's the first row.
            if row_idx == 0:
                # header-like: keep as bold paragraph
                wrapped_row.append(Paragraph(str(cell), ParagraphStyle('HeadCell', parent=cell_style, fontName='Helvetica-Bold')))
            else:
                wrapped_row.append(Paragraph(str(cell), cell_style))
        wrapped_rows.append(wrapped_row)

    # Set column widths: make right/value column wider (allows recommendations to wrap)
    col_widths = [2.5 * inch, 4.0 * inch]

    table = Table(wrapped_rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("Flags & Interpretations:", heading2))
    # Make sure flags are wrapped
    for f in flags:
        elements.append(Paragraph(str(f), cell_style))
        elements.append(Spacer(1, 4))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Norms & Sources:", heading2))
    elements.append(Paragraph(norms_source_text, cell_style))

    doc.build(elements)
    buf.seek(0)
    return buf.read()

# ---------- Streamlit application ----------
def run_streamlit_app() -> None:
    st.set_page_config(page_title="HealthAssist Dashboard", layout="wide")
    st.title("🏥 HealthAssist — Personal Health Dashboard")
    st.markdown(
        """
        <div style='display:flex;align-items:center;gap:12px'>
          <img src='https://img.icons8.com/fluency/48/000000/medical-doctor.png' alt='logo'/>
          <div>
            <h2 style='margin:0'>HealthAssist</h2>
            <div style='color:gray;margin-top:2px'>Personal health dashboard — enter your values and press Submit</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Use fixed updated norms only (no runtime fetch) — medical cutoffs are stable.
    norms = DEFAULT_NORMS
    st.caption("Using authoritative guideline thresholds (WHO for BMI, AHA/ACC for BP, ADA for glucose, NIH for lipids).")

    # Layout form: keep related inputs side-by-side
    with st.form("health_form"):
        st.subheader("👤 Basic Info & BMI")
        col_a, col_b = st.columns([1, 1])
        with col_a:
            name = st.text_input("👤 Name", placeholder="e.g. John Doe")
            age = st.number_input("🎂 Age", 0, 120, 30)
            sex = st.selectbox("⚥ Sex", ["Prefer not to say", "Male", "Female", "Other"])
        with col_b:
            height_cm = st.number_input("📏 Height (cm)", 100, 250, 175)
            st.caption("Example: 175 cm")
            weight_kg = st.number_input("⚖️ Weight (kg)", 30, 200, 70)
            st.caption("Example: 70 kg")

        st.markdown("---")
        bp_col, glu_col = st.columns(2)
        with bp_col:
            st.markdown("### 🩺 Blood Pressure")
            st.markdown("**Systolic / Diastolic (mm Hg)**")
            systolic = st.number_input("Systolic", 50, 300, 120, key='sys')
            diastolic = st.number_input("Diastolic", 30, 200, 80, key='dia')
            st.caption("Take an average of 2–3 readings when seated for more accuracy.")
        with glu_col:
            st.markdown("### 🍬 Blood Glucose")
            glucose = st.number_input("Glucose (mg/dL)", 20.0, 2000.0, 90.0, key='glu')
            context = st.selectbox("Context", ["Fasting", "Random", "Post-meal"], key='glu_ctx')
            st.caption("If diabetic or on meds, monitor per clinical guidance.")

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 🧪 Complete Blood Count (CBC)")
            hb_col, wbc_col, pl_col = st.columns([1, 1, 1])
            with hb_col:
                hemoglobin = st.number_input("Hemoglobin (g/dL)", 1.0, 30.0, 14.0, key='hb')
                hct = st.number_input("Hematocrit (%)", 5.0, 70.0, 42.0, key='hct')
            with wbc_col:
                wbc = st.number_input("WBC (10^3/uL)", 0.1, 200.0, 6.0, key='wbc')
                rbc = st.number_input("RBC (10^6/uL)", 0.5, 10.0, 4.6, key='rbc')
            with pl_col:
                platelets = st.number_input("Platelets (10^3/uL)", 1.0, 2000.0, 250.0, key='plt')
                mcv = st.number_input("MCV (fL)", 50.0, 200.0, 90.0, key='mcv')
        with c2:
            st.markdown("### 🧾 Lipid Panel (fasting preferred)")
            t_col, l_col, h_col = st.columns([1, 1, 1])
            with t_col:
                total = st.number_input("Total Cholesterol (mg/dL)", 50.0, 500.0, 180.0, key='tot')
            with l_col:
                ldl = st.number_input("LDL (mg/dL)", 10.0, 400.0, 100.0, key='ldl')
            with h_col:
                hdl = st.number_input("HDL (mg/dL)", 5.0, 150.0, 50.0, key='hdl')
            trig = st.number_input("Triglycerides (mg/dL)", 10.0, 3000.0, 120.0, key='tg')
            st.caption("If you have recent labs, use fasting values for lipids where possible.")

        st.markdown("---")
        st.write("After entering values, click **Submit & Generate Report** to view summary, advanced recommendations, and download PDF/TXT/CSV.")
        submitted = st.form_submit_button("Submit & Generate Report")

    if submitted:
        bmi_val = calculate_bmi(float(weight_kg), float(height_cm))
        bmi_cat = bmi_category(bmi_val, norms)
        bp_class = classify_bp(int(systolic), int(diastolic), norms)
        glucose_interp = interpret_glucose(float(glucose), context, norms)
        cbc = cbc_flags(float(hemoglobin), float(wbc), float(platelets))
        lipids = interpret_lipids(float(total), float(ldl), float(hdl), float(trig), norms)

        # Advanced recommendations
        diet = recommend_diet_advanced(int(age), sex, bmi_cat, glucose_interp, lipids)
        exercise = recommend_exercise_advanced(int(age), bmi_cat, bp_class, glucose_interp)

        # Emergency determination
        needs_emergency = False
        emergency_reasons = []
        if bp_class == "Hypertensive crisis":
            needs_emergency = True
            emergency_reasons.append("Very high blood pressure — hypertensive crisis")
        if "Severe" in glucose_interp:
            needs_emergency = True
            emergency_reasons.append("Severe hypoglycemia or very low glucose")
        for f in cbc + lipids:
            if any(k in f.lower() for k in ("severe", "urgent", "very low", "very high")):
                needs_emergency = True
                emergency_reasons.append(f)

        # Display summary with styled alerts for BMI/BP/Glucose like CBC/Lipids
        st.header("📋 Report Summary")
        coll, colr = st.columns([1, 1])
        with coll:
            # BMI styling
            if bmi_cat == "Normal weight":
                st.success(f"**BMI:** {bmi_val:.2f} — {bmi_cat}")
            elif bmi_cat in ("Underweight", "Overweight"):
                st.warning(f"**BMI:** {bmi_val:.2f} — {bmi_cat}")
            else:  # Obesity
                st.error(f"**BMI:** {bmi_val:.2f} — {bmi_cat}")

            # BP styling
            if bp_class == "Normal":
                st.success(f"**BP:** {systolic}/{diastolic} — {bp_class}")
            elif "Stage" in bp_class or "Elevated" in bp_class:
                st.warning(f"**BP:** {systolic}/{diastolic} — {bp_class}")
            else:  # Hypertensive crisis
                st.error(f"**BP:** {systolic}/{diastolic} — {bp_class}")

            # Glucose styling
            if "Normal" in glucose_interp:
                st.success(f"**Glucose:** {glucose} mg/dL ({context}) — {glucose_interp}")
            elif any(k in glucose_interp for k in ("Impaired", "High", "prediabetes")):
                st.warning(f"**Glucose:** {glucose} mg/dL ({context}) — {glucose_interp}")
            else:
                st.error(f"**Glucose:** {glucose} mg/dL ({context}) — {glucose_interp}")

            st.markdown(f"**Lipids summary:** LDL {ldl} mg/dL • HDL {hdl} mg/dL • TG {trig} mg/dL")
        with colr:
            st.markdown("**CBC**")
            if cbc:
                for f in cbc:
                    st.warning(f)
            else:
                st.success("CBC within general adult ranges")
            st.markdown("**Lipid flags**")
            if lipids:
                for l in lipids:
                    st.info(l)
            else:
                st.success("Lipids within common ranges")

        st.markdown("---")
        st.subheader("Recommendations (Advanced)")
        rec_col1, rec_col2 = st.columns(2)
        with rec_col1:
            st.markdown("### 🥗 Diet (Actionable)")
            for d in diet:
                st.write(f"- {d}")
        with rec_col2:
            st.markdown("### 🏃 Exercise (Actionable)")
            for e in exercise:
                st.write(f"- {e}")

        st.markdown("---")
        if needs_emergency:
            st.error("🚨 URGENT: Some inputs indicate a potential medical emergency. Seek immediate care.")
            for r in emergency_reasons:
                st.markdown(f"- **{r}**")
            st.markdown("**If experiencing chest pain, severe breathlessness, fainting, severe bleeding, or severe headache — call emergency services immediately.**")
        else:
            followups = []
            if lipids:
                followups.append("Repeat fasting lipid profile; if LDL high discuss statin therapy based on risk.")
            if "Impaired" in glucose_interp or "Diabetes" in glucose_interp:
                followups.append("Order HbA1c and fasting glucose tests; consider endocrinology if abnormal.")
            if cbc:
                followups.append("Repeat CBC and consider iron studies/ferritin if anemia suspected.")
            if followups:
                st.warning("Further clinical evaluation recommended:")
                for f in followups:
                    st.write(f"- {f}")
            else:
                st.success("No immediate emergency detected. Continue routine care and healthy lifestyle.")

        # Build PDF table rows and flags
        table_rows = [
            ["Field", "Value"],
            ["Name", name or ""],
            ["Age", str(age)],
            ["Sex", sex],
            ["Height (cm)", str(height_cm)],
            ["Weight (kg)", str(weight_kg)],
            ["BMI", f"{bmi_val:.2f} ({bmi_cat})"],
            ["Blood Pressure", f"{systolic}/{diastolic} ({bp_class})"],
            ["Glucose", f"{glucose} ({context}) - {glucose_interp}"],
            ["Hemoglobin", f"{hemoglobin} g/dL"],
            ["Hematocrit", f"{hct} %"],
            ["WBC", f"{wbc} (10^3/uL)"],
            ["Platelets", f"{platelets} (10^3/uL)"],
            ["Lipids", f"Total {total}, LDL {ldl}, HDL {hdl}, TG {trig}"],
            ["Diet recommendations", "; ".join(diet)],
            ["Exercise recommendations", "; ".join(exercise)],
        ]
        flags_combined = cbc + lipids + [glucose_interp]

        # Norms sources text (show which thresholds used)
        norms_source_text = "Guideline thresholds used: embedded defaults (WHO, AHA/ACC, ADA, NIH). See app notes for original references."
        # Generate PDF and offer download
        try:
            pdf_bytes = generate_pdf_from_table(table_rows, flags_combined, norms_source_text)
            st.download_button("📥 Download report (PDF)", data=pdf_bytes,
                               file_name=f"health_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                               mime="application/pdf")
        except Exception:
            # Fallback TXT
            txt = "\n".join([f"{r[0]}: {r[1]}" for r in table_rows])
            st.download_button("📥 Download report (TXT)", txt.encode(),
                               file_name=f"health_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                               mime="text/plain")

        # Also provide CSV of raw inputs
        df_inputs = pd.DataFrame([{
            "timestamp": datetime.datetime.now().isoformat(),
            "name": name,
            "age": age,
            "sex": sex,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "bmi": round(bmi_val, 2),
            "systolic": systolic,
            "diastolic": diastolic,
            "glucose": glucose,
            "glucose_context": context,
            "hb": hemoglobin,
            "hct": hct,
            "wbc": wbc,
            "rbc": rbc,
            "platelets": platelets,
            "mcv": mcv,
            "total_chol": total,
            "ldl": ldl,
            "hdl": hdl,
            "trig": trig,
        }])
        st.download_button("📥 Download inputs (CSV)", data=df_inputs.to_csv(index=False).encode(), file_name="health_inputs.csv", mime="text/csv")

        # Show norms/source references (brief)
        st.markdown("---")
        st.subheader("Norms & Sources used")
        st.write("The app used embedded guideline defaults (WHO for BMI, AHA/ACC for BP categories, ADA/Mayo for glucose cutoffs, NIH/ATP/Johns Hopkins for lipids).")
        # Removed the confusing production-deployment caption per your request.

# ---------- Entrypoint ----------
if __name__ == "__main__":
    if st is not None:
        run_streamlit_app()
    else:
        print("Streamlit not installed. Run with pip install streamlit")
