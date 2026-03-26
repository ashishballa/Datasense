from google import genai

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="What is 2+2? Answer in one sentence."
)

print(response.text)
