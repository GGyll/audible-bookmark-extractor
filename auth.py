import audible
import os

# Authorize and register in one step
auth = audible.Authenticator.from_login(
    os.environ.get("AUDIBLE_EMAIL"),
    os.environ.get("AUDIBLE_PASSWORD"),

    locale="uk",
    with_username=False
)
# Save credentials to file
auth.to_file("credentials.json")
