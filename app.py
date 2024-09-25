import os
import re
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure the Gemini API with the API key
api_key = os.getenv('GOOGLE_API_KEY')
if api_key:
    genai.configure(api_key=api_key)

# Define action regex pattern
action_re = re.compile(r'^Action: (\w+): (.*)$')

# Define functions for actions using the Gemini API
def generate_workout(level):
    response = genai.GenerativeModel("gemini-1.5-flash").generate_content(f"Generate a workout plan for a {level} fitness level.")
    return response.text

def suggest_meal(preference):
    response = genai.GenerativeModel("gemini-1.5-flash").generate_content(f"Suggest a meal plan for a {preference}.")
    return response.text

def motivational_quote():
    response = genai.GenerativeModel("gemini-1.5-flash").generate_content("Give me a motivational quote.")
    return response.text

# Mapping actions to functions
known_actions = {
    "generate_workout": generate_workout,
    "suggest_meal": suggest_meal,
    "motivational_quote": motivational_quote
}

# Chatbot class to handle conversation
class Chatbot:
    def __init__(self, system=""):
        self.system = system
        self.messages = []
        if self.system:
            self.messages.append({"role": "system", "content": system})
    
    def __call__(self, message):
        self.messages.append({"role": "user", "content": message})
        result = self.execute()
        self.messages.append({"role": "assistant", "content": result})
        return result
    
    def execute(self):
        prompt = "\n".join([f'{msg["role"]}: {msg["content"]}' for msg in self.messages])
        model = genai.GenerativeModel('gemini-1.5-flash')
        raw_response = model.generate_content(prompt)
        return raw_response.text

# Query function
def query(question, max_turns=5):
    bot = Chatbot(prompt)
    next_prompt = question
    i = 0
    query_result = ""
    while i < max_turns:
        i += 1
        result = bot(next_prompt)
        query_result += result + "\n\n"
        actions = [action_re.match(a) for a in result.split('\n') if action_re.match(a)]
        if actions:
            # There is an action to run
            action, action_input = actions[0].groups()
            if action not in known_actions:
                raise Exception(f"Unknown action: {action}: {action_input}")
            observation = known_actions[action](action_input)
            query_result += f"Observation: {observation}\n\n"
            next_prompt = f"Observation: {observation}"
        else:
            break
    return query_result

# Prompt for the chatbot
prompt = """
You are a fitness assistant. You help users with workout plans, dietary advice, and motivational quotes.
Your available actions are:
generate_workout:
e.g. generate_workout: Beginner
Generates a workout plan based on the user's fitness level.
suggest_meal:
e.g. suggest_meal: Low-carb breakfast
Suggests a meal plan based on the user's dietary preferences.
motivational_quote:
e.g. motivational_quote:
Returns a motivational quote to inspire the user.
Example session:
Question: Can you help me with a beginner workout plan?
Thought: I should generate a workout plan.
Action: generate_workout: Beginner
Observation: Here is a beginner workout plan: 10 push-ups, 20 squats, 30-second plank.
Answer: I suggest starting with 10 push-ups, 20 squats, and a 30-second plank.
"""

# Streamlit UI
st.sidebar.title("Settings")

# Input for Google API Key in the sidebar
google_api_key = st.sidebar.text_input("Enter your Google API Key:", type="password")

# Store the API key in the environment variable if provided
if google_api_key:
    os.environ['GOOGLE_API_KEY'] = google_api_key
    genai.configure(api_key=google_api_key)  # Reconfigure the API with the new key

# Main app title
st.title("Fitness Assistant")

# Multiple select box for workout level
workout_levels = st.multiselect(
    "Select your fitness level(s):",
    options=["Beginner", "Intermediate", "Advanced"],
    default=["Beginner"]
)

# Multiple select box for dietary preferences
dietary_preferences = st.multiselect(
    "Select dietary preferences:",
    options=["Low-carb", "High-protein", "Vegan", "Keto", "Mediterranean"],
    default=["Low-carb"]
)

user_input = st.text_input("Ask your question:")
if st.button("Submit"):
    if user_input:
        # Constructing a custom query based on the selections
        if "workout" in user_input.lower():
            question = f"Can you help me with a {', '.join(workout_levels)} workout plan?"
        elif "meal" in user_input.lower():
            question = f"Suggest a meal plan for {', '.join(dietary_preferences)} diet."
        else:
            question = user_input
        
        response = query(question)
        st.markdown("### Response:")
        st.markdown(response)
    else:
        st.error("Please enter a question.")
