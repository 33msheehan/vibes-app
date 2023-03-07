import openai
import os
from flask import Flask, jsonify
import random
from flask import request
import time
from data import *
import boto3
import json
from boto3.dynamodb.types import TypeDeserializer
from datetime import datetime
import logging
import math

# Define a logger object
logger = logging.getLogger(__name__)

# Flask Setup
app = Flask(__name__)

# Open AI Setup
openai.organization = os.getenv("OPENAI_ORG")
openai.api_key = os.getenv("OPENAI_API_KEY")

# DynamoDB Setup
client = boto3.client("dynamodb")
deserializer = TypeDeserializer()


MAKE_CALLS = False


@app.route("/api/get_fortune", methods=["GET"])
def get_fortune():
    try:
        # Call the function that generates a response using OpenAI"s API
        fortune_text = call_to_the_future()

        # Return the generated fortune as a JSON object
        return jsonify({"fortune": fortune_text})

    except Exception as e:
        # Log any exceptions that occur during the process
        logger.error(f"Error generating fortune: {e}")
        # Raise a custom exception with a more user-friendly message
        raise Exception(
            "An error occurred while generating your fortune. Please try again later.") from e


@app.route("/api/clarify_vibes", methods=["POST"])
def clarify_vibes():
    """
    Get clarification on the user"s vibe.

    Returns:
        dict: A dictionary containing the answer to the user"s question.
    """

    try:
        # Log that the "clarify_vibes" API endpoint was called
        logging.info("Request for vibe clarification received")

        # Get the request data from the JSON payload
        data = request.get_json()

        # Log the retrieved request data
        logging.info(f"Retrieved request data: {data}")

        fortune_text = call_for_clarity(data)
        logging.info(f"Retrieved clarification: {fortune_text}")

        # Return the clarification as a JSON response
        return jsonify({"answer": fortune_text})
    except Exception as e:
        # Log any errors that occur
        logging.error(f"An error occurred while clarifying user vibe: {e}")
        raise e


@app.route("/api/get_initial_vibe", methods=["GET"])
def get_initial_vibe():
    """
    Get the current vibe for the user.

    Returns:
        dict: A dictionary containing the user"s vibe information.
    """

    try:
        # Log that the "get_vibe" API endpoint was called
        logging.info("Request for user vibe received")

        # Get the user ID from the request
        user_id = get_user_id()

        # Log the retrieved user ID
        logging.info(f"Retrieved user ID: {user_id}")

        # Get the user"s information from the "vibes-db" table
        user_info, user_exists = get_user_info(user_id)

        # If the user does not exist in the database, initialize their information
        if not user_exists:
            user_info = initialise_user(user_id)

        # If the user has a timeToNextOracle value, check if it has passed and reset the user"s vibe if necessary
        if ("timeToNextOracle" in user_info):
            if not (user_info["timeToNextOracle"] == None):
                now = datetime.utcnow()
                reset_time = datetime.fromtimestamp(
                    int(math.floor(int(user_info["timeToNextOracle"]) / 1000.0)))

                # If the current time is after the reset time, reset the user"s vibe
                if now > reset_time:
                    logging.info(f"Resetting vibe for user {user_id}")
                    user_info = initialise_user(user_id, first_time=False)

        # Log the retrieved user information
        logging.info(
            f"Retrieved user info: {user_info}, user exists: {user_exists}")

        # Return the user"s information as a JSON response
        return jsonify(user_info)
    except Exception as e:
        # Log any errors that occur
        logging.error(f"An error occurred while retrieving user vibe: {e}")
        raise e


@app.route("/api/update_state", methods=["POST"])
def update_state():
    try:
        # Extract the user ID from the request arguments
        id = get_user_id()

        # Extract the state information from the request JSON
        state = request.get_json()

        # Update the user"s state in the database
        updated_state = update_user(id, state)

        # Log the successful update and return the updated state information
        logger.info(f"User {id} state updated successfully")
        return jsonify(updated_state)

    except Exception as e:
        # Log any exceptions that occur during the update process
        logger.error(f"Error updating user {id}: {e}")

        # Raise a custom exception with a more user-friendly message
        raise Exception(
            "An error occurred while updating the user's state. Please try again later.") from e


