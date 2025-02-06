
import os
import constants
import json
import logging

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from cdp_langchain.agent_toolkits import CdpToolkit
from cdp_langchain.utils import CdpAgentkitWrapper

from db.wallet import add_wallet_info, get_wallet_info
from agent.custom_actions.get_latest_block import get_latest_block

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_agent():
    """Initialize the agent with CDP Agentkit."""
    # Initialize LLM.
    llm = ChatOpenAI(model=constants.AGENT_MODEL)

    # First try loading from environment variables
    wallet_seed = os.getenv(constants.WALLET_SEED_ENV_VAR)
    wallet_id = os.getenv(constants.WALLET_ID_ENV_VAR)

    if wallet_seed and wallet_id:
        logger.info("Initializing CDP Agentkit with wallet from environment")
        if wallet_seed.startswith('0x'):
            wallet_seed = bytes.fromhex(wallet_seed[2:])
        agentkit = CdpAgentkitWrapper(wallet_seed=wallet_seed, wallet_id=wallet_id)
    else:
        # Try loading from database
        wallet_info = get_wallet_info()
        if wallet_info:
            logger.info("Initializing CDP Agentkit with wallet from database")
            agentkit = CdpAgentkitWrapper(wallet_seed=wallet_info['seed'], wallet_id=wallet_info['id'])
        else:
            # Create new wallet
            logger.info("Creating new CDP Agentkit wallet")
            agentkit = CdpAgentkitWrapper()
            # Save wallet info to database
            wallet_data = {
                'id': agentkit.wallet.id,
                'seed': agentkit.wallet.seed
            }
            add_wallet_info(json.dumps(wallet_data))
            
    logger.info(f"Using wallet address: {agentkit.wallet._address}")

    # Initialize CDP Agentkit Toolkit and get tools.
    cdp_toolkit = CdpToolkit.from_cdp_agentkit_wrapper(agentkit)
    tools = cdp_toolkit.get_tools() + [get_latest_block]

    # Store buffered conversation history in memory.
    memory = MemorySaver()

    # Create ReAct Agent using the LLM and CDP Agentkit tools.
    return create_react_agent(
        llm,
        tools=tools,
        checkpointer=memory,
        state_modifier=constants.AGENT_PROMPT,
    )
