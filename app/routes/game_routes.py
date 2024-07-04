
from flask import Blueprint, jsonify, request, abort, make_response
from ..db import db
from ..models.location import Location
from ..models.user_input import UserInput
from sqlalchemy import func, union, except_
from openai import OpenAI
import os


bp = Blueprint("tours", __name__, url_prefix="/tours")

client = OpenAI(
    api_key=os.environ.get("LLAMA_API_KEY"),
    base_url="https://api.llama-api.com"
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

@bp.post("/<char_id>/generate_locations", strict_slashes=False)
def add_locations(char_id):
    user_input = validate_model(UserInput, char_id)
    
    # Check if locations have already been generated
    if user_input.locations:
        return make_response(jsonify(f"Locations already generated for {user_input.id}"), 201)

    # Generate new locations
    locations = generate_locations(user_input)
    
    if not locations:
        return make_response(jsonify("Failed to generate locations"), 500)

    # Add new locations to the database
    try:
        db.session.add_all(locations)
        db.session.commit()
    except Exception as e:
        db.session.rollback()  # Rollback changes if an error occurs
        return make_response(jsonify(f"Failed to add locations: {str(e)}"), 500)

    return make_response(jsonify(f"Locations successfully added to {user_input.id}"), 201)


def generate_locations(user_input):
    game_prompts = {
        'Historical Quest': f"Generate a set of {user_input.num_sites} historical locations within {user_input.distance} square miles of ({user_input.latitude}, {user_input.longitude}). Provide the name, a brief description, and a clue for each location. Do not respond with an intro, do not waste tokens, only give me the info I'm requesting and nothing from you.",
        'Nature Walk': f"Generate a set of {user_input.num_sites} natural locations within {user_input.distance} square miles of ({user_input.latitude}, {user_input.longitude}). Provide the name, a brief description, and a clue for each location. Do not respond with an intro, do not waste tokens, only give me the info I'm requesting and nothing from you.",
        'Urban Adventure': f"Generate a set of {user_input.num_sites} urban locations within {user_input.distance} square miles of ({user_input.latitude}, {user_input.longitude}). Provide the name, a brief description, and a clue for each location. Do not respond with an intro, do not waste tokens, only give me the info I'm requesting and nothing from you.",
        'Mystery Solver': f"Generate a set of {user_input.num_sites} mysterious locations within {user_input.distance} square miles of ({user_input.latitude}, {user_input.longitude}). Provide the name, a brief description, and a clue for each location. Do not respond with an intro, do not waste tokens, only give me the info I'm requesting and nothing from you.",
        'Photo Hunt': f"Generate a set of {user_input.num_sites} picturesque locations within {user_input.distance} square miles of ({user_input.latitude}, {user_input.longitude}). Provide the name, a brief description, and a clue for each location. Do not respond with an intro, do not waste tokens, only give me the info I'm requesting and nothing from you.",
        'Exercise Challenge': f"Generate a set of {user_input.num_sites} locations suitable for an exercise challenge within {user_input.distance} square miles of ({user_input.latitude}, {user_input.longitude}). Provide the name, a brief description, and a clue for each location. Do not respond with an intro, do not waste tokens, only give me the info I'm requesting and nothing from you.",
        'Landmark Discovery': f"Generate a set of {user_input.num_sites} landmark locations within {user_input.distance} square miles of ({user_input.latitude}, {user_input.longitude}). Provide the name, a brief description, and a clue for each location. Do not respond with an intro, do not waste tokens, only give me the info I'm requesting and nothing from you.",
        'Art Walk': f"Generate a set of {user_input.num_sites} artistic locations within {user_input.distance} square miles of ({user_input.latitude}, {user_input.longitude}). Provide the name, a brief description, and a clue for each location. Do not respond with an intro, do not waste tokens, only give me the info I'm requesting and nothing from you.",
        'Puzzle Quest': f"Generate a set of {user_input.num_sites} locations suitable for a puzzle quest within {user_input.distance} square miles of ({user_input.latitude}, {user_input.longitude}). Provide the name, a brief description, and a clue for each location. Do not respond with an intro, do not waste tokens, only give me the info I'm requesting and nothing from you.",
        'Foodie Trail': f"Generate a set of {user_input.num_sites} locations suitable for a foodie trail within {user_input.distance} square miles of ({user_input.latitude}, {user_input.longitude}). Provide the name, a brief description, and a clue for each location. Do not respond with an intro, do not waste tokens, only give me the info I'm requesting and nothing from you."
    }

    input_message: str = game_prompts[user_input.game_type]

    chat_completion_object = client.chat.completions.create(
        model="llama3-70b",
        messages=[
            {"role": "user", "content": input_message}
        ]
    )
   
    rtrn_stmt = chat_completion_object.choices[0].message.content
    
    # Assuming the response is a string representation of a list, we need to convert it to an actual list
    # Example response: '["greeting1", "greeting2", "greeting3"]'
    greetings_list = eval(rtrn_stmt)  # eval is used to convert string representation of list to an actual list
    return greetings_list


        


def validate_model(cls, id):
    try:
        id = int(id)
    except ValueError:
        abort(make_response({"message": f"{cls.__name__} {id} invalid"}, 400))

    model = cls.query.get(id)
    if not model:
        abort(make_response({"message": f"{cls.__name__} {id} not found"}, 404))

    return model
