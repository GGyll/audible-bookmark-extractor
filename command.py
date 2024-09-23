from audible_api import AudibleAPI
from constants import artifacts_root_directory
from readwise import Readwise
from typing import Optional
import audible

help_dict = {
    "authenticate": "Logs in to Audible and stores credentials locally to be re-used",
    "readwise_authenticate": "Logs in to Readwise and stores token locally",
    "readwise_post_highlights": "Posts selected highlights to Readwise",
    "list_books": "Lists the users books",
    "download_books": "Downloads books and saves them locally",
    "convert_audiobook": "Removes Audible DRM from the selected audiobooks and converts them to .mp3 so they can be sliced",
    "get_bookmarks": "WIP, extracts all timestamps for bookmarks in the selected audiobook",
    "transcribe_bookmarks": "Self-explanatory, connects to Speech Recognition API and outputs the result",
    "quit/exit": "Exits this application"
}

AUTHLESS_COMMANDS = ["help", "quit", "exit", "authenticate", "readwise_authenticate"]

class Command:
        
  def __init__(self):
      self.audible_obj: Optional[AudibleAPI] = None
      self.readwise_obj: Optional[Readwise] = None  
  
  def show_help(self):
      for key in help_dict:
        print(f"{key} -- {help_dict[key]}")

  def welcome(self):
    # authenticate with login
    try:
        credentials = audible.Authenticator.from_file(f"{artifacts_root_directory}/secrets/credentials.json")
        self.audible_obj = AudibleAPI(credentials)
    except FileNotFoundError:
        print("\nNo Audible credentials found, please run 'authenticate' to generate them")
        credentials = None

    try:
      with open(f"{artifacts_root_directory}/secrets/readwise_token.json", "r") as file:
        token = file.read()
        self.readwise_obj = Readwise(token)
    except FileNotFoundError:
        print("\nNo Readwise Token found, please run 'readwise_authenticate' to generate them")
        token = None
    
    print("Audible Bookmark Extractor v1.0")
    print("To download your audiobooks, ensure you are authenticated, then enter download_books")
    print("Enter help for a list of commands")
    
  async def command_loop(self):
    command_input = input("\n\nEnter command: ")
    command = command_input.split(" ")[0]
    additional_kwargs = command_input.replace(command, '')
    _kwargs = {}

    if additional_kwargs:
        for kwarg in additional_kwargs.split(" --"):
            if kwarg == "":
                continue
            li_kwarg = kwarg.split("=")

            if not len(li_kwarg) > 1:
                await self.invalid_kwarg_callback()

            _kwargs[li_kwarg[0]] = li_kwarg[1]

    if not self.audible_obj and command not in AUTHLESS_COMMANDS:
        await self.invalid_auth_callback()
    # Takes the command supplied and sees if we have a function with the prefix cmd_ that we can execute with the given kwargs
    if command == "help":
      self.show_help()
    elif command == "authenticate":
        self.audible_obj = await AudibleAPI.authenticate()
    elif command == "readwise_authenticate":
        self.readwise_obj = await Readwise.authenticate()
    elif command == "quit" or command == "exit":
      return
    elif command.startswith("readwise"):
        command = command.replace("readwise_", "")
        await getattr(self.readwise_obj, f"cmd_{command}", self.invalid_command_callback)(**_kwargs)    
    else:    
        await getattr(self.audible_obj, f"cmd_{command}", self.invalid_command_callback)(**_kwargs)
    
    await self.command_loop()
  
  # Callbacks
  async def invalid_command_callback(self):
      print("Invalid command, try again")      

  async def invalid_kwarg_callback(self):
      print("Invalid command or arguments supplied, try again")      
    
  async def invalid_auth_callback(self):
      print("Invalid Audible credentials, run authenticate and try again")      
