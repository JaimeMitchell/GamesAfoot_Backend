
from flask import Blueprint, jsonify, request, abort, make_response
from ..db import db
from ..models.location import Location
from ..models.user_input import UserInput
from sqlalchemy import func, union, except_
from sqlalchemy.exc import SQLAlchemyError
from openai import OpenAI
import os
import json

bp = Blueprint("tours", __name__, url_prefix="/tours")

# client = OpenAI(
#     api_key=os.environ.get("OPENAI_API_KEY"),
#     base_url="https://api.llama-api.com"
# )

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

@bp.post("", strict_slashes=False)
def create_user_input():
    request_body = request.get_json()

    try:
        new_user_input = UserInput(
            latitude=request_body['latitude'],
            longitude=request_body['longitude'],
            distance=request_body['distance'],
            num_sites=request_body['num_sites'],
            game_type=request_body['game_type']
        )
        db.session.add(new_user_input)
        db.session.commit()

        return make_response(new_user_input.to_dict(), 201)

    except KeyError as e:
        abort(make_response({"message": f"missing required value: {e}"}, 400))

@bp.get("", strict_slashes=False)
def get_user_inputs():
    user_inputs = UserInput.query.all()
    response = []

    for user_input in user_inputs:
        response.append({
            "id": user_input.id,
            "latitude": user_input.latitude,
            "longitude": user_input.longitude,
            "distance": user_input.distance,
            "num_sites": user_input.num_sites,
            "game_type": user_input.game_type
        })

    return jsonify(response)

@bp.get("/<int:char_id>/user_input", strict_slashes=False)
def get_user_input(char_id):
    user_input = validate_model(UserInput, char_id)

    if not user_input:
        return make_response(jsonify(f"No user input found for ID {char_id}"), 404)

    locations = Location.query.filter_by(user_input_id=user_input.id).all()
    response = {
        "User_Input_Id": user_input.id,
        "Locations": []
    }
    for location in locations:
        response["Locations"].append({
            "location name": location.name,
            "location lat": location.latitude,
            "location long": location.longitude,
            "location description": location.description,
            "location clue": location.clue,
            "location id": location.id
        })

    return jsonify(response)

@bp.post("/<int:char_id>/generate_locations", strict_slashes=False)
def add_locations(char_id):
    user_input = validate_model(UserInput, char_id)

    # Check if locations have already been generated
    if user_input.locations:
        return make_response(jsonify(f"Locations already generated for User Input ID {user_input.id}"), 201)

    # Generate new locations
    locations_data = generate_locations(user_input)

    if not locations_data:
        return make_response(jsonify("Failed to generate locations"), 500)

    try:
        locations = json.loads(locations_data) if isinstance(locations_data, str) else locations_data
    except json.JSONDecodeError:
        return make_response(jsonify("Failed to parse generated locations"), 500)

    # Add new locations to the database
    try:
        new_locations = []

        for location in locations:
            # Ensure latitude and longitude are converted to strings
            latitude = str(location["latitude"])
            longitude = str(location["longitude"])

            new_location = Location(
                name=location["name"],
                latitude=latitude,
                longitude=longitude,
                description=location["description"],
                clue=location["clue"],
                user_input=user_input
            )
            new_locations.append(new_location)

        db.session.add_all(new_locations)
        db.session.commit()

        return make_response(jsonify(f"Locations successfully added to User Input ID {user_input.id}"), 201)

    except SQLAlchemyError as e:
        db.session.rollback()
        return make_response(jsonify(f"Failed to add locations: {str(e)}"), 500)

import json

