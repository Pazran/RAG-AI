import logging
import requests
import json

# Basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('app.log', mode='a')  # Log to file
    ]
)

logger = logging.getLogger()

url_generate_sse = "http://localhost:5001/api/extra/generate/stream"

headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}

def generate_sse(prompt: str, temp: float = 0.7, top_p: float = 0.9):
    try:
        logger.info("Starting SSE request.")
        response = requests.post(
            url=url_generate_sse,
            headers=headers,
            json={
                "prompt": prompt,
                "temperature": temp,
                "top_p": top_p
            },
            stream=True,
            timeout=60
        )
        response.raise_for_status()  # Log if response has an error status
        logger.info("SSE request successful. Streaming data...")
        return response
    except requests.exceptions.RequestException as e:
        logger.error("Request failed: %s", e)
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
                                logger.debug("Token received: %s", token)  # Log token
                                yield token
                except json.JSONDecodeError as e:
                    logger.warning("Error decoding JSON: %s", e)
                except Exception as e:
                    logger.error("Error processing line: %s", e)
    except Exception as e:
        logger.critical("Critical error in processing stream: %s", e)

# Main execution
if __name__ == "__main__":
    prompt = input(">>> ")
    logger.info("User input received.")
    logger.debug("Prompt: %s", prompt)
    
    response = generate_sse(prompt)

    if response and response.status_code == 200:
        logger.info("Starting to process the stream.")
        try:
            for token in process_stream(response):
                print(token, end='', flush=True)  # Print tokens without newlines
        except requests.exceptions.RequestException as e:
            logger.error("Request error during streaming: %s", e)
        finally:
            logger.info("Finished processing the stream.")
    else:
        logger.error("Failed to start streaming or invalid response status.")
