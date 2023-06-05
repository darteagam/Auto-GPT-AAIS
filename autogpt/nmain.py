"""The application entry point.  Can be invoked by a CLI or any other front end application."""
import logging
import sys
from pathlib import Path

from colorama import Fore, Style

from autogpt.agent.nagent import Agent
from autogpt.commands.command import CommandRegistry
from autogpt.config.nconfig import Config, check_openai_api_key
from autogpt.configurator import create_config
from autogpt.logs import logger
from autogpt.memory import get_memory
from autogpt.plugins import scan_plugins
from autogpt.prompts.nprompt import DEFAULT_TRIGGERING_PROMPT, construct_main_ai_config
from autogpt.utils import (
    get_current_git_branch,
    get_latest_bulletin,
    markdown_to_ansi_style,
)
from autogpt.workspace import Workspace
from scripts.install_plugin_deps import install_plugin_dependencies

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from typing import Optional


class Message(BaseModel):
    user_id: str
    text: str
    language: str

    @validator('user_id')
    def check_user_id(cls, v):
        if v.strip() == '':
            raise HTTPException(status_code=400, detail="The user ID cannot be empty.")
        return v

    @validator('text')
    def check_question(cls, v):
        if v.strip() == '':
            raise HTTPException(status_code=400, detail="The question cannot be empty.")
        return v

    @validator('language')
    def check_question(cls, v):
        if v.strip() == '':
            raise HTTPException(status_code=400, detail="The language cannot be empty.")
        return v


