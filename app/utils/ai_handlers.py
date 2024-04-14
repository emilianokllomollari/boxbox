import google.generativeai as genai
from openai import OpenAI


gemini_api = "AIzaSyCzQC_uvxEEDbFRhYDcdpURTQtcpFU2NGY"
gemini_history = []
gpt_key='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'
gpt_history = []
gpt4_history = []

# Configure your OpenAI key
client = OpenAI(api_key=gpt_key)

def transform_history_for_gemini(history):
    # Transform the conversation history into the expected format
    transformed_history = {
        "parts": [
            {"text": message["content"]} for message in history
        ]
    }
    return transformed_history

# Gemini api call
def gemini_answer(prompt):
    if len(gemini_history) > 3:
        gemini_history.pop(0)
    gemini_history.append({"role": "user", "content": prompt})
    genai.configure(api_key=gemini_api)
    model = genai.GenerativeModel('gemini-pro')
    
    formatted_history = transform_history_for_gemini(gemini_history)
    response = model.generate_content(formatted_history)
    
    gemini_response = response.text
    print(gemini_response)
    gemini_history.append({"role": "system", "content": gemini_response})
    return gemini_response

# GPT 3.5-Turbo api call
def ask_gpt(prompt):
    if len(gpt_history)>3:
        gpt_history.pop(0)
    
    gpt_history.append({"role": "user", "content": prompt})
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages= gpt_history
        )
    except Exception as e:
        print(f"Error: {e}")
        return "I'm sorry, I can't complete that task right now."
    
    gpt_response = response.choices[0].message.content.strip()
    print(gpt_response)
    gpt_history.append({"role": "system", "content": gpt_response})
    return gpt_response