import asyncio
import warnings

from dotenv import load_dotenv
from google.adk import Runner
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.cli.utils import logs
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

import agent

load_dotenv(override=True)
warnings.filterwarnings('ignore', category=UserWarning)
logs.log_to_tmp_folder()


async def main():
    app_name = 'my_app'
    user_id_1 = 'user1'
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()

    runner = Runner(
        app_name=app_name,
        agent=agent.root_agent,
        artifact_service=artifact_service,
        session_service=session_service,
    )

    session = await session_service.create_session(app_name=app_name,
                                                   user_id=user_id_1)

    print("==================================================")
    print("Agent is ready! (Type 'quit' or 'exit' to stop)")
    print("==================================================\n")

    while True:
        # 1. Get user input
        user_message = input("You: ").strip()

        if user_message.lower() in ['quit', 'exit']:
            print("Exiting...")
            break
        if not user_message:
            continue

        # 2. Package the message
        content = types.Content(role='user',
                                parts=[types.Part.from_text(text=user_message)])

        print(f"Agent: ", end="", flush=True)

        # 3. Stream the response
        try:
            async for event in runner.run_async(
                    user_id=user_id_1,
                    session_id=session.id,
                    new_message=content,
            ):
                # Ensure we only print text parts (ignoring internal system/tool events)
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            # Print characters as they stream in
                            print(part.text, end="", flush=True)

            print()  # Print a newline when the stream finishes

        except Exception as e:
            print(f"\n[Error during execution]: {e}")

        print("-" * 50)


if __name__ == '__main__':
    # Run the interactive loop
    asyncio.run(main())
