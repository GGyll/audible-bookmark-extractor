import asyncio
from command import Command

async def main():
    cmd = Command()
    cmd.welcome()
    try:
        await cmd.command_loop()
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    asyncio.run(main())