import google.generativeai as genai
import os

api_key = "Use Your API KEY"
genai.configure(api_key=api_key)

try:
    print("Listing models...")
    models = genai.list_models()
    for m in models:
        print(f"Model: {m.name}")
    
    print("\nTesting generation with gemini-pro...")
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Hello")
    print(f"Response: {response.text}")

except Exception as e:
    print(f"Total error: {str(e)}")