def generate_locations(user_input):
    input_message = f"Generate a JSON array of {user_input.num_sites} {user_input.game_type} within exactly {user_input.distance} square mile/s and/or {user_input.distance} walking distance of the user's location, which is ({user_input.latitude}, {user_input.longitude}) from start to finish. Each object should include a string data type for 'name', 'latitude', 'longitude', 'description', and 'clue'. However, DO NOT MAKE UP FICTIONAL LOCATIONS. F Make sure to ONLY RETURN A JSON ARRAY AND NEVER A STRING REPRESENTATION OF THE JSON ARRAY."

    print(f'input_message: {input_message}')

    completion = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "user", "content": input_message}
        ],
        temperature=0.01  # Adjust as needed
    )

    response_content = completion.choices[0].message.content.strip()

    # First try to parse response_content as JSON
    try:
        response_json = json.loads(response_content)
        if isinstance(response_json, dict) or isinstance(response_json, list):
            return response_json
        else:
            raise ValueError("Invalid JSON format")
    except (json.JSONDecodeError, ValueError):
        # If parsing fails, clean response_content to make it valid JSON
        try:
            cleaned_content = clean_to_json(response_content)
            response_json = json.loads(cleaned_content)
            if isinstance(response_json, dict) or isinstance(response_json, list):
                return response_json
            else:
                raise ValueError("Invalid JSON format after cleaning")
        except (json.JSONDecodeError, ValueError):
            # If still cannot parse as JSON, handle as needed (e.g., log the issue or return a default response)
            return {"error": "Failed to parse JSON"}

def clean_to_json(input_str):
    # Clean input_str to make it valid JSON by removing all non-JSON characters
    cleaned_str = ''.join(filter(lambda x: x in '[]{}"\'.,:0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ', input_str))
    return cleaned_str.strip()


@bp.put("/<int:char_id>", strict_slashes=False)
def update_user_input(char_id):
    user_input = validate_model(UserInput, char_id)

    request_body = request.get_json()

    try:
        user_input.latitude = request_body.get('latitude', user_input.latitude)
        user_input.longitude = request_body.get('longitude', user_input.longitude)
        user_input.distance = request_body.get('distance', user_input.distance)
        user_input.num_sites = request_body.get('num_sites', user_input.num_sites)
        user_input.game_type = request_body.get('game_type', user_input.game_type)

        db.session.commit()

        return make_response(user_input.to_dict(), 200)

    except KeyError as e:
        abort(make_response({"message": f"missing required value: {e}"}, 400))

    except SQLAlchemyError as e:
        db.session.rollback()
        return make_response(jsonify(f"Failed to update user input: {str(e)}"), 500)


@bp.delete("/<int:char_id>", strict_slashes=False)
def delete_user_input(char_id):
    user_input = validate_model(UserInput, char_id)

    try:
        db.session.delete(user_input)
        db.session.commit()

        return make_response(jsonify(f"User Input ID {user_input.id} deleted successfully"), 200)

    except SQLAlchemyError as e:
        db.session.rollback()
        return make_response(jsonify(f"Failed to delete user input: {str(e)}"), 500)

# # Locations I can't quite figure out why I'd want to update locations or how that would work in the game play. I think it's smarter to just delete and regenerate locations. Saves space and time.
#
# @bp.put("/locations/<int:location_id>", strict_slashes=False)
# def update_location(location_id):
#     location = validate_model(Location, location_id)

#     request_body = request.get_json()

#     try:
#         location.name = request_body.get('name', location.name)
#         location.latitude = request_body.get('latitude', location.latitude)
#         location.longitude = request_body.get('longitude', location.longitude)
#         location.description = request_body.get('description', location.description)
#         location.clue = request_body.get('clue', location.clue)

#         db.session.commit()

#         return make_response(location.to_dict(), 200)

#     except KeyError as e:
#         abort(make_response({"message": f"missing required value: {e}"}, 400))

#     except SQLAlchemyError as e:
#         db.session.rollback()
#         return make_response(jsonify(f"Failed to update location: {str(e)}"), 500)


# @bp.delete("/locations/<int:location_id>", strict_slashes=False)
# def delete_location(location_id):
#     location = validate_model(Location, location_id)

#     try:
#         db.session.delete(location)
#         db.session.commit()

#         return make_response(jsonify(f"Location ID {location.id} deleted successfully"), 200)

#     except SQLAlchemyError as e:
#         db.session.rollback()
#         return make_response(jsonify(f"Failed to delete location: {str(e)}"), 500)


def validate_model(cls, id):
    try:
        id = int(id)
    except ValueError:
        abort(make_response({"message": f"{cls.__name__} {id} invalid"}, 400))

    model = cls.query.get(id)
    if not model:
        abort(make_response({"message": f"{cls.__name__} {id} not found"}, 404))

    return model
