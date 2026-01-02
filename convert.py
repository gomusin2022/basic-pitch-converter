from flask import Flask, request, send_file, render_template_string, redirect, url_for, session
import os
import time
import yt_dlp
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from basic_pitch.inference import predict_and_save
from basic_pitch import ICASSP_2022_MODEL_PATH
import pretty_midi
from clean_midi_v2.entry import clean_midi_v2

app = Flask(__name__)
app.secret_key = "guitar_ai_key_2026" # 세션 유지를 위한 키

# --- [1. MongoDB 설정] ---
# <db_password>를 어제 설정한 실제 비번으로 바꾸세요.
MONGO_URI = "mongodb+srv://gomusin2022_db_user:<tkfkdgo12!@>@cluster0.ka4r3um.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['guitar_ai_db']
users_collection = db['users']

# 파일 경로 상수화
INPUT_AUDIO = "input_audio.mp3"
GENERATED_MIDI = "input_audio_basic_pitch.mid"
OUTPUT_MIDI = "final_output.mid"

# --- [2. 핵심 로직: 기존 기능 유지] ---

def process_transcription():
    """채보 및 정제 로직 (기존 유지)"""
    for p in [GENERATED_MIDI, OUTPUT_MIDI]:
        if os.path.exists(p): os.remove(p)

    predict_and_save(
        audio_path_list=[INPUT_AUDIO],
        output_directory=".",
        save_midi=True,
        sonify_midi=False,
        save_model_outputs=False,
        save_notes=False,
        model_or_model_path=ICASSP_2022_MODEL_PATH
    )
    
    if not os.path.exists(GENERATED_MIDI):
        return None

    midi_data = pretty_midi.PrettyMIDI(GENERATED_MIDI)
    success = clean_midi_v2(midi_data, OUTPUT_MIDI)
    return OUTPUT_MIDI if (success and os.path.exists(OUTPUT_MIDI)) else None

def download_from_yt(url):
    """유튜브에서 MP3 추출 (기존 유지)"""
    if os.path.exists(INPUT_AUDIO): os.remove(INPUT_AUDIO)
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
        'outtmpl': 'input_audio',
        'noplaylist': True,
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return INPUT_AUDIO

# --- [3. 사용자 관리 및 웹 화면] ---

@app.route('/')
def index():
    if 'user' in session:
        return render_template_string('''
            <h2>🎸 AI 기타 채보 서버</h2>
            <p>환영합니다, <b>{{ session['user'] }}</b>님!</p>
            <hr>
            <h3>1. 유튜브 링크로 변환</h3>
            <form action="/convert-yt" method="post">
                URL: <input type="text" name="url" placeholder="유튜브 주소" style="width:300px;">
                <input type="submit" value="변환 시작">
            </form>
            <br>
            <h3>2. MP3 파일 업로드로 변환</h3>
            <form action="/convert-mp3" method="post" enctype="multipart/form-data">
                <input type="file" name="file">
                <input type="submit" value="업로드 및 변환">
            </form>
            <br><hr>
            <a href="/logout">로그아웃</a>
        ''')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if users_collection.find_one({'username': username}):
            return "이미 있는 아이디입니다. <a href='/register'>다시 시도</a>"
        users_collection.insert_one({'username': username, 'password': password})
        return "가입 성공! <a href='/login'>로그인하기</a>"
    return '<h2>회원가입</h2><form method="post">아이디: <input name="username"><br>비번: <input type="password" name="password"><br><input type="submit" value="가입"></form>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = users_collection.find_one({'username': request.form['username']})
        if user and check_password_hash(user['password'], request.form['password']):
            session['user'] = user['username']
            return redirect(url_for('index'))
        return "로그인 실패! <a href='/login'>다시 시도</a>"
    return '<h2>로그인</h2><form method="post">아이디: <input name="username"><br>비번: <input type="password" name="password"><br><input type="submit" value="로그인"></form><p>계정이 없으신가요? <a href="/register">회원가입</a></p>'

@app.route('/convert-yt', methods=['POST'])
def convert_yt_web():
    if 'user' not in session: return redirect(url_for('login'))
    url = request.form.get('url')
    try:
        download_from_yt(url)
        result_path = process_transcription()
        return send_file(result_path, as_attachment=True) if result_path else "변환 실패"
    except Exception as e:
        return str(e), 500

@app.route('/convert-mp3', methods=['POST'])
def convert_mp3_web():
    if 'user' not in session: return redirect(url_for('login'))
    file = request.files.get('file')
    if not file or file.filename == '': return "파일 없음", 400
    file.save(INPUT_AUDIO)
    try:
        result_path = process_transcription()
        return send_file(result_path, as_attachment=True) if result_path else "변환 실패"
    except Exception as e:
        return str(e), 500

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)