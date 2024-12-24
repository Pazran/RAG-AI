import requests
import json

url_generate_sse = "http://localhost:5001/api/extra/generate/stream"

headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}

def generate_sse(prompt: str, temp: float = 0.7, top_p: float = 0.9):
    try:
        response = requests.post(
            url=url_generate_sse,
            headers=headers,
            json={
                "prompt": prompt,
                "temperature": temp,
                "top_p": top_p
            },
            stream=True,
            timeout=60  # Adjust timeout if necessary
        )
        response.raise_for_status()  # Will raise HTTPError if status is not 2xx
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def process_stream(response):
    try:
        for line in response.iter_lines():  # Process each line from the stream
            if line:
                try:
                    line_str = line.decode('utf-8')  # Decode line from bytes to string
                    if line_str.startswith("data:"):
                        event_data = line_str[len("data:"):].strip()
                        if event_data:
                            data = json.loads(event_data)  # Parse the JSON data
                            token = data.get("token", "")
                            if token:
                                yield token  # Yield token instead of printing
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
                except Exception as e:
                    print(f"Error processing line: {e}")
    except Exception as e:
        print(f"Error in processing stream: {e}")

# Get user input and start generating the SSE stream
user_input = input(">>> ")
print()

response = generate_sse(user_input)

if response:
    try:
        for token in process_stream(response):
            print(token, end='', flush=True)  # Print token without a newline
    except Exception as e:
        print(f"Error in streaming: {e}")
else:
    print("Failed to start streaming.")
