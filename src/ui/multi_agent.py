import asyncio
import os
import re
import subprocess
import time

from semantic_kernel import Kernel
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole

# Set your root directory
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))





# Custom termination strategy
class ApprovalTerminationStrategy(TerminationStrategy):
    async def should_agent_terminate(self, agent, history):
        for message in history:
            if message.role == AuthorRole.USER and "APPROVED" in message.content.upper():
                print('ApprovalTerminationStrategy invoked, agents should terminate')
                time.sleep(5)
                return True
        return False


def extract_html_code(msg):
    print('inside extract html_code function')
    html_pattern = re.compile(r"<html.*?</html>", re.DOTALL | re.IGNORECASE)
    for msg in messages:
        match = html_pattern.search(msg["content"])
        if match:
            print('match found',match.group(0))
            return match.group(0)
    
    return ""

import re

def extract_html_code(messages):
    html_pattern = re.compile(r"<html.*?</html>", re.DOTALL | re.IGNORECASE)
    for msg in messages:
        match = html_pattern.search(msg["content"])
        if match:
            print('match found',match.group(0))
            return match.group(0)
    return None


# Save HTML and push to GitHub
def save_html_and_push(html_code):
    print('inside save_html_and_push')
    file_path = os.path.join(ROOT_DIR, "index.html")
    with open(file_path, "w",encoding="utf-8") as f:
        f.write(html_code)
    git_bash = r"C:\Program Files\Git\bin\bash.exe"
    script_path = os.path.join(ROOT_DIR, "push_to_github.sh")
    subprocess.run([git_bash, "-c", "echo Hello from Git Bash!"], check=True)
    subprocess.run([
    git_bash,
    "-c",
    "git config --global --add safe.directory C:/LabFiles/Capstone-Project"])
    subprocess.run([git_bash, script_path], check=True)

# Create the kernel with Azure OpenAI
def create_kernel():
    kernel = Kernel()
    kernel.add_service(service=AzureChatCompletion(
        deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    ))
    return kernel

collected_messages = []
# Main function
async def run_multi_agent(user_input: str):
    kernel = create_kernel()

    # Define agents
    business_analyst = ChatCompletionAgent(
        kernel=kernel,
        name="BusinessAnalyst",
        instructions="You are a Business Analyst which will take the requirements from the user (also known as a 'customer') and create a project plan for creating the requested app. The Business Analyst understands the user requirements and creates detailed documents with requirements and costing. The documents should be usable by the SoftwareEngineer as a reference for implementing the required features, and by the Product Owner for reference to determine if the application delivered by the Software Engineer meets all of the user's requirements."
    )
    software_engineer = ChatCompletionAgent(
        kernel=kernel,
        name="SoftwareEngineer",
        instructions="You are a Software Engineer, and your goal is create a web app using HTML and JavaScript by taking into consideration all the requirements given by the Business Analyst. The application should implement all the requested features. Deliver the code to the Product Owner for review when completed. You can also ask questions of the BusinessAnalyst to clarify any requirements that are unclear."
    )
    product_owner = ChatCompletionAgent(
        kernel=kernel,
        name="ProductOwner",
        instructions="You are the Product Owner which will review the software engineer's code to ensure all user  requirements are completed. You are the guardian of quality, ensuring the final product meets all specifications. IMPORTANT: Verify that the Software Engineer has shared the HTML code using the format ```html [code] ```. This format is required for the code to be saved and pushed to GitHub. Once all client requirements are completed and the code is properly formatted, reply with 'READY FOR USER APPROVAL'. If there are missing features or formatting issues, you will need to send a request back to the SoftwareEngineer or BusinessAnalyst with details of the defect."
    )

    group_chat = AgentGroupChat(
        agents=[business_analyst, software_engineer, product_owner],
        termination_strategy=ApprovalTerminationStrategy())

    print("Enter your app requirements. Type 'exit' to quit.")
    await group_chat.add_chat_message(ChatMessageContent(content=user_input, role=AuthorRole.USER))
    

    try:
        async for response in group_chat.invoke():
            if response and response.name:
                collected_messages.append({
                    "role": response.name,
                    "content": response.content
                })
                print(f"\n# {response.name.upper()}:\n{response.content}")

            # ✅ Termination check
            if await group_chat.termination_strategy.should_agent_terminate(None, group_chat.history):
                print("\n✅ Termination condition met: 'APPROVED' found.")
                print(collected_messages)
                html_code = extract_html_code(collected_messages)
                print('html code:', html_code)
                if html_code:
                    print("✅ Saving and pushing HTML...")
                    save_html_and_push(html_code)

                # ✅ End the function here
                return {"messages": collected_messages}

    except Exception as e:
        print(f"Error during chat: {e}")

    # If it reaches here, the loop ended without termination
    print("🔁 Loop ended naturally without approval.")
    return {"messages": collected_messages}
