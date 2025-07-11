import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load .env file to get GROQ_API_KEY
load_dotenv()
client = OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")

# === Define Tools ===
tools = [
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["filename", "content"]
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "screenshot_file",
            "description": "Take a screenshot of a document or file and save as PNG.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Absolute path to the file"
                    },
                    "output_image": {
                        "type": "string",
                        "description": "Filename to save screenshot as (e.g., output.png)"
                    }
                },
                "required": ["filepath", "output_image"]
            }
        }
    }
]

# === Start interaction ===
user_task = input("What do you want to do? (write/screenshot): ").strip().lower()

messages = [{"role": "system", "content": "You are a helpful assistant who can write to files and take screenshots of documents."}]

if user_task == "write":
    filename = input("Enter filename (e.g., hello.txt): ").strip()
    content = input("Enter content to write: ").strip()
    user_prompt = f"Write the following content to a file named {filename}: {content}"
elif user_task == "screenshot":
    filepath = input("Enter full path to the PDF file: ").strip()
    output_image = input("Enter output image filename (e.g., shot.png): ").strip()
    user_prompt = f"Take a screenshot of the first page of {filepath} and save it as {output_image}"
else:
    print("❌ Invalid choice. Please enter 'write' or 'screenshot'.")
    exit()

# Add user prompt
messages.append({"role": "user", "content": user_prompt})

# === Call Groq API ===
response = client.chat.completions.create(
    model="deepseek-r1-distill-llama-70b",
    messages=messages,
    tools=tools,
    tool_choice="auto",
)

# === Handle Tool Call ===
tool_calls = response.choices[0].message.tool_calls

if tool_calls:
    for tool_call in tool_calls:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        if name == "write_file":
            filename = args["filename"]
            content = args["content"]
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ File '{filename}' created with content:\n{content}")

        elif name == "screenshot_file":
            from pdf2image import convert_from_path

            filepath = args["filepath"]
            output_image = args["output_image"]

            if not os.path.isfile(filepath):
                print(f"❌ File '{filepath}' does not exist.")
            else:
                try:
                    pages = convert_from_path(filepath, first_page=1, last_page=1)
                    page = pages[0]
                    page.save(output_image, "PNG")
                    print(f"✅ Screenshot saved as '{output_image}'.")
                except Exception as e:
                    print(f"❌ Error taking screenshot: {str(e)}")
else:
    print("🤖 Assistant:", response.choices[0].message.content)
