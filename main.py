from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3

from config import Config

from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
app.config.from_object(Config)
secret_key = app.config['SECRET_KEY']
def get_player_names():
    try:
        conn = sqlite3.connect('nba_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT Player FROM filtered_data")
        player_names = [row[0] for row in cursor.fetchall()]
        conn.close()
        return player_names
    except Exception as e:
        print("Error retrieving player names:", e)
        return []

def get_random_player_name():
    if 'random_player_info' not in session:
        conn = sqlite3.connect('nba_data.db')  
        cursor = conn.cursor()
        cursor.execute("SELECT Player FROM filtered_data ORDER BY RANDOM() LIMIT 1")
        random_player_name = cursor.fetchone()[0] 
        session['random_player_info'] = [random_player_name]
        conn.close()
    return session['random_player_info'][0]

def get_player_info(player_name):
    conn = sqlite3.connect('nba_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM filtered_data WHERE Player=?", (player_name,))
    player_info = cursor.fetchone()
    conn.close()
    return player_info

def get_random_player_info():
    if 'random_player_info' not in session:
        conn = sqlite3.connect('nba_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM filtered_data ORDER BY RANDOM() LIMIT 1")
        random_player_info = cursor.fetchone()  
        session['random_player_info'] = random_player_info
        conn.close()
    return session['random_player_info']
def process_player_info(players_info, random_player_info):
    processed_players_info = []
    jersey_number_index = 7 
    age_index = 6  
    height_index = 4  
    position_index = 5
    def height_to_inches(height_str):
        feet, inches = map(int, height_str.split('-'))
        return feet * 12 + inches
    
    for idx, player_info in enumerate(players_info):
        processed_player_info = []
        if player_info:
            for i, attribute in enumerate(player_info):
                match = '' 
                arrow = ''
                if i in [jersey_number_index, age_index]:
                    try:
                        guess_value = int(attribute)
                        correct_value = int(random_player_info[i])
                        if guess_value == correct_value:
                            match = 'green'
                        elif abs(guess_value - correct_value) <= 2:
                            match = 'yellow'
                            arrow = '↑' if guess_value < correct_value else '↓'
                        else:
                            arrow = '↑' if guess_value < correct_value else '↓'
                    except (ValueError, TypeError) as e:
                        print(f"Error processing attribute at index {i}: {e}")
                elif i == height_index:
                    try:
                        guess_height_in_inches = height_to_inches(attribute)
                        correct_height_in_inches = height_to_inches(random_player_info[i])
                        if guess_height_in_inches == correct_height_in_inches:
                            match = 'green'
                        elif abs(guess_height_in_inches - correct_height_in_inches) <= 2:
                            match = 'yellow'
                            arrow = '↑' if guess_height_in_inches < correct_height_in_inches else '↓'
                        else:
                            arrow = '↑' if guess_height_in_inches < correct_height_in_inches else '↓'
                    except (ValueError, TypeError) as e:
                        print(f"Error processing height: {e}")
                elif i == position_index:
                    correct_positions = set(random_player_info[i].split('-'))
                    guessed_positions = set(attribute.split('-'))
                    if guessed_positions == correct_positions:
                        match = 'green'
                    elif guessed_positions & correct_positions:
                        match = 'yellow'
                    
                else:
                    attribute_match = attribute == random_player_info[i]
                    if attribute_match:
                        match = 'green'
                if arrow:
                    attribute_with_arrow = f"{attribute} {arrow}"
                else:
                    attribute_with_arrow = attribute
                
                processed_player_info.append((attribute_with_arrow, match))
        else:
            processed_player_info = [(None, '')] * len(random_player_info)
        
        processed_players_info.append(processed_player_info)
      
    return processed_players_info

@app.route('/', methods=['GET', 'POST'])
def index():
    player_names = get_player_names()
    congrats_message = session.pop('congrats_message', None) 
    game_over = session.get('game_over', False)
    random_player_info = get_random_player_info()

    if request.method == 'POST':
        if 'reset_random_player' in request.form:
            session.pop('random_player_info', None)
            session['players_info'] = []
            session['game_over'] = False
            session.pop('congrats_message', None)
            return redirect(url_for('index'))  
        else:
            search_query = request.form.get('search_query')
            player_info = get_player_info(search_query)
            if player_info and len(session.get('players_info', [])) < 8 and not game_over:
                session.setdefault('players_info', []).append(player_info)
                player = player_info
                if player == random_player_info:
                    congrats_message = "Congratulations! You guessed the correct player."
                    session['congrats_message'] = congrats_message
                    session['game_over'] = True
                session.modified = True
                if len(session.get('players_info', [])) == 8 and not game_over:
                    congrats_message = "You failed. Better luck next time!"
                    session['congrats_message'] = congrats_message
                    session['game_over'] = True

        return redirect(url_for('index'))

    players_info = session.get('players_info', []) + [None] * (8 - len(session.get('players_info', [])))
    processed_players_info = process_player_info(players_info, random_player_info)

    return render_template('index.html', players_info=processed_players_info, player_names=player_names,
                           random_player_info=random_player_info, congrats_message=congrats_message, game_over=game_over)

if __name__ == '__main__':
    app.run(debug=True)
