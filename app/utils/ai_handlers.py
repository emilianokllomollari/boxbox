import google.generativeai as genai
from openai import OpenAI


gemini_api = "AIzaSyCzQC_uvxEEDbFRhYDcdpURTQtcpFU2NGY"
gpt_key='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'
# Configure your OpenAI key
client = OpenAI(api_key=gpt_key)

# Gemini api call
def gemini_answer(prompt):
    genai.configure(api_key=gemini_api)
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    print(response.text)
    return response.text

# GPT 3.5-Turbo api call
def ask_gpt(prompt):
    try:
        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        print(chat_completion.choices[0].message.content.strip())
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error: {e}")
        return "I'm sorry, I can't complete that task right now."