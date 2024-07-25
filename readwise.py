import os
from constants import artifacts_root_directory

class Readwise:
  
  def __init__(self, token):
    self.token = token
  
  async def cmd_readwise_authenticate(self):
      if os.path.exists(f"{artifacts_root_directory}/secrets/readwise_token.json"):
          print(f"You are already authenticated, to switch accounts, delete secrets directory under {artifacts_root_directory} and try again")          
      self.token = input("Readwise Token:")
      
      os.makedirs(f"{artifacts_root_directory}/secrets/", exist_ok=True)
      with open(f"{artifacts_root_directory}/secrets/readwise_token.json", "w") as f:
        f.write(str(self.token))
      print("Token saved locally successfully")
  
  async def cmd_readwise_post_highlights(self):
    priht ("Posting to Readwise…")