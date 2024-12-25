import argparse
import asyncio
import aiohttp
import logging
import json
import time
from urllib.parse import urlparse

# Argument parser setup
parser = argparse.ArgumentParser(description="SSE Client Application")
parser.add_argument("--url", type=str, default="http://172.20.10.6:5001/api/extra/generate/stream",
                    help="Server URL for the SSE endpoint")
parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
parser.add_argument("--timeout", type=int, default=60, help="Request timeout in seconds")
parser.add_argument("--check-version", action="store_true", help="Check and print API version")
parser.add_argument("--check-model", action="store_true", help="Check and print LLM model")
args = parser.parse_args()

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

# Adjust logging level based on verbosity flag
if args.verbose:
    logger.setLevel(logging.DEBUG)

# Server configuration
headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}

# Function to fetch version or model information
async def fetch_info(url: str, endpoint: str):
    """
    Fetches information from the specified endpoint.
    """
    full_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}{endpoint}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(full_url) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    logger.error("Failed to fetch info from %s: %s - %s", full_url, response.status, response.reason)

    except Exception as e:
        logger.error("Error fetching info from %s: %s", full_url, e)
    return None

# Asynchronous function to generate and process SSE with retries
async def generate_sse(url: str, prompt: str, temp: float = 0.7, top_p: float = 0.9, retries: int = 3, delay: float = 2.0):
    """
    Connects to the SSE endpoint and processes the stream for a given prompt with retry logic.
    """
    timeout = aiohttp.ClientTimeout(total=args.timeout)  # Configurable timeout
    attempt = 0
    MAX_DELAY = 10  # Maximum retry delay in seconds

    while attempt < retries:
        delay = min(2 ** attempt, MAX_DELAY)
        attempt += 1
        try:
            logger.info(f"Starting SSE request (Attempt %s/%s).", attempt, retries)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    url=url,
                    headers=headers,
                    json={
                        "prompt": prompt,
                        "temperature": temp,
                        "top_p": top_p
                    }
                ) as response:
                    if response.status != 200:
                        logger.error("Failed to connect: %s - %s", response.status, response.reason)
                        raise aiohttp.ClientResponseError(
                            status=response.status,
                            message=f"Server returned {response.status}"
                        )
                    
                    if not response.content:
                        logger.warning("Received empty content from server.")
                        break

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
            return
        except aiohttp.ClientResponseError as e:
            logger.error("Request failed with status %s: %s", e.status, e.message)
        except aiohttp.ClientError as e:
            logger.error("Request failed: %s", e)
        except Exception as e:
            logger.error("Unexpected error during SSE streaming: %s", e)

        if attempt < retries:
            logger.info("Retrying in %s seconds...", delay)
            await asyncio.sleep(delay)
        else:
            logger.error("All retries failed. Aborting SSE request.")

# Main function for initialization and conditionally checking version or model
async def main():
    """
    Main entry point for the application. Checks version and model if specified.
    """
    if args.check_version or args.check_model:
        base_url = f"{urlparse(args.url).scheme}://{urlparse(args.url).netloc}"
        if args.check_version:
            version_info = await fetch_info(base_url, "/api/v1/info/version")
            if version_info:
                print(f"API Version: {version_info.get('result', 'Unknown')}")
            else:
                print("Failed to fetch API version.")
        
        if args.check_model:
            model_info = await fetch_info(base_url, "/api/v1/model")
            if model_info:
                print(f"LLM Model: {model_info.get('result', 'Unknown')}")
            else:
                print("Failed to fetch LLM model.")
        
        # Exit program after printing version and model information
        return

    # Base URL for prompts
    base_url = f"{urlparse(args.url).scheme}://{urlparse(args.url).netloc}"
    while True:
        try:
            prompt = input(f"Enter prompt for server at {base_url} (or type 'exit' to quit): ")
            if prompt.lower() == "exit":
                logger.info("Exiting application.")
                break
            logger.info("Prompt: \"%s\"", prompt)

            response = []
            start = time.time()
            async for token in generate_sse(args.url, prompt):
                response.append(token)
                print(token, end="", flush=True)
                await asyncio.sleep(0.1)
            
            end = time.time()
            total_time = "{0:.2f}".format(end-start)
            if response:
                output = repr("".join(response))
                print()
                logger.info("Response(%s Seconds): %s", total_time, output)

        except KeyboardInterrupt:
            logger.info("Interrupted by user. Exiting application.")
            break
        except Exception as e:
            logger.error("Error in main loop: %s", e)
        finally:
            logger.info("Application shutdown complete.")

# Run the main loop
if __name__ == "__main__":
    asyncio.run(main())
