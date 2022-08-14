import audible
import httpx


# def captcha_callback(captcha_url: str) -> str:
#     """Helper function for handling captcha."""

#     captcha = httpx.get(captcha_url).content
#     f = io.BytesIO(captcha)
#     img = Image.open(f)
#     img.show()
#     guess = input("Answer for CAPTCHA: ")
#     return str(guess).strip().lower()

# def captcha_callback(captcha_url: str) -> str:
#     """Helper function for handling captcha."""

#     captcha = httpx.get(captcha_url).content
#     f = io.BytesIO(captcha)
#     img = Image.open(f)
#     img.show()
#     guess = input("Answer for CAPTCHA: ")
#     return str(guess).strip().lower()


def authorize_audible(audible_email, audible_password, locale, captcha_callback):
    # Authorize and register in one step
    auth = audible.Authenticator.from_login(
        audible_email,
        audible_password,
        locale=locale,
        with_username=False,
        captcha_callback=captcha_callback
    )
    return auth
