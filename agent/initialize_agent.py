
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

    # Get wallet seed from environment variables (Replit secrets)
    wallet_seed = os.getenv(constants.WALLET_SEED_ENV_VAR)
    if not wallet_seed:
        logger.error("No wallet seed found in environment variables")
        raise ValueError("CDP_WALLET_SEED must be set in Replit secrets")

    logger.info("Initializing CDP Agentkit with wallet from secrets")
    # Convert wallet seed to bytes if it's a hex string
    if wallet_seed.startswith('0x'):
        wallet_seed = bytes.fromhex(wallet_seed[2:])
    agentkit = CdpAgentkitWrapper(wallet_seed=wallet_seed)
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
