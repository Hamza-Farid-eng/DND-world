from flask import Flask, render_template, request, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import time

app = Flask(__name__)
app.secret_key = 'dnd_multiplayer_secret'
socketio = SocketIO(app)

players = {}
games = {}

class Game:
    def __init__(self, id, player1_name, player1_class):
        self.id = id
        self.players = {}
        self.players[player1_name] = {
            'class': player1_class,
            'hp': self._calc_hp(player1_class),
            'max_hp': None,
            'ac': 10
        }
        self.turn = player1_name
        self.message_log = []
        self._init_max_hp()

    def _calc_hp(self, char_class):
        if char_class == "fighter":
            return random.randint(10, 12)
        elif char_class == "wizard":
            return random.randint(6, 8)
        elif char_class == "rogue":
            return random.randint(6, 8)
        else:
            return random.randint(8, 10)

    def _init_max_hp(self):
        for name, p in self.players.items():
            if self.max_hp is None:
                self.max_hp = p['hp']
            else:
                self.max_hp = min(self.max_hp, p['hp'])

    def join(self, name, char_class):
        if name not in self.players and len(self.players) < 4:
            self.players[name] = {
                'class': char_class,
                'hp': self._calc_hp(char_class),
                'max_hp': None,
                'ac': 10
            }
            self._init_max_hp()
            return True
        return False

    def take_turn(self, actor, action, target=None):
        if self.turn != actor:
            return False, "Not your turn!"

        if action == "attack":
            damage = random.randint(1, 8) + self.players[actor]['class'] in ['fighter', 'rogue'] * 2
            target_data = self.players.get(target, {'hp': 0})
            target_data['hp'] -= damage
            self.players[target] = target_data
            msg = f"{actor} attacks {target} for {damage} damage!"
            if target_data['hp'] <= 0:
                msg += f" {target} is defeated!"
                del self.players[target]
                if len(self.players) <= 1:
                    msg += " Victory!"
            self.message_log.append(msg)
            self._switch_turn()
            return True, msg

        elif action == "heal":
            heal_amount = 10
            self.players[actor]['hp'] = min(self.players[actor]['max_hp'], 
                                           self.players[actor]['hp'] + heal_amount)
            msg = f"{actor} heals for {heal_amount} HP!"
            self.message_log.append(msg)
            self._switch_turn()
            return True, msg

        return False, "Invalid action"

    def _switch_turn(self):
        names = list(self.players.keys())
        current_idx = names.index(self.turn)
        next_idx = (current_idx + 1) % len(names)
        self.turn = names[next_idx]

    def get_state(self):
        return {
            'turn': self.turn,
            'players': {n: {'class': p['class'], 'hp': p['hp'], 'max_hp': p['max_hp']} 
                       for n, p in self.players.items()},
            'messages': self.message_log[-5:]
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_game', methods=['POST'])
def create_game():
    name = request.form['name']
    char_class = request.form['class'].lower()
    if char_class not in ['fighter', 'wizard', 'rogue']:
        return jsonify({'error': 'Invalid class'}), 400
    
    game_id = str(random.randint(1000, 9999))
    while game_id in games:
        game_id = str(random.randint(1000, 9999))
    
    games[game_id] = Game(game_id, name, char_class)
    session['game_id'] = game_id
    session['name'] = name
    session['class'] = char_class
    join_room(game_id)
    return jsonify({'game_id': game_id, 'success': True})

@app.route('/join_game', methods=['POST'])
def join_game():
    name = request.form['name']
    char_class = request.form['class'].lower()
    game_id = request.form.get('game_id', '')
    
    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404
    
    if not games[game_id].join(name, char_class):
        return jsonify({'error': 'Game full or name taken'}), 400
    
    session['game_id'] = game_id
    session['name'] = name
    session['class'] = char_class
    join_room(game_id)
    return jsonify({'game_id': game_id, 'success': True, 'players': list(games[game_id].players.keys())})

@app.route('/action', methods=['POST'])
def action():
    data = request.get_json()
    game_id = session.get('game_id')
    name = session.get('name')
    
    if not game_id or not name or game_id not in games:
        return jsonify({'error': 'Not in a game'}), 400
    
    success, message = games[game_id].take_turn(name, data['action'], data.get('target'))
    socketio.emit('game_state', games[game_id].get_state(), room=game_id)
    
    return jsonify({'success': success, 'message': message, 'state': games[game_id].get_state()})

@socketio.on('connect')
def handle_connect():
    game_id = session.get('game_id')
    if game_id and game_id in games:
        join_room(game_id)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)