"""A module that contains a command to send a message to the user"""

from colorama import Fore, Style
# from autogpt.config.nconfig import Config
from autogpt.logs import logger
from autogpt.utils import clean_input
from autogpt.commands.command import command


@command(
    "message_user",
    "Message the user",
    '"message": "<message_for_the_user>"',
)
def message_user(message: str) -> list[str]:
    """Message the user and get the response
    
    Args:
        message (str): The message to be sent to the user

    Returns:
        list[str]: The list with the message for the user and his/her response
    """
    logger.info(message)
    console_input = clean_input(
        Fore.MAGENTA + "User:" + Style.RESET_ALL
        )
    
    return ["AAIA: " + message, console_input]