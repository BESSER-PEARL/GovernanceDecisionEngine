# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path
import logging

from besser.agent.core.agent import Agent
from besser.agent.core.event import ReceiveMessageEvent
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from besser.agent.platforms.websocket import WEBSOCKET_PORT, STREAMLIT_PORT

# Configure the logging module (optional)
logger.setLevel(logging.INFO)

# Create the agent
agent = Agent('ui_agent')
# Load agent properties stored in a dedicated file
agent.load_properties('../config.ini')
agent.set_property(WEBSOCKET_PORT, 8012)
agent.set_property(STREAMLIT_PORT, 5002)
# Define the platform your agent will use
websocket_platform = agent.use_websocket_platform(use_ui=True)

# STATES

idle_state = agent.new_state('idle_state', initial=True)
send_state = agent.new_state('send_state')

# STATES BODIES' DEFINITION + TRANSITIONS

def idle_body(session: Session):
    session.reply("I'ready to take your input")

idle_state.set_body(idle_body)
idle_state.when_event(ReceiveMessageEvent()) \
          .with_condition(lambda session: session.event.human) \
          .go_to(send_state)


def send_body(session: Session):
    message = session.event.message
    session.send_message_to_websocket(
        url='ws://localhost:8765',
        message=message
    )


send_state.set_body(send_body)
send_state.go_to(idle_state)

# RUN APPLICATION

if __name__ == '__main__':
    agent.run()
