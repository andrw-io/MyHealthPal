import streamlit as st # for the website 
import time
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime, timedelta
import os 
import openai # for the chatbot
from openai import OpenAI  # for the chatbot

if 'history' not in st.session_state:
    st.session_state.history = []
if 'form_data' not in st.session_state:
    st.session_state.form_data = {}
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "metrics_history" not in st.session_state:
   
    days = 30
    dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    st.session_state.metrics_history = pd.DataFrame({
        "date": dates,
        "blood_pressure_systolic": np.random.randint(110, 140, size=days),
        "blood_pressure_diastolic": np.random.randint(70, 90, size=days),
        "weight": np.random.normal(75, 2, days),
        "symptom_severity": np.random.randint(1, 5, size=days)
    })

client = OpenAI(api_key="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")

def predict_base_recommendation(age, disease, strength, duration):
    try:
        age_int = int(age)
    except ValueError:
        return "Invalid age provided."

    if age_int < 18:
        return "Pediatric consultation recommended."
    elif strength == "Critical":
        return "Immediate medical attention recommended."
    elif age_int < 40 and strength in ["Mild", "Moderate"]:
        return "We recommend lifestyle changes and regular monitoring."
    else:
        return "We recommend further evaluation, potential medication management, and lifestyle adjustments."

