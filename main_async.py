import asyncio
import aiohttp
import logging
import json
import time

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('app.log', mode='a')  # Log to file
    ]
)
logger = logging.getLogger()

# Server configuration
url_generate_sse = "http://localhost:5001/api/extra/generate/stream"
headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}

# Asynchronous function to generate and process SSE with retries
async def generate_sse(prompt: str, temp: float = 0.7, top_p: float = 0.9, retries: int = 3, delay: float = 2.0):
    """
    Connects to the SSE endpoint and processes the stream for a given prompt with retry logic.
    """
    timeout = aiohttp.ClientTimeout(total=None)  # No total timeout
    attempt = 0

    while attempt < retries:
        attempt += 1
        try:
            logger.info(f"Starting SSE request (Attempt {attempt}/{retries}).")
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    url=url_generate_sse,
                    headers=headers,
                    json={
                        "prompt": prompt,
                        "temperature": temp,
                        "top_p": top_p
                    }
                ) as response:
                    if response.status != 200:
                        logger.error(f"Failed to connect: {response.status} - {response.reason}")
                        raise aiohttp.ClientResponseError(
                            status=response.status,
                            message=f"Server returned {response.status}"
                        )

                    logger.info("SSE request successful. Streaming data...")
                    async for line in response.content.iter_any():
                        if line:
                            try:
                                line_str = line.decode('utf-8')
                                if line_str.startswith("data:"):
                                    event_data = line_str[len("data:"):].strip()
                                    if event_data:
                                        logger.debug("Event data: %s", event_data)
                                        data = json.loads(event_data)
                                        token = data.get("token", "")
                                        if token:
                                            yield token
                            except Exception as e:
                                logger.warning("Error processing line: %s", e)
            # If we finish streaming successfully, exit retry loop
            return
        except aiohttp.ClientResponseError as e:
            logger.error(f"Request failed with status {e.status}: {e.message}")
        except aiohttp.ClientError as e:
            logger.error(f"Request failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during SSE streaming: {e}")

        # Wait before retrying
        if attempt < retries:
            logger.info(f"Retrying in {delay} seconds...")
            await asyncio.sleep(delay)
        else:
            logger.error("All retries failed. Aborting SSE request.")

# Main loop for continuous input
async def main():
    """
    Main loop to continuously prompt the user for input and process SSE streams.
    Tokens are aggregated and printed as a complete response.
    """
    while True:
        try:
            prompt = input("Enter prompt (or type 'exit' to quit): ")
            if prompt.lower() == "exit":
                logger.info("Exiting application.")
                break
            logger.info("Prompt: \"%s\"", prompt)

            # Aggregate tokens
            response = []
            start = time.time()
            async for token in generate_sse(prompt):
                response.append(token)
                print(token, end="", flush=True)
                await asyncio.sleep(0.1)
            
            # Print the aggregated response
            #print("".join(response))
            end = time.time()
            output = "".join(response)
            print()
            logger.info("Response(%s Seconds): \"%s\"", "{0:.2f}".format(end-start), output.replace("\n ",""))

        except KeyboardInterrupt:
            logger.info("Interrupted by user. Exiting application.")
            break
        except Exception as e:
            logger.error("Error in main loop: %s", e)

# Run the main loop
if __name__ == "__main__":
    asyncio.run(main())