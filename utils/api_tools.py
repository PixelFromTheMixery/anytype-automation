from utils.logger import logger

import os, requests, time
from dotenv import load_dotenv

load_dotenv()

def make_call_with_retry(
    category: str,
    url: str,
    info: str,
    data: dict | None = None,
    retries: int=3,
    delay: int=2,
):
    headers = {
        "Authorization": f'Bearer {os.getenv("API_KEY")}',
        "Content-Type": "application/json",
        "Anytype-Version": "2025-05-20",
    }

    for attempt in range(1, retries + 1):
        result = None
        try:
            logger.info(f"Attempt to {info}. {attempt} of {retries}")
            
            match category:
                case "get":
                    response = requests.get(url, headers=headers)
                case "patch":
                    response = requests.patch(url, headers=headers, json=data)
                case "post":
                    response = requests.post(url, headers=headers, json=data)
                case "put":
                    response = requests.put(url, headers=headers, json=data)
                case _:
                    raise ValueError(f"Unknown category: {category}")

            result = response.json()
            response.raise_for_status()
            
            if "results" in result:
                return result["results"]
            else:
                return result

        except requests.exceptions.RequestException as e:
            if result and "status" in result and result["status"] == 429:
                if attempt < retries:
                    time.sleep(delay)
            else:
                print(f"RequestException on attempt {attempt}: {e}")
                if result and "message" in result:
                    print(f'json response: {result["message"]}')
        except ValueError as e:
            print(f"ValueError: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
