from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_heroku import Heroku
from flask_bcrypt import Bcrypt
from mafia import *
import math
import random

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://skgtsmntcijlfj:006e324c08797f4bd5b07b0737cbdb94d570a8ab0cfa93f062a9b4211262a01a@ec2-54-234-44-238.compute-1.amazonaws.com:5432/d4p2608hahi3l6"

db = SQLAlchemy(app)
ma = Marshmallow(app)

heroku = Heroku(app)
CORS(app)
bcrypt = Bcrypt(app)

number_of_players = 0
mafia_count = 0
current_number_of_players = 0
current_mafia_count = 0
game_going = False
game = Game()
town = game.add_faction(Town())
mafia = game.add_faction(Mafia("Mafia"))


class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    userName = db.Column(db.String(20), nullable = False, unique = True)
    displayName = db.Column(db.String(20), nullable = False, unique = False)
    email = db.Column(db.String(), nullable = False, unique = True)
    password = db.Column(db.String(), nullable = False)

    def __init__(self, userName, displayName, email, password):
        self.userName = userName
        self.displayName = displayName
        self.email = email
        self.password = password

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "userName", "displayName", "email", "password")

user_schema = UserSchema()
users_schema = UserSchema(many = True)


# User API Endpoints

@app.route("/user/create", methods=['POST'])
def create_user():
    if request.content_type != "application/json":
        return jsonify("Error: Data must be sent as JSON")
    
    post_data = request.get_json()

    username = post_data.get("username")
    display_name = post_data.get("displayName")
    email = post_data.get("email")
    password = post_data.get("password")

    #is username used

    username_check = db.session.query(User.userName).filter(User.userName == username).first()
    if username_check is not None:
        return jsonify("Username is Taken")

    #is email used

    email_check = db.session.query(User.email).filter(User.email == email).first()
    if email_check is not None:
        return jsonify("Email is already used")
    
    hashed_password = bcrypt.generate_password_hash(password).decode("utf8")

    record = User(username, display_name, email, hashed_password)
    db.session.add(record)
    db.session.commit()

    return jsonify("Account created Successfully!")

@app.route("/user/get", methods=['GET'])
def get_all_users():
    all_users = db.session.query(User).all()
    return jsonify(users_schema.dump(all_users))

@app.route("/user/get/<id>", methods=['GET'])
def get_one_user(id):
    user = db.session.query(User).filter(User.id == id).first()
    return jsonify(user_schema.dump(user))

@app.route("/user/lookupByName/<name>", methods=['GET'])
def get_user_by_name(name):
    user = db.session.query(User).filter(User.userName == name).first()
    return jsonify(user_schema.dump(user))

@app.route("/user/lookupByEmail/<email>", methods=['GET'])
def get_user_by_email(email):
    user = db.session.query(User).filter(User.email == email).first()
    return jsonify(user_schema.dump(user))

@app.route("/user/verification", methods=['POST'])
def verify_user():
    if request.content_type != "application/json":
        return jsonify("Error: Data must be sent as JSON")
    
    post_data = request.get_json()
    username = post_data.get("username")
    email = post_data.get("email")
    password = post_data.get("password")


    if email is None:
        stored_password = db.session.query(User.password).filter(User.userName == username).first()
    
    if username is None:
        stored_password = db.session.query(User.password).filter(User.email == email).first()

    if stored_password is None:
        return jsonify("User NOT verified")

    valid_password_check = bcrypt.check_password_hash(stored_password[0], password)

    if valid_password_check == False:
        return jsonify("User NOT verified")

    return jsonify("User Verified")


@app.route("/user/logged_in", methods=['GET'])
def logged_in():
    if request.with_credentials == "true":
        return jsonify("With credentials!")
    else:
        return jsonify("Not with credentials!")


@app.route("/user/delete/<id>", methods=['DELETE'])
def delete_user(id):
    user_to_delete = db.session.query(User).filter(User.id == id).first()
    db.session.delete(user_to_delete)
    db.session.commit()
    return jsonify("User Deleted Successfully")