def get_devine_instruction():
    """
    Get a devine instruction for the user.

    Returns:
        dict: A dictionary containing the devine instruction.
    """

    try:
        # Log that a devine instruction was requested
        logging.info("Request for devine instruction received")

        if (app.debug):
            # Call the API to get a devine instruction
            fortune_response = call_to_the_future()

            # Extract the devine instruction from the response
            fortune_text = fortune_response.choices[0].message.content

            # Log the retrieved devine instruction
            logging.info(f"Devine instruction retrieved: {fortune_text}")
        else:
            # Use a fake devine instruction if not in debug mode
            fortune_text = EXAMPLE_TEXT
            time.sleep(2)

            # Log the fake devine instruction
            logging.info(f"Fake devine instruction retrieved: {fortune_text}")

        # Return the devine instruction as a JSON response
        return jsonify({
            "fortune": fortune_text
        })
    except Exception as e:
        # Log any errors that occur
        logging.error(
            f"An error occurred while retrieving devine instruction: {e}")
        raise e


def get_user_info(id):
    """
    Get information about a user from the "vibes-db" DynamoDB table.

    Args:
        id (str): The user"s ID.

    Returns:
        tuple: A tuple containing a dictionary of the user"s information
               and a boolean indicating whether the information was found.
    """

    try:
        # Query the DynamoDB table
        response = client.get_item(
            TableName="vibes-db",
            Key={
                "id": {
                    "S": id
                }
            }
        )

        # Check if the item was found
        if "Item" in response:
            # Extract the initial state map from the item dictionary
            info = response["Item"]["vibe"]["M"]

            # Convert the DynamoDB attribute values to Python data types
            info = {k: deserializer.deserialize(v) for k, v in info.items()}

            # Log the retrieved user info
            logging.info(f"Retrieved user info for ID {id}: {info}")

            return info, True
        else:
            # Log that the user was not found
            logging.info(f"User with ID {id} was not found")

            return None, False
    except Exception as e:
        # Log any errors that occur
        logging.error(
            f"An error occurred while retrieving user info for ID {id}: {e}")
        raise e


def initialise_user(id, first_time=True):
    """
    Adds a new item to the "vibes-db" table representing a new user, or updates an existing item if the user ID already exists.
    Args:
        id (str): A string containing the unique ID of the user to add or update.
        first_time (bool): A boolean indicating whether this is the first time the user has been added to the table.
                           Default is True.
    Returns:
        dict: A dictionary representing the new or updated item that was added to the table.
    """
    try:
        # Create a dictionary representing the initial state for the user
        init_state = (
            {
                "M": {
                    "fortune": {"NULL": True},
                    "answer": {"NULL": True},
                    "response": {"NULL": True},
                    "isButtonShown": {"BOOL": True},
                    "isFortuneShown": {"BOOL": False},
                    "isClarityShown": {"BOOL": False},
                    "timeToNextOracle": {"NULL": True}
                }
            }
        )

        # Create a dictionary representing the new item
        item = {
            "id": {"S": id},
            "vibe": init_state
        }

        # Add the new item to the table if this is the user"s first time
        if first_time:
            response = client.put_item(
                TableName="vibes-db",
                Item=item
            )
        # Update the existing item if the user already exists in the table
        else:
            response = client.update_item(
                TableName="vibes-db",
                Key={
                    "id": {"S": id}
                },
                UpdateExpression="SET vibe = :val1",
                ExpressionAttributeValues={
                    ":val1": init_state
                },
                ReturnValues="UPDATED_NEW"
            )

        # Check if the item was successfully added to or updated in the table
        if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            logger.info(
                f"New item with ID {id} added to or updated in the table vibes-db")
        else:
            logger.error("Failed to add or update item in the table")

        return item

    except Exception as e:
        # Log any exceptions that occur during the function"s execution
        logger.error(f"Error initialising user: {e}")
        # Raise a custom exception with a more user-friendly message
        raise Exception(
            "An error occurred while initialising the user. Please try again later.") from e


