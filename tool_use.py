from google import genai
from google.genai import types

client = genai.Client()

# Step 1: Define the actual Python function
def celsius_to_fahrenheit(celsius: float) -> float:
    return (celsius * 9 / 5) + 32

# Step 2: Describe the function to Gemini (this is what it "sees")
tools = [
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="celsius_to_fahrenheit",
            description="Converts a temperature from Celsius to Fahrenheit",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "celsius": types.Schema(type="NUMBER", description="Temperature in Celsius")
                },
                required=["celsius"]
            )
        )
    ])
]

# Step 3: Send a message — Gemini decides it needs the tool
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="What is 100 degrees Celsius in Fahrenheit?",
    config=types.GenerateContentConfig(tools=tools)
)

# Step 4: Gemini responds with a function call (not text yet)
part = response.candidates[0].content.parts[0]
print("Gemini wants to call:", part.function_call.name)
print("With args:", part.function_call.args)

# Step 5: We execute the real function
args = part.function_call.args
result = celsius_to_fahrenheit(**args)
print("Our function returned:", result)

# Step 6: Send the result back so Gemini can answer naturally
response2 = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        types.Content(role="user", parts=[types.Part(text="What is 100 degrees Celsius in Fahrenheit?")]),
        types.Content(role="model", parts=[types.Part(function_call=part.function_call)]),
        types.Content(role="user", parts=[  # tool result goes back as "user"
            types.Part(function_response=types.FunctionResponse(
                name="celsius_to_fahrenheit",
                response={"result": result}
            ))
        ])
    ],
    config=types.GenerateContentConfig(tools=tools)
)

print("\nFinal answer:", response2.text)
