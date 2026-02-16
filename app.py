import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import requests
from datetime import datetime, timedelta
import extra_streamlit_components as stx
import time

# --- 1. 설정 및 관리자 계정 ---
ADMIN_EMAIL = "hoodman10@yahoo.com"
DEFAULT_AVATAR = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
FIREBASE_WEB_API_KEY = st.secrets["firebase"].get("api_key")

# --- 2. Firebase 초기화 ---
if not firebase_admin._apps:
    try:
        cred_dict = dict(st.secrets["firebase"])
        cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"연결 오류: {e}")

db = firestore.client()

# --- 3. 쿠키 매니저 초기화 ---
cookie_manager = stx.CookieManager()

# --- 4. 비밀번호 검증 함수 ---
def verify_password(email, password):
    if not FIREBASE_WEB_API_KEY:
        st.error("API Key 미설정")
        return False
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    res = requests.post(url, json=payload)
    return res.status_code == 200

# --- 5. CSS 디자인 (OurNoliter.com 브랜딩) ---
st.set_page_config(page_title="OurNoliter.com", page_icon="🎡", layout="centered")
st.markdown("""
    <style>
    .main { background-color: #f0f2f5; }
    .stColumn > div { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }
    .hot-post-container { background-color: #fffbeb; border: 1px solid #fde68a; padding: 12px; border-radius: 10px; margin-bottom: 10px; }
    .hot-badge { background-color: #f59e0b; color: white; padding: 2px 8px; border-radius: 20px; font-size: 11px; font-weight: bold; margin-right: 8px; }
    .not-found-box { background-color: #fff4f4; padding: 20px; border-radius: 12px; border: 1px solid #ffcccc; margin-bottom: 25px; text-align: center; color: #d32f2f; font-weight: bold; }
    .admin-badge { background-color: #ff4b4b; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; margin-left: 5px; }
    .profile-img { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; margin-right: 10px; vertical-align: middle; border: 1px solid #ddd; }
    .playground-title { color: #003399; font-weight: bold; font-size: 26px; margin-bottom: 10px; border-bottom: 2px solid #003399; padding-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 세션 상태 초기화
if "user_info" not in st.session_state: st.session_state.user_info = None
if "current_playground" not in st.session_state: st.session_state.current_playground = "전체"
if "search_target" not in st.session_state: st.session_state.search_target = ""

# --- 6. 사이드바 (인증 & 저장 기능) ---
with st.sidebar:
    st.title("🌐 OurNoliter.com")
    
    # [개선] 쿠키 로딩 대기 및 읽기
    all_cookies = cookie_manager.get_all()
    if not all_cookies:
        time.sleep(0.1) # 0.1초 대기하여 브라우저 동기화 유도
        all_cookies = cookie_manager.get_all()

    c_email = all_cookies.get("saved_email", "")
    c_pw = all_cookies.get("saved_pw", "")

    if st.session_state.user_info is None:
        menu = st.tabs(["로그인", "회원가입"])
        with menu[0]:
            # autocomplete 옵션으로 브라우저 자동완성 보조
            l_email = st.text_input("이메일", value=c_email, key="l_em", autocomplete="email")
            l_pw = st.text_input("비밀번호", value=c_pw, type="password", key="l_pw", autocomplete="current-password")
            
            col1, col2 = st.columns(2)
            with col1: rem_id = st.checkbox("아이디 저장", value=bool(c_email))
            with col2: rem_pw = st.checkbox("비밀번호 저장", value=bool(c_pw))
            
            if st.button("로그인", use_container_width=True, type="primary"):
                if verify_password(l_email, l_pw):
                    user = auth.get_user_by_email(l_email)
                    st.session_state.user_info = {
                        "name": user.display_name, "email": user.email,
                        "photo": user.photo_url if user.photo_url else DEFAULT_AVATAR
                    }
                    # 쿠키 저장 (30일)
                    exp = datetime.now() + timedelta(days=30)
                    if rem_id: cookie_manager.set("saved_email", l_email, expires_at=exp)
                    else: cookie_manager.delete("saved_email")
                    if rem_pw: cookie_manager.set("saved_pw", l_pw, expires_at=exp)
                    else: cookie_manager.delete("saved_pw")
                    
                    st.success("로그인 중...")
                    time.sleep(0.5) # 쿠키 저장 시간 확보
                    st.rerun()
                else: st.error("로그인 정보가 틀렸습니다.")
        with menu[1]:
            nem, npw, nnk = st.text_input("이메일", key="r_em"), st.text_input("비밀번호", type="password", key="r_pw"), st.text_input("닉네임", key="r_nk")
            if st.button("회원가입", use_container_width=True):
                try:
                    auth.create_user(email=nem, password=npw, display_name=nnk)
                    st.success("가입 완료! 로그인 해주세요.")
                except Exception as e: st.error(f"실패: {e}")
    else:
        st.image(st.session_state.user_info['photo'], width=70)
        st.success(f"✅ {st.session_state.user_info['name']}님")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.user_info = None
            st.rerun()

    st.markdown("---")
    st.subheader("📁 놀이터 목록")
    if st.button("🏠 전체 메인 피드"):
        st.session_state.current_playground = "전체"
        st.rerun()
    
    pg_list = db.collection("playgrounds").order_by("created_at", direction=firestore.Query.DESCENDING).stream()
    existing_pgs = []
    for pg in pg_list:
        pg_name = pg.id
        existing_pgs.append(pg_name)
        c1, c2 = st.columns([0.8, 0.2])
        with c1:
            if st.button(f"🎡 {pg_name}", key=f"l_{pg_name}"):
                st.session_state.current_playground = pg_name
                st.rerun()
        with c2:
            if st.session_state.user_info and st.session_state.user_info['email'] == ADMIN_EMAIL:
                if st.button("🗑️", key=f"dp_{pg_name}"):
                    db.collection("playgrounds").document(pg_name).delete()
                    st.rerun()

# --- 7. 메인 콘텐츠 (인기글 TOP 5) ---
st.title("🏛️ OurNoliter 광장")

all_posts_stream = db.collection("posts").stream()
post_list = []
for p in all_posts_stream:
    d = p.to_dict(); d['id'] = p.id
    d['score'] = len(d.get('upvotes', [])) - len(d.get('downvotes', []))
    post_list.append(d)

hot_posts = sorted(post_list, key=lambda x: x['score'], reverse=True)[:5]
st.markdown("### 🔥 실시간 인기글 TOP 5")
for idx, hp in enumerate(hot_posts):
    if hp['score'] > 0:
        st.markdown(f'<div class="hot-post-container"><span class="hot-badge">TOP {idx+1}</span><b>[{hp.get("playground")}] {hp.get("title")}</b> <span style="float:right;">⭐ {hp["score"]}</span></div>', unsafe_allow_html=True)

st.markdown("---")

# --- 8. 검색 및 생성 ---
col_s, col_b = st.columns([0.8, 0.2])
with col_s:
    s_in = st.text_input("놀이터 검색", placeholder="가고 싶은 놀이터...", label_visibility="collapsed")
with col_b:
    if st.button("이동", use_container_width=True):
        if s_in in existing_pgs:
            st.session_state.current_playground = s_in
        else: st.session_state.search_target = s_in
        st.rerun()

if st.session_state.search_target and st.session_state.search_target not in existing_pgs:
    st.markdown(f'<div class="not-found-box">⚠️ \'{st.session_state.search_target}\' 놀이터가 없습니다.</div>', unsafe_allow_html=True)
    if st.session_state.user_info and st.button(f"🏗️ '{st.session_state.search_target}' 지금 만들기", use_container_width=True):
        db.collection("playgrounds").document(st.session_state.search_target).set({"created_at": datetime.now()})
        st.session_state.current_playground = st.session_state.search_target
        st.session_state.search_target = ""
        st.rerun()

# --- 9. 게시판 피드 ---
curr = st.session_state.current_playground
st.markdown(f"<div class='playground-title'>{curr} 놀이터</div>", unsafe_allow_html=True)

if curr != "전체" and st.session_state.user_info:
    with st.expander("📝 새 글 작성"):
        with st.form("p_form", clear_on_submit=True):
            t, u, c = st.text_input("제목"), st.text_input("이미지 URL"), st.text_area("내용")
            if st.form_submit_button("등록") and t and c:
                db.collection("posts").add({
                    "playground": curr, "title": t, "content": c, "image": u,
                    "author": st.session_state.user_info['name'],
                    "author_email": st.session_state.user_info['email'],
                    "author_photo": st.session_state.user_info['photo'],
                    "created_at": datetime.now(), "upvotes": [], "downvotes": [], "comments": []
                })
                st.rerun()

query = db.collection("posts")
if curr != "전체": query = query.where("playground", "==", curr)
posts = query.order_by("created_at", direction=firestore.Query.DESCENDING).stream()

for post in posts:
    p, pid = post.to_dict(), post.id
    with st.container():
        h_col, d_col = st.columns([0.85, 0.15])
        with h_col:
            photo = p.get('author_photo', DEFAULT_AVATAR)
            admin_tag = '<span class="admin-badge">ADMIN</span>' if p.get('author_email') == ADMIN_EMAIL else ""
            st.markdown(f'<img src="{photo}" class="profile-img"> <b>{p.get("author")}</b>{admin_tag} <small>• {p["created_at"].strftime("%m/%d %H:%M")}</small>', unsafe_allow_html=True)
        with d_col:
            if st.session_state.user_info and (st.session_state.user_info['email'] == ADMIN_EMAIL or st.session_state.user_info['email'] == p.get('author_email')):
                if st.button("🗑️", key=f"del_{pid}"):
                    db.collection("posts").document(pid).delete(); st.rerun()

        st.subheader(p.get('title'))
        if p.get('image'): st.image(p['image'], use_container_width=True)
        st.write(p.get('content'))

        up_l, down_l = p.get('upvotes', []), p.get('downvotes', [])
        v1, v2, _ = st.columns([0.2, 0.2, 0.6])
        with v1:
            if st.button(f"👍 {len(up_l)}", key=f"up_{pid}"):
                if st.session_state.user_info:
                    email = st.session_state.user_info['email']
                    if email in up_l: db.collection("posts").document(pid).update({"upvotes": firestore.ArrayRemove([email])})
                    else: db.collection("posts").document(pid).update({"upvotes": firestore.ArrayUnion([email]), "downvotes": firestore.ArrayRemove([email])})
                    st.rerun()
        with v2:
            if st.button(f"👎 {len(down_l)}", key=f"dw_{pid}"):
                if st.session_state.user_info:
                    email = st.session_state.user_info['email']
                    if email in down_l: db.collection("posts").document(pid).update({"downvotes": firestore.ArrayRemove([email])})
                    else: db.collection("posts").document(pid).update({"downvotes": firestore.ArrayUnion([email]), "upvotes": firestore.ArrayRemove([email])})
                    st.rerun()
        
        with st.expander(f"💬 댓글 {len(p.get('comments', []))}개"):
            for com in p.get('comments', []):
                st.markdown(f'<b>{com["author"]}</b>: {com["text"]}', unsafe_allow_html=True)
            if st.session_state.user_info:
                with st.form(key=f"f_{pid}", clear_on_submit=True):
                    c_txt = st.text_input("댓글 입력", label_visibility="collapsed")
                    if st.form_submit_button("등록"):
                        db.collection("posts").document(pid).update({"comments": firestore.ArrayUnion([{"author": st.session_state.user_info['name'], "text": c_txt}])})
                        st.rerun()