def generate_treatment_plan(user_data):
    base_recommendation = predict_base_recommendation(
        user_data["age"], 
        user_data["disease"],
        user_data["strength_of_symptoms"],
        user_data["duration_of_symptoms"]
    )

    prompt = f"""
    As a medical information assistant, provide a customized health plan based on the following information:

    PATIENT PROFILE:
    - Age: {user_data["age"]}
    - Gender: {user_data["gender"]}
    - Disease/Condition: {user_data["disease"]}
    - Symptoms: {user_data["symptoms"]}
    - Symptom Severity: {user_data["strength_of_symptoms"]}
    - Symptom Duration: {user_data["duration_of_symptoms"]}
    - Medical History: {user_data["medical_history"]}
    - Current Medications: {user_data["current_medications"]}
    - Allergies: {user_data["allergies"]}
    - Lifestyle Factors: {", ".join(user_data["lifestyle_choices"]) if user_data["lifestyle_choices"] else "None specified"}
    - Income Level: {user_data["income_level"]}

    Please organize your response in the following sections:
    1. SUMMARY: Brief overview of the health situation
    2. RECOMMENDED ACTIONS: Immediate steps that might be appropriate
    3. LIFESTYLE RECOMMENDATIONS: Specific to the patient's profile
    4. POTENTIAL TREATMENTS: General information about treatments that might be discussed with healthcare providers
    5. FOLLOW-UP STEPS: Ongoing monitoring and care

    Base medical recommendation to incorporate: {base_recommendation}

    IMPORTANT: Include a prominent disclaimer that this is NOT professional medical advice and should not replace consultation with healthcare providers.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a health information assistant providing general health guidance. Additionally, give the user a recommeded treatment plan. You do not diagnose or prescribe. Always emphasize the importance of consulting with healthcare professionals. "},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating treatment plan: {str(e)}")
        return "Unable to generate treatment plan at this time. Please try again later."

def save_to_history(user_data, recommendation):
    st.session_state.history.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "age": user_data["age"],
        "disease": user_data["disease"],
        "recommendation": recommendation
    })

def display_recommendation(recommendation):
    st.subheader("Your Customized Health Plan")
    st.markdown(recommendation)

    st.download_button(
        label="Download as Text",
        data=recommendation,
        file_name="health_plan.txt",
        mime="text/plain"
    )

def show_health_metrics_graph():
    """Function to display health metrics visualization"""
    st.subheader("Health Metrics Visualization")

    
    metric_to_view = st.selectbox(
        "Select metric to visualize",
        ["Blood Pressure", "Weight", "Symptom Severity"]
    )

    df = st.session_state.metrics_history

    if metric_to_view == "Blood Pressure":
        
        bp_chart = alt.Chart(df).transform_fold(
            ['blood_pressure_systolic', 'blood_pressure_diastolic'],
            as_=['Measurement', 'Value']
        ).mark_line(point=True).encode(
            x='date:T',
            y='Value:Q',
            color='Measurement:N',
            tooltip=['date', 'Value', 'Measurement']
        ).properties(
            title='Blood Pressure Over Time',
            width=700,
            height=400
        ).interactive()

        st.altair_chart(bp_chart)

        
        st.markdown("""
        ### Understanding Blood Pressure Readings
        - **Systolic (upper number)**: Pressure when heart beats
        - **Diastolic (lower number)**: Pressure between beats

        **Healthy Range:**
        - Normal: Below 120/80 mm Hg
        - Elevated: 120-129/below 80 mm Hg
        - Stage 1 Hypertension: 130-139/80-89 mm Hg
        - Stage 2 Hypertension: 140+/90+ mm Hg
        """)

    elif metric_to_view == "Weight":
        # Create a line chart for weight
        weight_chart = alt.Chart(df).mark_line(point=True).encode(
            x='date:T',
            y=alt.Y('weight:Q', scale=alt.Scale(zero=False)),
            tooltip=['date', 'weight']
        ).properties(
            title='Weight Tracking',
            width=700,
            height=400
        ).interactive()

        st.altair_chart(weight_chart)

        
        if "form_data" in st.session_state and "age" in st.session_state.form_data:
            st.markdown(f"""
            ### Weight Context
            Regular weight tracking can help monitor health status and treatment effectiveness.
            Small fluctuations are normal, but consistent trends may be significant.
            """)

    elif metric_to_view == "Symptom Severity":
        
        severity_chart = alt.Chart(df).mark_bar().encode(
            x='date:T',
            y='symptom_severity:Q',
            color=alt.Color('symptom_severity:Q', scale=alt.Scale(scheme='reds')),
            tooltip=['date', 'symptom_severity']
        ).properties(
            title='Symptom Severity Tracking (1-5 scale)',
            width=700,
            height=400
        ).interactive()

        st.altair_chart(severity_chart)

        # Add severity scale explanation
        st.markdown("""
        ### Symptom Severity Scale
        1. **Minimal**: Barely noticeable, no impact on daily activities
        2. **Mild**: Noticeable but manageable, minimal impact
        3. **Moderate**: Clearly noticeable, moderate impact on activities
        4. **Severe**: Significant impact on daily activities and quality of life
        5. **Extreme**: Unable to perform normal activities, may require immediate attention
        """)

def show_treatment_comparison():
    """Function to display treatment comparison visualization"""
    st.subheader("Treatment Effectiveness Comparison")

    # Get disease from form data if available
    selected_disease = "General Condition"
    if "form_data" in st.session_state and "disease" in st.session_state.form_data:
        if st.session_state.form_data["disease"] != "None" and st.session_state.form_data["disease"] != "Other":
            selected_disease = st.session_state.form_data["disease"]
        elif st.session_state.form_data["disease"] == "Other" and "other_disease" in st.session_state.form_data:
            selected_disease = st.session_state.form_data["other_disease"]

    st.markdown(f"### Comparative Analysis for: {selected_disease}")

    # Sample treatment data based on selected disease
    treatment_data = {
        "Diabetes": {
            'treatments': ['Medication Only', 'Diet Changes Only', 'Exercise Only', 'Combined Approach', 'No Treatment'],
            'effectiveness': [65, 35, 30, 85, 0],
            'side_effects': [25, 0, 5, 15, 35],
            'adherence_difficulty': [30, 40, 45, 60, 0],
            'cost': [70, 20, 10, 80, 0]
        },
        "Hypertension": {
            'treatments': ['Medication Only', 'Diet Changes Only', 'Exercise Only', 'Combined Approach', 'No Treatment'],
            'effectiveness': [70, 30, 35, 90, 0],
            'side_effects': [30, 0, 0, 20, 40],
            'adherence_difficulty': [20, 50, 40, 55, 0],
            'cost': [60, 30, 15, 75, 0]
        },
        "Heart Disease": {
            'treatments': ['Medication Only', 'Lifestyle Changes Only', 'Surgery', 'Combined Approach', 'No Treatment'],
            'effectiveness': [60, 40, 85, 90, 0],
            'side_effects': [35, 5, 60, 40, 65],
            'adherence_difficulty': [25, 45, 10, 50, 0],
            'cost': [65, 25, 95, 85, 0]
        },
        "General Condition": {
            'treatments': ['Medication Only', 'Lifestyle Changes Only', 'Combined Approach', 'No Treatment'],
            'effectiveness': [60, 40, 80, 5],
            'side_effects': [30, 5, 20, 45],
            'adherence_difficulty': [30, 45, 55, 0],
            'cost': [75, 25, 80, 0]
        }
    }

    
    if selected_disease not in treatment_data:
        selected_disease = "General Condition"

    
    data = treatment_data[selected_disease]

    
    comparison_df = pd.DataFrame({
        'Treatment': data['treatments'],
        'Effectiveness (%)': data['effectiveness'],
        'Side Effects (%)': data['side_effects'],
        'Adherence Difficulty': data.get('adherence_difficulty', [0] * len(data['treatments'])),
        'Relative Cost': data['cost']
    })

    # Let user select what metrics to compare
    metrics = st.multiselect(
        "Select metrics to compare",
        ['Effectiveness (%)', 'Side Effects (%)', 'Adherence Difficulty', 'Relative Cost'],
        default=['Effectiveness (%)', 'Side Effects (%)']
    )

    if metrics:
        
        chart_data = comparison_df.melt(
            id_vars=['Treatment'], 
            value_vars=metrics,
            var_name='Metric', 
            value_name='Value'
        )

        
        sorted_treatments = comparison_df.sort_values('Effectiveness (%)', ascending=False)['Treatment'].tolist()

        comparison_chart = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('Treatment:N', sort=sorted_treatments),
            y='Value:Q',
            color='Metric:N',
            column='Metric:N'
        ).properties(
            width=150,
            height=300
        ).interactive()

        st.altair_chart(comparison_chart)

        st.markdown("""
        ### Understanding the Metrics
        - **Effectiveness**: Higher values indicate better outcomes
        - **Side Effects**: Lower values are better (fewer side effects)
        - **Adherence Difficulty**: Lower values are better (easier to follow)
        - **Relative Cost**: Lower values indicate more affordable options

        *Note: These values are estimates based on general medical literature and may vary for individual cases.*
        """)

def show_symptom_progress():
    """Function to display symptom progression chart"""
    st.subheader("Projected Symptom Progress")

    # Get condition details if available
    condition = "General Condition"
    severity = "Moderate"
    if "form_data" in st.session_state:
        if "disease" in st.session_state.form_data and st.session_state.form_data["disease"] != "None":
            condition = st.session_state.form_data["disease"]
        if "strength_of_symptoms" in st.session_state.form_data:
            severity = st.session_state.form_data["strength_of_symptoms"]

    # Generate time points (weeks)
    weeks = list(range(0, 13))

    # Adjust baseline severity based on input
    baseline_severity = {
        "Mild": 3,
        "Moderate": 5,
        "Severe": 8,
        "Critical": 10
    }.get(severity, 5)

    # Generate symptom trajectory
    if condition == "None" or baseline_severity < 3:
        # Minimal symptoms, mostly flat line
        base_trajectory = [max(baseline_severity - 0.1 * week, 1) + np.random.normal(0, 0.3) for week in weeks]
    else:
        # More significant symptoms with improvement over time
        base_trajectory = [max(baseline_severity - 0.4 * week, 1) + np.random.normal(0, 0.5) for week in weeks]

    # Create DataFrame
    progress_df = pd.DataFrame({
        'Week': weeks,
        'Symptom Severity': [max(round(val, 1), 0) for val in base_trajectory],
        'Expected Range': ['Severe' if val > 7 else 'Moderate' if val > 4 else 'Mild' for val in base_trajectory]
    })

    
    base = alt.Chart(progress_df).encode(x='Week:Q')

    
    line = base.mark_line(color='blue').encode(
        y=alt.Y('Symptom Severity:Q', scale=alt.Scale(domain=[0, 10])),
        tooltip=['Week', 'Symptom Severity', 'Expected Range']
    )

    
    points = base.mark_point(size=100, color='blue').encode(
        y='Symptom Severity:Q'
    )

    
    chart = (line + points).properties(
        title=f'Expected {condition} Symptom Progression Over 12 Weeks',
        width=700,
        height=400
    ).interactive()

    st.altair_chart(chart)

    st.write("This graph shows the expected progression of symptoms over time with proper treatment and lifestyle adjustments. Individual results may vary significantly.")

    # Add contextual information
    st.markdown("""
    ### Factors Affecting Recovery Timeline:
    - **Treatment Adherence**: Following medical recommendations consistently
    - **Lifestyle Changes**: Implementing and maintaining recommended adjustments
    - **Condition Severity**: More severe initial conditions may take longer to improve
    - **Individual Factors**: Age, overall health, and comorbidities affect recovery rates
    """)

st.set_page_config(page_title="MyHealthPal", page_icon="🏥", layout="wide")

# Update the navigation to include the new page "More Detailed Results"
page = st.sidebar.radio("Navigation", 
    ["Home", "New Health Plan", "History", "More Detailed Results", "How to use it"], 
    index=["Home", "New Health Plan", "History", "More Detailed Results", "How to use it"].index(st.session_state.page) 
          if st.session_state.page in ["Home", "New Health Plan", "History", "More Detailed Results", "How to use it"] 
          else 0)
st.session_state.page = page

if page == "New Health Plan":
    st.title("Customized Health Plan Assistant")
    st.write("This tool provides general health information based on your inputs. **This is NOT professional medical advice.**")

    col1, col2 = st.columns(2)

    with col1:
        age = st.text_input("Age", st.session_state.form_data.get("age", ""), help="Enter your age in years")

        disease = st.selectbox(
            "Primary Health Concern", 
            ["None", "Diabetes", "Hypertension", "Heart Disease", "Stroke", "Alzheimer's", "Liver Disease", "Anxiety/Depression", "Other"],
            index=0 if "disease" not in st.session_state.form_data else 
                  ["None", "Diabetes", "Hypertension", "Heart Disease", "Stroke", "Alzheimer's", "Liver Disease", "Anxiety/Depression", "Other"].index(st.session_state.form_data["disease"])
        )

        if disease == "Other":
            other_disease = st.text_input("Please specify your health concern", st.session_state.form_data.get("other_disease", ""))

        symptoms = st.text_area("Describe your symptoms", st.session_state.form_data.get("symptoms", ""))
        strength_of_symptoms = st.select_slider(
            "Symptom Severity", 
            options=["Mild", "Moderate", "Severe", "Critical"],
            value=st.session_state.form_data.get("strength_of_symptoms", "Moderate")
        )

        duration_of_symptoms = st.select_slider(
            "Duration of Symptoms", 
            options=["Acute (0-3 days)", "Subacute (4-14 days)", "Chronic (15+ days)", "Recurrent (Comes and goes)"],
                value=st.session_state.form_data.get("duration_of_symptoms", "Acute (0-3 days)")
        )
        weight = st.text_input("Weight (lb)", st.session_state.form_data.get("weight", ""))
        blood_pressure = st.text_input("Blood Pressure (e.g., 120/80 mmHg)", st.session_state.form_data.get("blood_pressure", ""))
    with col2:
        gender = st.selectbox(
            "Gender", 
            ["Male", "Female", "Other", "Prefer not to say"],
            index=0 if "gender" not in st.session_state.form_data else 
                  ["Male", "Female", "Other", "Prefer not to say"].index(st.session_state.form_data["gender"])
        )

        medical_history = st.text_area("Medical history (optional)", st.session_state.form_data.get("medical_history", ""))
        current_medications = st.text_area("Current medications (optional)", st.session_state.form_data.get("current_medications", ""))
        allergies = st.text_area("Allergies (optional)", st.session_state.form_data.get("allergies", ""))

        lifestyle_choices = st.multiselect(
            "Current lifestyle factors (select all that apply)",
            ["Sedentary", "High Sugar Intake", "Smoker", "Alcohol Use", "Stressful Job", "Poor Sleep", "Adequate Hydration", "Regular Exercise", "Balanced Diet", "Social Engagement", "Other"],
            default=st.session_state.form_data.get("lifestyle_choices", [] )
        )

        income_level = st.selectbox(
            "Income Level", 
            ["Prefer not to say", "< $30,000", "$30,001-$58,020", "$58,021-$100,000", "$100,000-$153,000", "> $153,000"],
            index=0 if "income_level" not in st.session_state.form_data else 
                  ["Prefer not to say", "< $30,000", "$30,001-$58,020", "$58,021-$100,000", "$100,000-$153,000", "> $153,000"].index(st.session_state.form_data["income_level"])
        )

    if st.button("Generate Health Plan"):
        if not age or not age.isdigit():
            st.error("Please enter a valid age (numeric value).")
        else:
            st.session_state.form_data = {
                "age": age,
                "disease": disease,
                "other_disease": other_disease if disease == "Other" else "",
                "symptoms": symptoms,
                "strength_of_symptoms": strength_of_symptoms,
                "duration_of_symptoms": duration_of_symptoms,
                "gender": gender,
                "medical_history": medical_history,
                "current_medications": current_medications,
                "allergies": allergies,
                "lifestyle_choices": lifestyle_choices,
                "income_level": income_level
            }

            with st.spinner("Generating your personalized health plan..."):
                time.sleep(1)
                recommendation = generate_treatment_plan(st.session_state.form_data)
                save_to_history(st.session_state.form_data, recommendation)
                display_recommendation(recommendation)

                st.success("For more detailed visualizations and analysis, visit the 'More Detailed Results' page.")

    st.markdown("---")
    st.markdown("""
    **IMPORTANT DISCLAIMER**: This tool provides general health information but is not a substitute for professional medical advice. Always seek the advice of your physician or other qualified health provider with any questions you may have 
    regarding a medical condition.
    """)

elif page == "History":
    st.title("Your Health Plan History")

    if not st.session_state.history:
        st.info("No health plans generated yet. Create a new health plan to see your history.")
        st.info("**IMPORTANT!** If you refresh this page, any current history will be **LOST!**")
    else:
        st.info("**IMPORTANT!** If you refresh this page, any current history will be **LOST!**")
        history_df = pd.DataFrame(st.session_state.history)
        st.dataframe(history_df[["timestamp", "age", "disease"]])

        if st.session_state.history:
            selected_timestamp = st.selectbox(
                "Select a health plan to view",
                options=[entry["timestamp"] for entry in st.session_state.history]
            )

            selected_plan = next((entry for entry in st.session_state.history if entry["timestamp"] == selected_timestamp), None)

            if selected_plan:
                st.subheader(f"Health Plan from {selected_timestamp}")
                st.markdown(selected_plan["recommendation"])

                st.download_button(
                    label="Download This Plan",
                    data=selected_plan["recommendation"],
                    file_name=f"health_plan_{selected_timestamp.replace(' ', '_').replace(':', '-')}.txt",
                    mime="text/plain"
                )

                st.info("For visualizations and detailed analysis, visit the 'More Detailed Results' page.")

elif page == "More Detailed Results":
    st.title("Detailed Health Analytics")

    if not st.session_state.form_data:
        st.warning("Please create a health plan first to see detailed results.")
        if st.button("Go to Health Plan Creator"):
            st.session_state.page = "New Health Plan"
            st.rerun()
    else:
        # Create tabs for different visualizations
        tab1, tab2, tab3 = st.tabs(["Health Metrics", "Treatment Comparison", "Symptom Progression"])

        with tab1:
            show_health_metrics_graph()

        with tab2:
            show_treatment_comparison()

        with tab3:
            show_symptom_progress()

        st.markdown("---")
        st.markdown("""
        **DISCLAIMER**: These visualizations provide general information based on population-level data and should not be used for 
        diagnosis or treatment decisions. Individual results may vary significantly. Always consult with healthcare professionals for 
        personalized medical advice.
        """)

elif page == "Home":
    st.markdown(
        """
        <style>
        .hero {
            text-align: center;
            padding: 50px 0;
            background-color: #f5f5f5;
            margin-bottom: 20px;
        }
        .hero h1 {
            font-size: 3em;
            font-weight: bold;
            margin: 0;
        }
        .hero p {
            font-size: 1.5em;
            margin-top: 10px;
        }
        .btn {  
            font-family: Arial, Helvetica, sans-serif;  
            text-transform: uppercase;
        }
        .btn:hover .btn-slide-show-text1 {  
            margin-left: 65px;
        }
        .btn-rect-to-round {  
            height: 55px;  
            width: 200px;  
            font-size: 16px;  
            font-weight: 600;  
            background: transparent;  
            cursor: pointer;  
            transition: 0.5s ease-in;
        }
        .btn-rect-to-round:hover {  
            border-radius: 60px;  
            color: rgb(255, 255, 255) !important;
        }
        .btn-rect-to-round--red {  
            border: 2px solid rgb(239, 35, 60);  
            color: rgb(239, 35, 60) !important;
        }
        .btn-rect-to-round--red:hover {  
            border-color: rgb(239, 35, 60);  
            background: rgb(239, 35, 60);
        }
        .btn-rect-to-round--orange {  
            border: 2px solid rgb(254, 174, 0);  
            color: rgb(254, 174, 0) !important;
        }
        .btn-rect-to-round--orange:hover {  
            border-color: rgb(254, 174, 0);  
            background: rgb(254, 174, 0);
        }
        /* Flex container for buttons */
        .button-container {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 40px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="hero">
            <h1>MyHealthPal</h1>
            <p>Tailored Insights for a Healthier You</p>
        </div>
        <div class="button-container">
            <button class="btn btn-rect-to-round btn-rect-to-round--red" 
                    onclick="window.location.href='?page=New%20Health%20Plan';">
                Try It Out
            </button>
            <button class="btn btn-rect-to-round btn-rect-to-round--orange" 
                    onclick="window.location.href='?page=How%20to%20Use%20It';">
                How to use it
            </button>
        </div>
        """,
        unsafe_allow_html=True
    )

    try:
        st.image("home_image1.jpg", use_container_width=True)
    except:
        st.warning("Home image not found. Please ensure 'home_image.jpg' is in the same directory as your script.")

elif page == "How to use it":
    st.title("How to Use It")
    st.markdown("""
    ### Welcome to MyHealthPal!
    
    This tool provides you with a customized health plan based on the information you provide.
    
    **Steps to use the tool:**
    1. **New Health Plan:** Fill in your details such as age, health concerns, symptoms, and more. Click on "Generate Health Plan" to receive a personalized plan.
    2. **History:** View your previous health plans. Note that refreshing the page will clear the history.
    3. **More Detailed Results:** Explore enhanced visualizations and analyses of your health data once a plan is generated.
    
    *Remember: This tool offers general health information and is not a substitute for professional medical advice.*
    """)
    try:
        st.image("guide_image.jpg", use_container_width=True)
    except:
        st.warning("Home image not found. Please ensure 'home_image.jpg' is in the same directory as your script.")
