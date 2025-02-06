
import sqlite3
from typing import Optional, Dict
import logging
import json
import os
import constants

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_wallet_info(info: str) -> None:
    """
    Add or update wallet information in the database.
    """
    try:
        with sqlite3.connect("agent.db") as con:
            cur = con.cursor()
            cur.execute("DELETE FROM wallet")  # Clear existing entries
            cur.execute("INSERT INTO wallet(info) VALUES (?)", (info,))
            con.commit()
            logger.info("Wallet configuration updated")
                
    except sqlite3.Error as e:
        logger.error(f"Database error occurred: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")

def get_wallet_info() -> Optional[Dict]:
    """
    Retrieve wallet information from the database or environment.
    Prioritizes environment variables over database.
    """
    # First check environment variables
    wallet_id = os.getenv(constants.WALLET_ID_ENV_VAR)
    wallet_seed = os.getenv(constants.WALLET_SEED_ENV_VAR)
    
    if wallet_id and wallet_seed:
        logger.info("Using wallet info from environment variables")
        return {
            'id': wallet_id,
            'seed': wallet_seed
        }
    
    # If not in environment, try database
    try:
        with sqlite3.connect("agent.db") as con:
            cur = con.cursor()
            cur.execute("SELECT info FROM wallet")
            result = cur.fetchone()
            
            if result:
                return json.loads(result[0])
            return None
                
    except sqlite3.Error as e:
        logger.error(f"Failed to retrieve wallet info: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error while retrieving wallet info: {str(e)}")
        return None
