
from flask import Blueprint, jsonify, request, abort, make_response
from ..db import db
from ..models.location import Location
from ..models.hunt import Hunt
from sqlalchemy import func, union, except_
from sqlalchemy.exc import SQLAlchemyError
from openai import OpenAI
import os
import json

bp = Blueprint("hunts", __name__, url_prefix="/hunts")

# client = OpenAI(
#     api_key=os.environ.get("OPENAI_API_KEY"),
#     base_url="https://api.llama-api.com"
# )

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

@bp.post("", strict_slashes=False)
def create_hunt():
    request_body = request.get_json()

    try:
        new_hunt = Hunt(
            start_latitude=request_body['start_latitude'],
            start_longitude=request_body['start_longitude'],
            distance=request_body['distance'],
            num_sites=request_body['num_sites'],
            game_type=request_body['game_type']
        )
        db.session.add(new_hunt)
        db.session.commit()

        return make_response(new_hunt.to_dict(), 201)

    except KeyError as e:
        abort(make_response({"message": f"missing required value: {e}"}, 400))

@bp.get("", strict_slashes=False)
def get_hunts():
    hunts = Hunt.query.all()
    response = []

    for hunt in hunts:
        response.append({
            "id": hunt.id,
            "start_latitude": hunt.start_latitude,
            "start_longitude": hunt.start_longitude,
            "distance": hunt.distance,
            "num_sites": hunt.num_sites,
            "game_type": hunt.game_type
        })

    return jsonify(response)

@bp.get("/<int:char_id>/locations", strict_slashes=False)
def get_hunt(char_id):
    hunt = validate_model(Hunt, char_id)

    if not hunt:
        return make_response(jsonify(f"No hunt found for ID {char_id}"), 404)

    locations = Location.query.filter_by(hunt_id=hunt.id).all()
    response = {
        "hunt_Id": hunt.id,
        "Locations": []
    }
    for location in locations:
        response["Locations"].append({
            "location name": location.name,
            "location lat": location.latitude,
            "location long": location.longitude,
            "location description": location.description,
            "location clues": location.clues,
            "location id": location.id
        })

    return jsonify(response)

@bp.post("/<int:char_id>/generate_locations", strict_slashes=False)
def add_locations(char_id):
    hunt = validate_model(Hunt, char_id)

    # Check if locations have already been generated
    if hunt.locations:
        return make_response(jsonify(f"Locations already generated for Hunt ID {hunt.id}"), 201)

    # Generate new locations
    locations_data = generate_locations(hunt)

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
   

    # Safely get the 'clues' key, default to an empty list if not present
            # clues = location.get("clues", [])
            
            new_location = Location(
                name=location.get("name", ""),
                latitude=str(location.get("latitude", "")),
                longitude=str(location.get("longitude", "")),
                description=location.get("description", ""),
                clues=location.get("clues"),
                hunt=hunt
            )
            #print each clues in the list
            for clues in location.get("clues"):
                print(clues)

            new_locations.append(new_location)

        db.session.add_all(new_locations)
        db.session.commit()

        return make_response(jsonify(f"Locations successfully added to Hunt ID {hunt.id}"), 201)

    except SQLAlchemyError as e:
        db.session.rollback()
        return make_response(jsonify(f"Failed to add locations: {str(e)}"), 500)

def generate_locations(hunt):
    input_message = f"Generate a JSON array of {hunt.num_sites} {hunt.game_type} within exactly {hunt.distance} miles from the user's location, which is ({hunt.start_latitude}, {hunt.start_longitude}) from start to finish. DO NOT GO OUT OF BOUNDS OF THE WALKING DISTANCE. DO NOT MAKE UP FICTIONAL LOCATIONS. Each object should include a string data type for 'name', 'latitude', 'longitude', 'description', and a JSON array of 3 'clues'. Make sure to ONLY respond with a JSON ARRAY, without any charaters before or after the JSON, and NEVER A STRING REPRESENTATION OF THE JSON ARRAY. Note: If you can not find real and legitimate locations in the user's location that meet the promts request, than just insert the string values in the JSON prompting the user as to why you couldn't find anymore real locations within the distance given, whether that's distance requirements or the kind of things they want to see in their treasure hunt." 

    print(f'input_message: {input_message}')

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": input_message}
        ],
        temperature=0.2,  # Lower temperature for more deterministic responses
        top_p=1.0,        # Use all possible tokens
        frequency_penalty=0,  # Allow repetitions
        presence_penalty=1.0  # Strongly discourage new topics
    )

    response_content = completion.choices[0].message.content.strip()
    print(response_content)
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
def update_hunt(char_id):
    hunt = validate_model(Hunt, char_id)

    request_body = request.get_json()

    try:
        hunt.start_latitude = request_body.get('start_latitude', hunt.start_latitude)
        hunt.start_longitude = request_body.get('start_longitude', hunt.start_longitude)
        hunt.distance = request_body.get('distance', hunt.distance)
        hunt.num_sites = request_body.get('num_sites', hunt.num_sites)
        hunt.game_type = request_body.get('game_type', hunt.game_type)

        db.session.commit()

        return make_response(hunt.to_dict(), 200)

    except KeyError as e:
        abort(make_response({"message": f"missing required value: {e}"}, 400))

    except SQLAlchemyError as e:
        db.session.rollback()
        return make_response(jsonify(f"Failed to update hunt: {str(e)}"), 500)


@bp.delete("/<int:char_id>", strict_slashes=False)
def delete_hunt(char_id):
    hunt = validate_model(Hunt, char_id)

    try:
        db.session.delete(hunt)
        db.session.commit()

        return make_response(jsonify(f"Hunt ID {hunt.id} deleted successfully"), 200)

    except SQLAlchemyError as e:
        db.session.rollback()
        return make_response(jsonify(f"Failed to delete hunt: {str(e)}"), 500)

# # Locations I can't quite figure out why I'd want to update locations or how that would work in the game play. I think it's smarter to just delete and regenerate locations. Saves space and time.
#
# @bp.put("/locations/<int:location_id>", strict_slashes=False)
# def update_location(location_id):
#     location = validate_model(Location, location_id)

#     request_body = request.get_json()

#     try:
#         location.name = request_body.get('name', location.name)
#         location.start_latitude = request_body.get('start_latitude', location.start_latitude)
#         location.start_longitude = request_body.get('start_longitude', location.start_longitude)
#         location.description = request_body.get('description', location.description)
#         location.clues = request_body.get('clues', location.clues)

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
