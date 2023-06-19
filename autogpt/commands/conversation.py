"""A module that contains a command to send a message to the user"""

from colorama import Fore, Style
# from autogpt.config.nconfig import Config
from autogpt.logs import logger
from autogpt.utils import clean_input
from autogpt.commands.command import command


@command(
    "message_user",
    "Message the user",
    '"message": "<message_for_the_user>", "attatchments": "<attatchments>"',
)
def message_user(message: str, attatchments=None) -> dict:
    """Message the user and get the response
    
    Args:
        message (str): The message to be sent to the user
        attatchments (dict): The attatchments to the message for the user

    Returns:
        dict: The message for the user in a dictionary format
    """
    aaia_message = {}
    aaia_message['message'] = message
    aaia_message['attatchments'] = attatchments
    
    return aaia_message


# @command(
#     "message_user",
#     "Message the user",
#     '"message": "<message_for_the_user>", "attatchments": "<attatchments>"',
# )
# def message_user(message: str, attatchments: dict | None) -> dict:
#     """Message the user and get the response
    
#     Args:
#         message (str): The message to be sent to the user
#         attatchments (dict): The attatchments to the message for the user

#     Returns:
#         dict: The message for the user in a dictionary format
#     """
#     aaia_message = {}
#     aaia_message['message'] = message
#     aaia_message['attatchments'] = attatchments
    
#     return aaia_message