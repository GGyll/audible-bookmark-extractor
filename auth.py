import audible

from login_details import AUDIBLE_EMAIL, AUDIBLE_PASSWORD

# Authorize and register in one step
auth = audible.Authenticator.from_login(
    AUDIBLE_EMAIL,
    AUDIBLE_PASSWORD,
    locale="uk",
    with_username=False
)
# Save credentials to file
auth.to_file("credentials.json")
