import os
from constants import artifacts_root_directory

class OpenAIConfig:
  
  def __init__(self, api_key):
    self.api_key = api_key
  
  @classmethod
  async def authenticate(self) -> "OpenAIConfig":
      openai_key_path = f"{artifacts_root_directory}/secrets/openai_key.json"
      if os.path.exists(openai_key_path):
          print(f"You are already authenticated with OpenAI, to switch keys, delete the file at {openai_key_path} and try again")
          with open(openai_key_path, "r") as f:
            api_key = f.read().strip()
          return OpenAIConfig(api_key)
      
      api_key = input("OpenAI API Key (Go to https://platform.openai.com/api-keys to get one): ")
      
      os.makedirs(f"{artifacts_root_directory}/secrets/", exist_ok=True)
      with open(openai_key_path, "w") as f:
        f.write(str(api_key).strip())
      print("OpenAI API Key saved locally successfully")
      
      return OpenAIConfig(api_key)

