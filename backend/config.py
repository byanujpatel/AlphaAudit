import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # LLM Settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Bright Data Settings
    BRIGHT_DATA_API_KEY = os.getenv("BRIGHT_DATA_API_KEY")
    BRIGHT_DATA_CUSTOMER_ID = os.getenv("BRIGHT_DATA_CUSTOMER_ID")
    BRIGHT_DATA_SCRAPING_BROWSER_URL = os.getenv("BRIGHT_DATA_SCRAPING_BROWSER_URL")
    BRIGHT_DATA_WEB_UNLOCKER_PROXY = os.getenv("BRIGHT_DATA_WEB_UNLOCKER_PROXY")
    BRIGHT_DATA_SERP_API_KEY = os.getenv("BRIGHT_DATA_SERP_API_KEY")
    
    # Bright Data Zones for REST API Fallback
    BRIGHT_DATA_SERP_ZONE = os.getenv("BRIGHT_DATA_SERP_ZONE", "serp_api1")
    BRIGHT_DATA_WEB_UNLOCKER_ZONE = os.getenv("BRIGHT_DATA_WEB_UNLOCKER_ZONE", "web_unlocker1")

    # Local Bright Data MCP command template if using local stdio
    BRIGHT_DATA_MCP_SERVER_COMMAND = os.getenv(
        "BRIGHT_DATA_MCP_SERVER_COMMAND", 
        "npx -y @brightdata/mcp-server"
    )

    @classmethod
    def validate(cls):
        missing = []
        if not cls.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        if not cls.BRIGHT_DATA_API_KEY:
            missing.append("BRIGHT_DATA_API_KEY")
        
        # If the user didn't set specific proxy/browser/serp keys, we can fallback to using
        # the main BRIGHT_DATA_API_KEY if that's supported. We'll warn them or log it.
        return len(missing) == 0, missing

# Singleton instance
config = Config()
