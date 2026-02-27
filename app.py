import streamlit as st
import json
import google.generativeai as genai

# -------------------------------
# CONFIG
# -------------------------------
genai.configure(api_key="AIzaSyDLzHTK0N74kbHwHSYOoOQOJwZNiecDKYI")  # <-- replace properly later

model = genai.GenerativeModel("gemini-2.5-flash")

# -------------------------------
# SESSION STATE
# -------------------------------
if "generated" not in st.session_state:
    st.session_state.generated = False

# -------------------------------
# FUNCTIONS
# -------------------------------
def calculate_bmi(weight, height):
    return weight / ((height / 100) ** 2)


def classify_goal(goal, bmi):
    if goal == "Auto":
        if bmi < 18.5:
            return "Muscle Gain"
        elif bmi > 25:
            return "Fat Loss"
        else:
            return "Maintenance"
    return goal


def generate_prompt(user_data):
    return f"""
You are a certified fitness trainer.

STRICT RULES:
- Return ONLY valid JSON
- No markdown
- No explanation
- Output must start with {{ and end with }}

Output format:
{{
  "goal": "",
  "target_muscle": "",
  "workout_plan": [
    {{
      "exercise": "",
      "sets": "",
      "reps": "",
      "rest": ""
    }}
  ],
  "notes": ""
}}

User Details:
Age: {user_data['age']}
Height: {user_data['height']}
Weight: {user_data['weight']}
BMI: {user_data['bmi']:.2f}
Goal: {user_data['goal']}
Muscle: {user_data['muscle']}
Experience: {user_data['experience']}
Diet: {user_data['diet']}
Injuries: {user_data['injuries']}
Equipment: {user_data['equipment']}
Duration: {user_data['duration']}
"""


def call_gemini(prompt):
    try:
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.3}
        )
        return response.text
    except Exception as e:
        return f"ERROR: {str(e)}"


def parse_output(output):
    try:
        output = output.replace("```json", "").replace("```", "")
        start = output.find("{")
        end = output.rfind("}") + 1
        return json.loads(output[start:end])
    except:
        return None


def fallback_plan(goal, muscle):
    return {
        "goal": goal,
        "target_muscle": muscle,
        "workout_plan": [
            {"exercise": "Jump Rope", "sets": 3, "reps": "1 min", "rest": "30 sec"},
            {"exercise": "Bodyweight Squats", "sets": 3, "reps": "15", "rest": "45 sec"}
        ],
        "notes": "Fallback plan (AI unavailable)"
    }

# -------------------------------
# UI SETUP
# -------------------------------
st.set_page_config(layout="wide")
st.title("🏋️ AI Gym Trainer")

left, spacer, right = st.columns([1, 0.3, 2])

# -------------------------------
# LEFT COLUMN (INPUTS)
# -------------------------------
with left:
    st.header("User Inputs")

    age = st.number_input("Age", 10, 80)
    height = st.number_input("Height (cm)", 100, 220)
    weight = st.number_input("Weight (kg)", 30, 150)

    goal = st.selectbox("Goal", ["Auto", "Fat Loss", "Muscle Gain", "Maintenance"])
    muscle = st.selectbox("Target Muscle", ["Chest", "Back", "Legs", "Shoulders", "Arms", "Full Body"])

    experience = st.selectbox("Experience", ["Beginner", "Intermediate", "Advanced"])
    diet = st.selectbox("Diet", ["Vegetarian", "Non-Vegetarian", "Vegan"])

    injuries = st.text_input("Injuries", "None")
    equipment = st.selectbox("Equipment", ["Full Gym", "Dumbbells Only", "Bodyweight Only"])
    duration = st.slider("Duration (minutes)", 20, 120, 60)

    if st.button("Generate Workout Plan"):
        st.session_state.generated = True

# -------------------------------
# RIGHT COLUMN (OUTPUT)
# -------------------------------
with right:
    st.header("Workout Plan")

    if st.session_state.generated:

        # Scroll to top
        st.markdown("""
        <script>
        window.scrollTo(0, 0);
        </script>
        """, unsafe_allow_html=True)

        bmi = calculate_bmi(weight, height)
        final_goal = classify_goal(goal, bmi)

        st.subheader(f"📊 BMI: {bmi:.2f}")
        st.subheader(f"🎯 Goal: {final_goal}")

        user_data = {
            "age": age,
            "height": height,
            "weight": weight,
            "bmi": bmi,
            "goal": final_goal,
            "muscle": muscle,
            "experience": experience,
            "diet": diet,
            "injuries": injuries,
            "equipment": equipment,
            "duration": duration
        }

        prompt = generate_prompt(user_data)

        with st.spinner("Generating your workout..."):
            output = call_gemini(prompt)

        # Debug section
        with st.expander("🔍 Raw AI Output"):
            st.code(output)

        if "ERROR" in output:
            st.error(output)
        else:
            plan = parse_output(output)

            if not plan:
                st.warning("Invalid AI response. Using fallback.")
                plan = fallback_plan(final_goal, muscle)

            for ex in plan["workout_plan"]:
                st.markdown(f"""
**{ex['exercise']}**
- Sets: {ex['sets']}
- Reps: {ex['reps']}
- Rest: {ex['rest']}
""")

            st.subheader("📝 Notes")
            st.write(plan["notes"])