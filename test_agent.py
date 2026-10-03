from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

endpoint = "https://warrantycheckai-resource.services.ai.azure.com/api/projects/WarrantyCheckAI"

project_client = AIProjectClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential(),
)

my_agent = "WarrantyCheckAI"
my_version = "1"

openai_client = project_client.get_openai_client()

response = openai_client.responses.create(
    input=[
        {
            "role": "user",
            "content": "Tell me what you can help with."
        }
    ],
    extra_body={
        "agent_reference": {
            "name": my_agent,
            "version": my_version,
            "type": "agent_reference"
        }
    },
)

print("Response output:")
print(response.output_text)