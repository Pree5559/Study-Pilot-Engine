import streamlit as st
import json, os, tempfile
from extract import extract_text_from_pdf, extract_syllabus
from planner import allocate_hours, generate_weekly_plan, clean_json_response as clean_plan_json
from pdf_export import generate_pdf, load_timetable
from remainder import send_daily_nudge

st.set_page_config(page_title="StudyPilot", page_icon=":books:", layout="wide")
st.title("StudyPilot - Your AI Study Companion")
st.caption("stop guessing what to study, ask your agent instead")

st.header("Upload your syllabus PDF")
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
email = st.text_input("Enter your email for daily reminders (optional)")
hours = st.slider("How many hours per day can you study?", min_value=1, max_value=12, value=4)

def clean_syllabus_json(raw):
    """Extract JSON array from AI response (syllabus data uses [])."""
    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("No JSON array found in response")
    return raw[start:end + 1]

if st.button("Generate Study Plan"):
    if uploaded_file is not None:
        with st.spinner("Extracting syllabus from PDF..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                temp_pdf.write(uploaded_file.read())
                temp_pdf_path = temp_pdf.name

            text = extract_text_from_pdf(temp_pdf_path)
            raw_output = extract_syllabus(text)
            cleaned = clean_syllabus_json(raw_output)

        with st.spinner("Building your 7 day plan..."):
            subjects = json.loads(cleaned)
            allocated = allocate_hours(subjects, hours)
            raw_plan = generate_weekly_plan(allocated, hours)
            cleaned_plan = clean_plan_json(raw_plan)

            # Handle possible markdown wrapping in timetable response
            if "```" in cleaned_plan:
                cleaned_plan = cleaned_plan.split("```")[1].strip()
                if cleaned_plan.startswith("json"):
                    cleaned_plan = cleaned_plan[4:].strip()

            timetable_data = json.loads(cleaned_plan)

            with open("timetable.json", "w") as f:
                json.dump(timetable_data, f, indent=2)

        st.subheader("Your Weekly Study Timetable")
        for day in timetable_data["timetable"]:
            st.subheader(f"Day {day['day']} - {day['date']}")
            for slot in day["slots"]:
                chapters = ", ".join(slot["chapters_to_cover"])
                st.write(f"**{slot['duration_minutes']} min | {slot['subject']}**")
                st.write(f"Chapters: {chapters}")
                if slot.get("notes"):
                    st.write(f"Note: {slot['notes']}")
            st.write(f"Total Study Minutes: {day['total_study_minutes']}")
            st.divider()

        with st.spinner("Generating PDF..."):
            rows, summary = load_timetable("timetable.json")
            generate_pdf(rows, summary, output_path="study_timetable.pdf")

        st.success("Plan completed!")

        with open("study_timetable.pdf", "rb") as f:
            st.download_button(
                label="Download Timetable as PDF",
                data=f,
                file_name="study_timetable.pdf",
                mime="application/pdf"
            )

        if email:
            try:
                send_daily_nudge(email, timetable_data)
                st.success(f"Daily reminders will be sent to {email}.")
            except Exception as e:
                st.error(f"Failed to send daily reminders: {e}")

    else:
        st.error("Please upload a syllabus PDF file.")