def run_auto_gpt(
    continuous: bool,
    continuous_limit: int,
    ai_settings: str,
    skip_reprompt: bool,
    speak: bool,
    debug: bool,
    gpt3only: bool,
    gpt4only: bool,
    memory_type: str,
    browser_name: str,
    allow_downloads: bool,
    skip_news: bool,
    workspace_directory: str,
    install_plugin_deps: bool,
):
    app = FastAPI()
    agents = {}

    # Configure logging before we do anything else.
    logger.set_level(logging.DEBUG if debug else logging.INFO)
    logger.speak_mode = speak

    cfg = Config()
    # TODO: fill in llm values here
    check_openai_api_key()
    create_config(
        continuous,
        continuous_limit,
        ai_settings,
        skip_reprompt,
        speak,
        debug,
        gpt3only,
        gpt4only,
        memory_type,
        browser_name,
        allow_downloads,
        skip_news,
    )

    if not cfg.skip_news:
        motd, is_new_motd = get_latest_bulletin()
        if motd:
            motd = markdown_to_ansi_style(motd)
            for motd_line in motd.split("\n"):
                logger.info(motd_line, "NEWS:", Fore.GREEN)
            if is_new_motd and not cfg.chat_messages_enabled:
                input(
                    Fore.MAGENTA
                    + Style.BRIGHT
                    + "NEWS: Bulletin was updated! Press Enter to continue..."
                    + Style.RESET_ALL
                )

        git_branch = get_current_git_branch()
        if git_branch and git_branch != "stable":
            logger.typewriter_log(
                "WARNING: ",
                Fore.RED,
                f"You are running on `{git_branch}` branch "
                "- this is not a supported branch.",
            )
        if sys.version_info < (3, 10):
            logger.typewriter_log(
                "WARNING: ",
                Fore.RED,
                "You are running on an older version of Python. "
                "Some people have observed problems with certain "
                "parts of Auto-GPT with this version. "
                "Please consider upgrading to Python 3.10 or higher.",
            )

    if install_plugin_deps:
        install_plugin_dependencies()

    # TODO: have this directory live outside the repository (e.g. in a user's
    #   home directory) and have it come in as a command line argument or part of
    #   the env file.
    if workspace_directory is None:
        workspace_directory = Path(__file__).parent / "auto_gpt_workspace"
    else:
        workspace_directory = Path(workspace_directory)
    # TODO: pass in the ai_settings file and the env file and have them cloned into
    #   the workspace directory so we can bind them to the agent.
    workspace_directory = Workspace.make_workspace(workspace_directory)
    cfg.workspace_path = str(workspace_directory)

    # HACK: doing this here to collect some globals that depend on the workspace.
    file_logger_path = workspace_directory / "file_logger.txt"
    if not file_logger_path.exists():
        with file_logger_path.open(mode="w", encoding="utf-8") as f:
            f.write("File Operation Logger ")

    cfg.file_logger_path = str(file_logger_path)

    cfg.set_plugins(scan_plugins(cfg, cfg.debug_mode))
    # Create a CommandRegistry instance and scan default folder
    command_registry = CommandRegistry()
    command_registry.import_commands("autogpt.commands.conversation")
    command_registry.import_commands("autogpt.commands.youtube_selenium")
    # command_registry.import_commands("autogpt.commands.analyze_code")
    # command_registry.import_commands("autogpt.commands.audio_text")
    # command_registry.import_commands("autogpt.commands.execute_code")
    command_registry.import_commands("autogpt.commands.nfile_operations")
    # command_registry.import_commands("autogpt.commands.git_operations")
    command_registry.import_commands("autogpt.commands.google_search")
    command_registry.import_commands("autogpt.commands.image_gen")
    # command_registry.import_commands("autogpt.commands.improve_code")
    # command_registry.import_commands("autogpt.commands.twitter")
    command_registry.import_commands("autogpt.commands.web_selenium")
    # command_registry.import_commands("autogpt.commands.write_tests")
    command_registry.import_commands("autogpt.napp")

    ai_config = construct_main_ai_config()
    ai_name = ai_config.ai_name
    ai_config.command_registry = command_registry
    # for v in ai_config.command_registry.commands.values():
    #     print('Name: ', v.name)
    #     print('Enabled: ', v.enabled)
    # print(cfg.google_api_key)
    # Initialize variables
    full_message_history = []
    next_action_count = 0

    # add chat plugins capable of report to logger
    if cfg.chat_messages_enabled:
        for plugin in cfg.plugins:
            if hasattr(plugin, "can_handle_report") and plugin.can_handle_report():
                logger.info(f"Loaded plugin into logger: {plugin.__class__.__name__}")
                logger.chat_plugins.append(plugin)

    # Initialize memory and make sure it is empty.
    # this is particularly important for indexing and referencing pinecone memory
    memory = get_memory(cfg, init=True)
    logger.typewriter_log(
        "Using memory of type:", Fore.GREEN, f"{memory.__class__.__name__}"
    )
    logger.typewriter_log("Using Browser:", Fore.GREEN, cfg.selenium_web_browser)
    system_prompt = ai_config.construct_full_prompt()

    if cfg.debug_mode:
        logger.typewriter_log("Prompt:", Fore.GREEN, system_prompt)

    print('Memory: ', memory)
    print('Full message history: ', full_message_history)
    print('System Prompt: ', system_prompt + '\n\n')


    @app.post("/answer")
    async def get_answer(message: Message):
        user_id = message.user_id
        question = message.text
        language = message.language

        # conversations = {'12345': Agent(12345), '2345': Agent(2345), ...}

        if user_id not in agents:
            # conversations[user_id] = agent.start_interaction()
            agents[user_id] = Agent(ai_name=ai_name,
                                           memory=memory,
                                           full_message_history=full_message_history,
                                           next_action_count=next_action_count,
                                           command_registry=command_registry,
                                           config=ai_config,
                                           system_prompt=system_prompt,
                                           triggering_prompt=DEFAULT_TRIGGERING_PROMPT,
                                           workspace_directory=workspace_directory,
                                           )

        try:
            answer = agents[user_id].generate_answer(question) # start_interaction()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
        return {"answer": answer}


    agent = Agent(
        ai_name=ai_name,
        memory=memory,
        full_message_history=full_message_history,
        next_action_count=next_action_count,
        command_registry=command_registry,
        config=ai_config,
        system_prompt=system_prompt,
        triggering_prompt=DEFAULT_TRIGGERING_PROMPT,
        workspace_directory=workspace_directory,
    )
    agent.start_interaction_loop()
