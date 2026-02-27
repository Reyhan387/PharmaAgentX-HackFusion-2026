import os
from dotenv import load_dotenv
from langfuse import Langfuse

load_dotenv()

langfuse = Langfuse(
    public_key=os.getenv("pk-lf-88da0fd9-a934-4749-a55b-dafdf99ebf62"),
    secret_key=os.getenv("sk-lf-bab93c32-fda7-4f65-96ed-7301eec0aae0"),
    host="https://cloud.langfuse.com"
)