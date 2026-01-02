# 1. 가볍고 안정적인 Python 3.9 이미지 사용
FROM python:3.9-slim-bookworm

# 2. 환경 변수 설정
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# 3. 시스템 의존성 패키지 설치
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# 4. 파이썬 라이브러리 설치
# yt-dlp: 유튜브 다운로드 기능을 위해 추가
RUN pip install --no-cache-dir \
    flask \
    "basic-pitch[tf]" \
    numpy \
    soundfile \
    pretty_midi \
    yt-dlp

# 5. 작업 디렉토리 설정 및 소스 코드 복사
WORKDIR /app
COPY . .

# 6. 포트 노출
EXPOSE 5000

# 7. 서버 실행
CMD ["python", "convert.py"]