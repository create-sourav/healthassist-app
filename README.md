# 🏥 HealthAssist – Personal Health Dashboard




Link: https://healthassist-app-9hw94do5sz6knqzz3ytq7s.streamlit.app/

A Python-based interactive personal health assessment dashboard built with Streamlit. Enter your health parameters and receive instant interpretations, risk assessments, and personalized recommendations using rule-based medical logic.

> ⚠️ **Disclaimer**: This project is for educational and health-awareness purposes only. It does not replace professional medical advice, diagnosis, or treatment.

---

## ✅ Key Features

- **BMI Calculation & Classification** – Automatic body mass index computation with WHO category classification
- **Blood Pressure Analysis** – Interpretation based on AHA/ACC guidelines
- **Blood Glucose Monitoring** – Support for fasting, random, and post-meal glucose levels
- **Complete Blood Count (CBC) Analysis** – Risk flags for hemoglobin, WBC, RBC, platelets, and MCV
- **Lipid Profile Interpretation** – Cholesterol and triglyceride assessment
- **Personalized Diet Recommendations** – Tailored nutritional advice based on health parameters
- **Custom Exercise Plans** – Activity recommendations aligned with your health status
- **Emergency Risk Detection** – Automatic flagging of critical health values
- **PDF Health Report** – Downloadable comprehensive health summary
- **CSV Data Export** – Save your health data for tracking and sharing
- **Clean Streamlit UI** – User-friendly, interactive interface

---

## 🧪 Health Parameters Supported

#### Basic Metrics
- Height & Weight
- Age & Gender

#### Vital Signs
- Blood Pressure (Systolic / Diastolic)
- Blood Glucose (Fasting / Random / Post-meal)

#### Complete Blood Count (CBC)
- Hemoglobin (Hb)
- White Blood Cell Count (WBC)
- Red Blood Cell Count (RBC)
- Platelet Count
- Mean Corpuscular Volume (MCV)

#### Lipid Profile
- Total Cholesterol
- LDL (Low-Density Lipoprotein)
- HDL (High-Density Lipoprotein)
- Triglycerides

**All interpretations follow clinical guidelines from:**
- World Health Organization (WHO)
- American Heart Association / American College of Cardiology (AHA/ACC)
- American Diabetes Association (ADA)
- National Institutes of Health (NIH)

---

## 🛠️ Technology Stack

| Technology | Purpose |
|------------|---------|
| **Python** | Core programming language |
| **Streamlit** | Web application framework |
| **Pandas** | Data manipulation and CSV export |
| **ReportLab** | PDF report generation |

---

#### Processing Flow

1. **Data Input** – User enters health values through the interactive dashboard
2. **Rule-Based Analysis** – Application applies medical logic to:
   - Classify BMI categories
   - Interpret blood pressure levels
   - Analyze glucose readings
   - Detect anemia and infection risks
   - Evaluate lipid disorders
3. **Report Generation** – System produces:
   - Comprehensive health summary
   - Critical risk flags
   - Personalized diet recommendations
   - Customized exercise plans
4. **Export Options** – Users can:
   - Download PDF health report
   - Export CSV data file

---

## 🚀 Quick Start

#### Prerequisites

- Python 3.7 or higher
- pip package manager

#### Installation

1. **Clone the repository**
   git clone https://github.com/yourusername/healthassist.git
   cd healthassist

2. **Install dependencies**
   pip install streamlit pandas reportlab

3. **Run the application**
   streamlit run healthassist.py

4. **Access the dashboard**
   - Open your browser and navigate to http://localhost:8501

---


## 🎯 Use Cases

- **Personal Health Tracking** – Monitor your health metrics over time
- **Educational Tool** – Learn about health parameter interpretations
- **Health Awareness** – Understand risk factors and preventive measures
- **Preliminary Assessment** – Get initial insights before medical consultation

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


---

## 👨‍⚕️ Medical Disclaimer

HealthAssist is an educational tool and should not be used as a substitute for professional medical advice, diagnosis, or treatment. Always consult with qualified healthcare professionals for medical concerns.

---

## 📧 Contact
email: souravmondal5f@gmail.com 
For questions or feedback, please open an issue on GitHub.



