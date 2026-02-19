# 🎡 OurNoliter.com

Streamlit과 Firebase를 결합한 커뮤니티 플랫폼입니다. 누구나 자신만의 '놀이터(게시판)'를 만들고, 다양한 주제로 글을 쓰며 소통할 수 있는 공간입니다.

## ✨ 주요 기능

- **실시간 게시판 시스템**: 사용자가 직접 놀이터를 생성하고 관리할 수 있습니다.
- **게시글 및 댓글**: 이미지 포함 게시글 작성, 추천(👍/👎), 댓글 및 하트(❤️) 기능.
- **어드민 전용 관리 도구**: 
  - **유저 리스트 확인**: 가입된 전체 유저 목록을 별도 창에서 확인.
  - **유저 관리**: 어드민 계정(`hoodman10@yahoo.com`)으로 로그인 시 유저 삭제 기능 활성화.
  - **게시판 제어**: 부적절한 게시글 및 놀이터 삭제 권한.
- **사용자 편의**: 
  - **아이디 저장**: 쿠키를 이용한 자동 이메일 입력 기능.
  - **아코디언 디자인**: 게시글 제목을 클릭하면 내용이 펼쳐지는 깔끔한 UI.
- **보안**: Firebase Authentication을 통한 안전한 사용자 관리.

## 🛠 기술 스택

- **Frontend/Backend**: Streamlit
- **Database**: Google Cloud Firestore (NoSQL)
- **Authentication**: Firebase Auth
- **State Management**: Streamlit Session State & Cookies

## 🚀 시작하기
https://ournoliter.streamlit.app/
