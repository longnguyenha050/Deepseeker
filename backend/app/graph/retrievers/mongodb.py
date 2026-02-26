from langchain_mongodb.agent_toolkit import MONGODB_AGENT_SYSTEM_PROMPT
from langchain_mongodb.agent_toolkit.database import MongoDBDatabase
from langchain_mongodb.agent_toolkit.toolkit import MongoDBDatabaseToolkit
from langgraph.prebuilt import ToolNode

from dotenv import load_dotenv
import os

load_dotenv()


class MongoDBRetriever:
    def __init__(self, llm):
        self.db = MongoDBDatabase.from_connection_string(
            os.getenv("MONGODB_URI"),
            database="test"
        )

        self.toolkit = MongoDBDatabaseToolkit(
            db=self.db,
            llm=llm
        )

        self.tools = self.toolkit.get_tools()
        self.tool_map = {t.name: t for t in self.tools}

        self.schema_node = ToolNode(
            [self.tool_map["mongodb_schema"]],
            name="get_schema"
        )

        self.run_node = ToolNode(
            [self.tool_map["mongodb_query"]],
            name="run_query"
        )