# 실행 스크립트:  PowerShell에서  .\run.ps1

# 인증: 시스템에 등록된 사용자 환경 변수 GOOGLE_APPLICATION_CREDENTIALS 를 자동으로 사용합니다.
# (등록 방법 - 한 번만 실행 후 터미널 재시작)
#   [Environment]::SetEnvironmentVariable("GOOGLE_APPLICATION_CREDENTIALS", "본인_키_경로.json", "User")
#
# 환경 변수를 등록하지 않았다면, 아래 주석을 풀고 본인 키 경로로 바꿔서 쓰세요.
# $env:GOOGLE_APPLICATION_CREDENTIALS = "D:\GCP_Api.json"

# (선택) 리전. 기본 global 권장. 필요시 us-central1 등으로 변경
$env:GOOGLE_CLOUD_LOCATION = "global"

# (선택) 프로젝트 ID. 비워두면 위 JSON 키에서 자동으로 읽음
# $env:GOOGLE_CLOUD_PROJECT = "your-project-id"

python -m streamlit run src\app.py
