# `Games Afoot AI!</h2>

## `Overview`

<h3>A customized AI tour guide and treasure hunting game at your fingertips. Anytime, anywhere, the game's afoot!</h3>
<p>
AI generated tour guide game in which the participants use their phone’s or computer’s location to generate a historical geocache tour in their surrounding area. I tested this out and it works. My last capstone involved mapping markers on React leaflet. I thought I’d revisit plotting markers but with AI. When the user's location marker == a the AI generated location then points are added and the next clue and location on the location list appears until the user has come to the final locaton.
MVP Feature Set
The user prompts with their location. They can give a distance they’d like to walk OR a number of sites they’d like to see in a predetermined area.
The request goes towards a text response first from llama/OpenAI
The response it a set of treasure hunt/scavenger hunt clues to go on this tour. If they can’t figure it out, it can be shown on the map via location markers, including their own realtime location. I would recycle some of the code from my WaterWitch project.
Stretch goal would be to click on each of these places when the users locate it and give a brief commentary on it’s history or fun facts.
Stretch goal 2: Eventually have plans to turn it into a dating/social app where a treasure hunt could be created between two player’s locations so that they find each other by the location clues provided. Yes, the UPDATE would absolutely need to be involved since a person could go off course and so new clues generated to get them back on-course towards the other/s.
"Go East" Getting direction prompts. A ping or visual or radius circle on the map, red if far, yellow if closer, green if closer, while trying to find it. Visual cues to help. Not just clue.
example user_input that is plugged into the AI prompt to get "a list of location" { "distance": "2", "game_type": "Historical Quest", "id": 1, "starting_latitude": "40.712776", "starting_longitude": "-74.005974", "num_sites": "3" },
NOTE "Starting Location" - User Location OR User Dictated and assigned. Gives user a choice between automatically dictating the starting point, or allowing user to.
Example of locations list . Example
Third model USER to tie location list and user_input. User model keeps track of user model or
Location Model and User model have to work together in order to update game play such as user marker changing color to dictate how close they are to location they are looking for, or when they find location user_location == cur_location.id the go to the next cur_loction = new_location.
<br/>
Written in React and Python as a Capstone Project at <a href='https://adadevelopersacademy.org/'>Ada Developers Academy.</a>
</h4>

<h2> App Link:
<a href='https://GamesAfoot.com/'>Games Afoot</a></h2>

</p>
<h3 align="left">Languages and Tools Used To Create This Project:</h3>
<p align="left"> <a href="https://flask.palletsprojects.com/" target="_blank" rel="noreferrer"> <img src="https://www.vectorlogo.zone/logos/pocoo_flask/pocoo_flask-icon.svg" alt="flask" width="40" height="40"/> </a> <a href="https://git-scm.com/" target="_blank" rel="noreferrer"> <img src="https://www.vectorlogo.zone/logos/git-scm/git-scm-icon.svg" alt="git" width="40" height="40"/> </a> <a href="https://heroku.com" target="_blank" rel="noreferrer"> <img src="https://www.vectorlogo.zone/logos/heroku/heroku-icon.svg" alt="heroku" width="40" height="40"/> </a> <a href="https://developer.mozilla.org/en-US/docs/Web/JavaScript" target="_blank" rel="noreferrer"> <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/javascript/javascript-original.svg" alt="javascript" width="40" height="40"/> </a> <a href="https://jestjs.io" target="_blank" rel="noreferrer"> <img src="https://www.vectorlogo.zone/logos/jestjsio/jestjsio-icon.svg" alt="jest" width="40" height="40"/> </a> <a href="https://www.postgresql.org" target="_blank" rel="noreferrer"> <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/postgresql/postgresql-original-wordmark.svg" alt="postgresql" width="40" height="40"/> </a> <a href="https://postman.com" target="_blank" rel="noreferrer"> <img src="https://www.vectorlogo.zone/logos/getpostman/getpostman-icon.svg" alt="postman" width="40" height="40"/> </a> <a href="https://www.python.org" target="_blank" rel="noreferrer"> <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg" alt="python" width="40" height="40"/> </a> <a href="https://reactjs.org/" target="_blank" rel="noreferrer"> <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/react/react-original-wordmark.svg" alt="react" width="40" height="40"/> </a> <a href="https://leafletjs.com/" target="_blank" rel="noreferrer"> <img src="https://www.svgrepo.com/show/353991/leaflet.svg" alt="leaflet" width="60" height="60"/> </a>
<a href="https://pandas.pydata.org/" target="_blank" rel="noreferrer"> <img src="https://seeklogo.com/images/P/pandas-logo-776F6D45BB-seeklogo.com.png" alt="Pandas" width="40" height="40"/> </a>
<a href="https://geopandas.org/en/stable/index.html" target="_blank" rel="noreferrer"> <img src="https://geopandas.org/en/stable/_images/geopandas_icon_green.png"
 alt="GeoPandas" width="40" height="40"/> </a></p>

## App Features"

- **Interactive Map** The page will load with all game location markers currently in the Database.. The database is seeded by data generated using AI LLM Models. Both Llama and OpenAI have been implemented and tested successfully.
- [**Desktop Version Only**] This will run on both desktop and phone but is not optimized for phone... yet.
- Map will automatically load your current location with geo-coordinates, unless you have your web browsers location turned off.
- **Menu** to navigate between Map, Instructions, Filters, Search Address, Game Type, Distance to walk, and number of sites user wants to generate in the game Form.
