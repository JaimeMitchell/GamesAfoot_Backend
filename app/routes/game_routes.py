from flask import Blueprint, jsonify, request, abort, make_response
from ..db import db
from ..models.location import Location
from ..models.user_input import UserInput
from sqlalchemy import func, union, except_
from openai import OpenAI
import os

bp = Blueprint("tours", __name__, url_prefix="/tours")
client = OpenAI(
api_key = os.environ.get("LLAMA_API_KEY"),
base_url = "https://api.llama-api.com"
)


@bp.post("", strict_slashes=False)
def create_user_input():

    request_body = request.get_json()
    print(request_body)
    try: 
        new_user_input = UserInput.from_dict(request_body)
        print(new_user_input)
        db.session.add(new_user_input)
        db.session.commit()

        return make_response(new_user_input.to_dict(), 201)
    
    except KeyError as e:
        abort(make_response({"message": f"missing required value: {e}"}, 400))

@bp.get("", strict_slashes=False)
def get_user_inputs():
    user_input_query = db.select(UserInput)

    user_inputs = db.session.scalars(user_input_query)
    response = []

    for user_input in user_inputs:
        response.append(
            {
                "id" : user_input.id,
                "latitude" : user_input.latitude,
                "longitude" : user_input.longitude,
                "distance" : user_input.distance,
                "num_sites" : user_input.num_sites,
                "game_type" : user_input.game_type
            }
        )

    return jsonify(response)

@bp.get("/<char_id>/user_input", strict_slashes=False)
def get_user_input(char_id):
    user_input = validate_model(UserInput, char_id)
    
    if not user_input.locations:
        return make_response(jsonify(f"No locations found for {user_input.id} "), 201)
    
    response = {"User_Input_Id" : user_input.id,
                "Locations" : []}
    for location in user_input.locations:
        response["Locations"].append({
            "location name": location.name,
            "location lat" : location.latitude,
            "location long": location.longitude,
            "location description": location.description,
            "location clue": location.clue
        })
    
    return jsonify(response)

@bp.post("/<char_id>/generate_locations", strict_slashes=False)
def add_locations(char_id):
    user_input = validate_model(UserInput, char_id)
    locations = generate_locations(user_input)
    
    # Print each location on its own separate line
    for location in locations:
        print(location)

    if user_input.locations:
        return make_response(jsonify(f"Locations already generated for {user_input.name}"), 201)
    
    new_locations = []

    for location in locations:
        new_location = Location(
            name = location["name"],
            user_input = user_input
        )
        new_locations.append(new_location)
    
    db.session.add_all(new_locations)
    db.session.commit()

    return make_response(jsonify(f"Locations successfully added to {user_input.name}"), 201)


def generate_locations(user_input):
    game_prompts = {
    'Historical Quest': f"Generate a set of {user_input.num_sites} historical locations within {user_input.distance} of ({user_input.latitude}, {user_input.longitude}). Provide coordinates, a brief description, and a clue for each location.",
    'Nature Walk': f"Generate a set of {user_input.num_sites} natural locations within {user_input.distance} of ({user_input.latitude}, {user_input.longitude}). Provide coordinates, a brief description, and a clue for each location.",
    'Urban Adventure': f"Generate a set of {user_input.num_sites} urban locations within {user_input.distance} of ({user_input.latitude}, {user_input.longitude}). Provide coordinates, a brief description, and a clue for each location.",
    'Mystery Solver': f"Generate a set of {user_input.num_sites} mysterious locations within {user_input.distance} of ({user_input.latitude}, {user_input.longitude}). Provide coordinates, a brief description, and a clue for each location.",
    'Photo Hunt': f"Generate a set of {user_input.num_sites} picturesque locations within {user_input.distance} of ({user_input.latitude}, {user_input.longitude}). Provide coordinates, a brief description, and a clue for each location.",
    'Exercise Challenge': f"Generate a set of {user_input.num_sites} locations suitable for an exercise challenge within {user_input.distance} of ({user_input.latitude}, {user_input.longitude}). Provide coordinates, a brief description, and a clue for each location.",
    'Landmark Discovery': f"Generate a set of {user_input.num_sites} landmark locations within {user_input.distance} of ({user_input.latitude}, {user_input.longitude}). Provide coordinates, a brief description, and a clue for each location.",
    'Art Walk': f"Generate a set of {user_input.num_sites} artistic locations within {user_input.distance} of ({user_input.latitude}, {user_input.longitude}). Provide coordinates, a brief description, and a clue for each location.",
    'Puzzle Quest': f"Generate a set of {user_input.num_sites} locations suitable for a puzzle quest within {user_input.distance} of ({user_input.latitude}, {user_input.longitude}). Provide coordinates, a brief description, and a clue for each location.",
    'Foodie Trail': f"Generate a set of {user_input.num_sites} locations suitable for a foodie trail within {user_input.distance} of ({user_input.latitude}, {user_input.longitude}). Provide coordinates, a brief description, and a clue for each location."
}
    input_message = {game_prompts[user_input.game_type]}
    print(input_message)

    chat_completion_object = client.chat.completions.create(
        model="llama3-70b",
        messages=[
            {"role": "user", "content": input_message}
        ]
    )
    print(chat_completion_object.choices[0].message.content)
    rtrn_stmt = chat_completion_object.choices[0].message.content
    
    # Assuming the response is a string representation of a list, we need to convert it to an actual list
    # Example response: '["location1", "location2", "location3"]'
    locations_list = eval(rtrn_stmt)  # eval is used to convert string representation of list to an actual list
    return locations_list



def validate_model(cls,id):
    try:
        id = int(id)
    except:
        response =  response = {"message": f"{cls.__name__} {id} invalid"}
        abort(make_response(response , 400))

    query = db.select(cls).where(cls.id == id)
    model = db.session.scalar(query)
    if model:
        return model

    response = {"message": f"{cls.__name__} {id} not found"}
    abort(make_response(response, 404))