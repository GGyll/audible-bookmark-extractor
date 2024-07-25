import asyncio
import audible_api
from audible_api import AudibleAPI
from constants import artifacts_root_directory

if __name__ == "__main__":
    # authenticate with login
    try:
        credentials = audible_api.audible.Authenticator.from_file(f"{artifacts_root_directory}/secrets/credentials.json")
    except FileNotFoundError:
        credentials = None

    loop = asyncio.get_event_loop()

    audible_obj = AudibleAPI(credentials)
    loop.run_until_complete(audible_obj.welcome())
    loop.run_until_complete(audible_obj.main())
