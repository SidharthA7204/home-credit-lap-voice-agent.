import asyncio
import json
import os

from dotenv import load_dotenv
from app.interpretation import AIInterpreter

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv("MODEL_NAME", "openai/gpt-oss-20b")

if not API_KEY:
    raise RuntimeError("GROQ_API_KEY was not found in your .env file")


async def main():
    interpreter = AIInterpreter(
        api_key=API_KEY,
        model=MODEL,
    )

    test_cases = [
        {
            "name": "Clear answer",
            "transcript": "Residential",
            "asked_field": "property_type",
            "question": "What type of property do you own?",
        },
        {
            "name": "Partial answer",
            "transcript": "Resi",
            "asked_field": "property_type",
            "question": "What type of property do you own?",
        },
        {
            "name": "Unclear answer",
            "transcript": "Something, I am not sure",
            "asked_field": "property_type",
            "question": "What type of property do you own?",
        },
        {
            "name": "Clear commercial answer",
            "transcript": "It is a shop",
            "asked_field": "property_type",
            "question": "What type of property do you own?",
        },
        {
            "name": "Ambiguous ownership answer",
            "transcript": "We have it together, maybe",
            "asked_field": "ownership",
            "question": "Do you own the property alone or jointly?",
        },
    ]

    for case in test_cases:
        print("\n" + "=" * 60)
        print(f"TEST: {case['name']}")
        print(f"Transcript: {case['transcript']}")

        result = await interpreter.interpret(
            case["transcript"],
            asked_field=case["asked_field"],
            question=case["question"],
            conversation_context="",
            language="en",
        )

        print(json.dumps({
            "status": result.status,
            "candidate_value": result.candidate_value,
            "candidate_display": result.candidate_display,
            "alternatives": result.alternatives,
            "reason": result.reason,
        }, indent=2))


if __name__ == "__main__":
    asyncio.run(main())