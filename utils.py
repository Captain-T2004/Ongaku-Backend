from google import genai
from config import GEMINI_API_KEY

def call_gemini_streaming(prompt):
    """Call Gemini with streaming to avoid timeout"""
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        response_text = ""
        
        for chunk in client.models.generate_content_stream(
            model='gemini-2.0-flash-exp',
            contents=prompt,
            config={
                'temperature': 0.7,
                'max_output_tokens': 12000,
                'top_p': 0.95,
                'top_k': 40
            }
        ):
            if chunk.text:
                response_text += chunk.text
        
        return response_text
        
    except Exception as e:
        raise Exception(f"Gemini API error: {str(e)}")