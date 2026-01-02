from flask import Flask, request, send_file, render_template, redirect, url_for, session
import os
import yt_dlp
from pymongo import MongoClient
from basic_pitch.inference import predict_and_save
from basic_pitch import ICASSP_2022_MODEL_PATH
import pretty_midi
from clean_midi_v2.entry import clean_midi_v2
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret_guitar_key" # 세션 보안키

# --- [MongoDB 설정] ---
# 사용자님의 주소를 여기에 넣었습니다. <db_password> 부분만 실제 비밀번호로 바꿔주세요.
MONGO_URI = "mongodb+srv://gomusin2022_db_user:<db_password>@cluster0.ka4r3um.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['guitar_ai_db']
users_collection = db['users']

# --- [파일 경로 설정] ---
INPUT_AUDIO = "input_audio.mp3"
GENERATED_MIDI = "input_audio_basic_pitch.mid"
OUTPUT_MIDI = "final_output.mid"

@app.route('/')
def index():
    if 'user' in session:
        return f"안녕하세요 {session['user']}님! <br> <a href='/convert'>변환하러 가기</a> | <a href='/logout'>로그아웃</a>"
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users_collection.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['user'] = username
            return redirect(url_for('convert_page'))
        return "로그인 실패!"
    return '''
        <form method="post">
            아이디: <input type="text" name="username"><br>
            비밀번호: <input type="password" name="password"><br>
            <input type="submit" value="로그인">
        </form>
        <p>계정이 없으신가요? <a href="/register">회원가입</a></p>
    '''

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if users_collection.find_one({'username': username}):
            return "이미 존재하는 아이디입니다."
        users_collection.insert_one({'username': username, 'password': password})
        return "가입 성공! <a href='/login'>로그인하기</a>"
    return '''
        <form method="post">
            가입할 아이디: <input type="text" name="username"><br>
            가입할 비밀번호: <input type="password" name="password"><br>
            <input type="submit" value="회원가입">
        </form>
    '''

@app.route('/convert')
def convert_page():
    if 'user' not in session: return redirect(url_for('login'))
    return '''
        <h2>유튜브 링크로 악보 만들기</h2>
        <form action="/convert-yt" method="post">
            유튜브 URL: <input type="text" name="url" style="width:300px;">
            <input type="submit" value="악보 변환 시작">
        </form>
    '''

@app.route('/convert-yt', methods=['POST'])
def convert_yt():
    if 'user' not in session: return "로그인 필요", 401
    url = request.form.get('url')
    
    # 1. 유튜브 다운로드
    ydl_opts = {'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}], 'outtmpl': 'input_audio'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    # 2. AI 분석 및 MIDI 생성
    predict_and_save([INPUT_AUDIO], ".", save_midi=True, model_or_model_path=ICASSP_2022_MODEL_PATH)
    
    # 3. MIDI 정제
    midi_data = pretty_midi.PrettyMIDI(GENERATED_MIDI)
    clean_midi_v2(midi_data, OUTPUT_MIDI)
    
    return send_file(OUTPUT_MIDI, as_attachment=True)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)