@app.route("/user/friends/lookupByUsername/<user>", methods=['GET'])
def find_friends(user):
    user = db.session.query(User).filter(User.userName == user).first()
    return jsonify(user_schema.dump(user))

# Game API Endpoints

number_of_players = 0

@app.route("/game/init", methods=['POST'])
def initialize_game():
    global number_of_players
    global game_going
    global mafia_count
    global current_number_of_players
    global current_mafia_count

    if number_of_players % 2 == 0 or number_of_players < 7:
        return jsonify(
            'You must have an odd number of players and there must be at least 7'
            )

    game_going = True    
    mafia_count = math.floor(number_of_players / 3)
    town_count = number_of_players - mafia_count

    current_number_of_players = town_count + mafia_count
    current_mafia_count = mafia_count







    # Guest1 = game.add_player("Doctor", Villager(town))
    # Guest2 = game.add_player("Cop", Cop(town))
    # Guest3 = game.add_player("Vigilante", Vigilante(town))
    # Guest4 = game.add_player("Godfather", Godfather(mafia))
    # Guest5 = game.add_player("Goon", Goon(mafia))

    # night0 = Night(0)
    # night0.add_action(Protect(aDoctor, aCop))
    # night0.add_action(FactionAction(mafia, Kill(aGodfather, aCop)))
    # night0.add_action(Investigate(aCop, aGoon))
    # night0.add_action(Kill(aVigilante, aGodfather))
    # game.resolve(night0)

    # print(game.log.phase(night0))

    # return jsonify(str(game.log.phase(night0)))

    return jsonify(f"There are {mafia_count} mafia and {town_count} townspeople")

@app.route('/game/get_role', methods=['GET'])
def get_role():
    global number_of_players
    global mafia_count
    global current_number_of_players
    global current_mafia_count


    if game_going == True:

        if current_number_of_players > 0:
            current_odds = current_mafia_count / current_number_of_players
            print(current_odds)
            random_number = random.random()
            print(random_number)

            if random_number < current_odds:
                current_mafia_count -= 1
                current_number_of_players -= 1
                print(f'{current_mafia_count} mafia & {current_number_of_players} players')
                return jsonify("You are Mafia") 
            else:
                current_number_of_players -= 1
                print(f'{current_mafia_count} mafia & {current_number_of_players} players')
                return jsonify("You are Villager")
        else:
            return jsonify("Out of Players!")
    else:
        return jsonify("Game is not going!")



@app.route('/game/enter', methods=['POST'])
def enter_game():
    global number_of_players

    if game_going == True:
        return jsonify("There is a game going!")

    number_of_players += 1
    print(number_of_players)
    return jsonify(f"Entered! You are player #{number_of_players}")

@app.route('/game/finish', methods=['DELETE'])
def finish_game():
    global game_going
    global number_of_players
    global mafia_count

    number_of_players = 0
    mafia_count = 0
    game_going = False
    return jsonify('Game is finished!')

@app.route('/game/exit', methods=['POST'])
def exit_game():
    global number_of_players
    global game_going

    if game_going == True:
        return jsonify("There is a game going! Finish it!")
    if number_of_players <= 0:
        return jsonify("There are no players in the match!")

    number_of_players -= 1    
    print(number_of_players)
    return jsonify("Exited!")

@app.route('/game/reset_players', methods=['DELETE'])
def reset_game():
    global number_of_players
    global game_going

    number_of_players = 0    
    print(number_of_players)
    return jsonify("Reset!")

@app.route('/game/ping', methods=['GET'])
def ping_game():
    global number_of_players
    global game_going

    if not game_going:
        if number_of_players % 2 == 0:
            print(number_of_players)
            return jsonify('Odd Number Required')
        else:
            if number_of_players < 7:
                print(number_of_players)
                return jsonify('Not enough players')
            else:
                return jsonify('Ready to start!')
        
    else:
        return jsonify('Game going!')



if __name__ == "__main__":
    app.run(debug=True)