def update_user(id, state):
    """
    Updates the state of a user with the given ID in the vibes-db table.
    Args:
        id (str): The ID of the user to update.
        state (dict): A dictionary containing the new state information to set for the user.
    Returns:
        dict: A dictionary containing the updated state information for the user.
    """
    try:
        # Convert the state dictionary into the format required by DynamoDB
        state = {
            "M": {
                "fortune": {"S": state["fortune"] if state["fortune"] else ""},
                "question": {"S": state["question"] if state["question"] else ""},
                "answer": {"S": state["answer"] if state["answer"] else ""},
                "isButtonShown": {"BOOL": state["isButtonShown"]},
                "isFortuneShown": {"BOOL": state["isFortuneShown"]},
                "isClarityShown": {"BOOL": state["isClarityShown"]},
                "timeToNextOracle": {"N": str(state["timeToNextOracle"])}
            }
        }

        # Call the DynamoDB client"s update_item method to update the user"s state in the table
        response = client.update_item(
            TableName="vibes-db",
            Key={
                "id": {"S": id}
            },
            UpdateExpression="SET vibe = :val1",
            ExpressionAttributeValues={
                ":val1": state
            },
            ReturnValues="UPDATED_NEW")

        # Extract and return the updated state information from the response
        return response["Attributes"]["vibe"]["M"]

    except Exception as e:
        # Log any exceptions that occur during the update process
        logger.error(f"Error updating user {id}: {e}")
        # Raise a custom exception with a more user-friendly message
        raise Exception(
            "An error occurred while updating the user's state. Please try again later.") from e


def get_user_id():
    """
    Generates a unique user ID based on the user"s IP address, or returns a debug ID if in debug mode.
    Returns:
        str: A string containing the unique user ID.
    """
    try:
        # If the application is in debug mode, return a debug user ID
        if app.debug:
            return "debug_user"

        # Otherwise, generate a unique user ID based on the user"s IP address
        else:
            return str(hash(request.remote_addr))

    except Exception as e:
        # Log any exceptions that occur during the function"s execution
        logger.error(f"Error generating user ID: {e}")
        # Raise a custom exception with a more user-friendly message
        raise Exception(
            "An error occurred while generating the user ID. Please try again later.") from e


def call_for_clarity(data):
    """
    Uses the OpenAI API to generate a chat response based on the given input data.
    Args:
        data (dict): A dictionary containing the input data, with keys "text" and "fortune".
    Returns:
        str: A string containing the generated chat response.
    """
    try:
        # Use the OpenAI API to generate a chat response based on the given input data
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                BASE_INSTRUCTION,
                {
                    "role": "user",
                    "content": "Make the prediction {} and {}".format(random.choice(EMOTIONS), random.choice(EMOTIONS)),
                },
                {
                    "role": "system",
                    "content": data["fortune"],
                },
                {
                    "role": "user",
                    "content": data["question"],
                },
            ],
            temperature=1,
            max_tokens=75
        )

        # Extract and return the generated chat response from the API response
        return response.choices[0].message.content

    except Exception as e:
        # Log any exceptions that occur during the API call
        logger.error(f"Error generating chat response: {e}")
        # Raise a custom exception with a more user-friendly message
        raise Exception(
            "An error occurred while generating the chat response. Please try again later.") from e


def call_to_the_future():
    """
    Uses the OpenAI API to generate a chat response based on the given input.
    Returns:
        str: A string containing the generated chat response.
    """
    try:
        # Use the OpenAI API to generate a chat response based on the given input
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                BASE_INSTRUCTION,
                {
                    "role": "user",
                    "content": "Make the prediction {} and {}".format(random.choice(EMOTIONS), random.choice(EMOTIONS)),
                },
                {
                    "role": "user",
                    "content": random.choice(POSSIBLE_ADDITIONAL_INSTRUCTIONS),
                }
            ],
            temperature=1,
            max_tokens=75
        )

        logger.info(response)

        # Extract and return the generated chat response from the API response
        return response.choices[0].message.content

    except Exception as e:
        # Log any exceptions that occur during the API call
        logger.error(f"Error generating chat response: {e}")
        # Raise a custom exception with a more user-friendly message
        raise Exception(
            "An error occurred while generating the chat response. Please try again later.") from e


if __name__ == "__main__":
    app.run(debug=True)
