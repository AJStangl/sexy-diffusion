import logging

import dotenv
dotenv.load_dotenv()
logging.getLogger("azure.storage").setLevel(logging.WARNING)
