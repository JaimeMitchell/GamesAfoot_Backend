
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
  organization='org-fcykkab8msT5mAV96whSHaeI'
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
            "location clue": location.clue
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

def generate_locations(user_input):
    game_prompts = {
    'Historical Quest': f"Generate a JSON array of {user_input.num_sites} historical locations within {user_input.distance} square miles of ({user_input.latitude}, {user_input.longitude}). Each object should include a string data type for 'name', 'latitude', 'longitude', 'description', and 'clue'.",
    'Nature Walk': f"Generate a JSON array of {user_input.num_sites} natural locations within {user_input.distance} square miles of ({user_input.latitude}, {user_input.longitude}). Each object should include a string data type for 'name', 'latitude', 'longitude', 'description', and 'clue'.",
    'Urban Adventure': f"Generate a JSON array of {user_input.num_sites} urban locations within {user_input.distance} square miles of ({user_input.latitude}, {user_input.longitude}). Each object should include a string data type for 'name', 'latitude', 'longitude', 'description', and 'clue'.",
    'Mystery Solver': f"Generate a JSON array of {user_input.num_sites} mysterious locations within {user_input.distance} square miles of ({user_input.latitude}, {user_input.longitude}). Each object should include a string data type for 'name', 'latitude', 'longitude', 'description', and 'clue'.",
    'Photo Hunt': f"Generate a JSON array of {user_input.num_sites} picturesque locations within {user_input.distance} square miles of ({user_input.latitude}, {user_input.longitude}). Each object should include a string data type for 'name', 'latitude', 'longitude', 'description', and 'clue'.",
    'Exercise Challenge': f"Generate a JSON array of {user_input.num_sites} locations suitable for an exercise challenge within {user_input.distance} square miles of ({user_input.latitude}, {user_input.longitude}). Each object should include a string data type for 'name', 'latitude', 'longitude', 'description', and 'clue'.",
    'Landmark Discovery': f"Generate a JSON array of {user_input.num_sites} landmark locations within {user_input.distance} square miles of ({user_input.latitude}, {user_input.longitude}). Each object should include a string data type for 'name', 'latitude', 'longitude', 'description', and 'clue'.",
    'Art Walk': f"Generate a JSON array of {user_input.num_sites} artistic locations within {user_input.distance} square miles of ({user_input.latitude}, {user_input.longitude}). Each object should include a string data type for 'name', 'latitude', 'longitude', 'description', and 'clue'.",
    'Puzzle Quest': f"Generate a JSON array of {user_input.num_sites} locations suitable for a puzzle quest within {user_input.distance} square miles of ({user_input.latitude}, {user_input.longitude}). Each object should include a string data type for 'name', 'latitude', 'longitude', 'description', and 'clue'.",
    'Foodie Trail': f"Generate a JSON array of {user_input.num_sites} locations suitable for a foodie trail within {user_input.distance} square miles of ({user_input.latitude}, {user_input.longitude}). Each object should include a string data type for 'name', 'latitude', 'longitude', 'description', and 'clue'."
}


    input_message = game_prompts[user_input.game_type]

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": input_message}
        ]
    )
   
    print(f'completion response from generate_greetings method: {completion.choices[0].message.content}')
    rtrn_stmt = completion.choices[0].message.content
    return rtrn_stmt
    # try:
    #     location_list = json.loads(rtrn_stmt)  # Parse JSON response into a Python list
    # except json.JSONDecodeError as e:
    #     return []  # Handle the case where JSON decoding fails

    # return location_list
        


def validate_model(cls, id):
    try:
        id = int(id)
    except ValueError:
        abort(make_response({"message": f"{cls.__name__} {id} invalid"}, 400))

    model = cls.query.get(id)
    if not model:
        abort(make_response({"message": f"{cls.__name__} {id} not found"}, 404))

    return model
