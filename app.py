import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth
import requests
from datetime import datetime, timedelta
import extra_streamlit_components as stx
import time

# [에러 방지] google-cloud-firestore를 직접 사용합니다.
from google.cloud import firestore as google_firestore

# --- 1. 설정 및 관리자 계정 ---
ADMIN_EMAIL = "hoodman10@yahoo.com"
DEFAULT_AVATAR = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
FIREBASE_WEB_API_KEY = st.secrets["firebase"].get("api_key")

# --- 2. Firebase 초기화 및 DB 연결 ---
@st.cache_resource
def init_all_services():
    if not firebase_admin._apps:
        cred_dict = dict(st.secrets["firebase"])
        cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    
    cred_dict = dict(st.secrets["firebase"])
    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
    return google_firestore.Client.from_service_account_info(cred_dict)

db = init_all_services()

# --- 3. 쿠키 매니저 초기화 ---
cookie_manager = stx.CookieManager()

# --- 4. 검증 함수들 ---
def verify_password(email, password):
    if not FIREBASE_WEB_API_KEY:
        st.error("API Key 미설정")
        return False
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    res = requests.post(url, json=payload)
    return res.status_code == 200

def is_valid_image_url(url):
    if not url: return True 
    image_formats = (".png", ".jpg", ".jpeg", ".gif", ".webp")
    if not url.lower().endswith(image_formats):
        return False
    try:
        res = requests.head(url, timeout=3)
        return res.status_code == 200
    except:
        return False

# --- 5. CSS 디자인 ---
st.set_page_config(page_title="OurNoliter.com", page_icon="🎡", layout="centered")
st.markdown("""
    <style>
    .top-header {
        background-color: #808080; color: white; padding: 10px;
        text-align: center; font-weight: bold; border-radius: 8px; margin-bottom: 20px;
    }
    div.stButton > button { transform: scale(0.85); }
    div.stButton > button[key^="side_l_"], div.stButton > button[key^="main_l_"] {
        transform: scale(0.7); margin-left: -15%;
    }
    div.stButton > button[key^="up_"], div.stButton > button[key^="dw_"], div.stButton > button[key^="h_com_"] {
        transform: scale(0.7); display: block; margin: 0 auto;
    }
    .not-found-box {
        background-color: #fee2e2; border: 1px solid #ef4444; color: #b91c1c;
        padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px; font-weight: bold;
    }
    div[data-testid="stCheckbox"] {
        background-color: #f8f9fa; padding: 0px 10px; border-radius: 4px; border: 1px solid #ddd;
        width: 100%; height: 28px; display: flex; align-items: center;
    }
    .stColumn > div { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }
    .hot-post-container { background-color: #fffbeb; border: 1px solid #fde68a; padding: 12px; border-radius: 10px; margin-bottom: 10px; }
    .hot-badge { background-color: #f59e0b; color: white; padding: 2px 8px; border-radius: 20px; font-size: 11px; font-weight: bold; margin-right: 8px; }
    .rank-badge { background-color: #003399; color: white; padding: 2px 8px; border-radius: 5px; font-size: 12px; font-weight: bold; margin-right: 10px; }
    .admin-badge { background-color: #ff4b4b; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; margin-left: 5px; }
    .profile-img { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; margin-right: 10px; vertical-align: middle; border: 1px solid #ddd; }
    .playground-title { color: #003399; font-weight: bold; font-size: 26px; margin-bottom: 10px; border-bottom: 2px solid #003399; padding-bottom: 5px; }
    .rank-item { padding: 10px; border-bottom: 1px solid #eee; display: flex; align-items: center; justify-content: space-between; }
    </style>
    <div class="top-header">OurNoliter.com</div>
    """, unsafe_allow_html=True)

# 세션 상태
if "user_info" not in st.session_state: st.session_state.user_info = None
if "current_playground" not in st.session_state: st.session_state.current_playground = "전체"
if "search_target" not in st.session_state: st.session_state.search_target = ""

# --- 6. 사이드바 (아이디 저장 기능 복구) ---
with st.sidebar:
    st.title("OurNoliter.com")
    
    # [복구] 저장된 쿠키에서 이메일 가져오기
    saved_email = cookie_manager.get("saved_email")
    if saved_email is None: saved_email = ""

    if st.session_state.user_info is None:
        menu = st.tabs(["로그인", "회원가입"])
        with menu[0]:
            l_email = st.text_input("이메일", value=saved_email, key="l_em")
            l_pw = st.text_input("비밀번호", type="password", key="l_pw")
            rem_id = st.checkbox("아이디 저장", value=bool(saved_email), key="rem_cb")
            
            if st.button("로그인", use_container_width=True, type="primary"):
                if verify_password(l_email, l_pw):
                    user = auth.get_user_by_email(l_email)
                    st.session_state.user_info = {
                        "name": user.display_name, 
                        "email": user.email, 
                        "photo": user.photo_url if user.photo_url else DEFAULT_AVATAR
                    }
                    
                    # [복구] 아이디 저장 로직
                    if rem_id:
                        cookie_manager.set("saved_email", l_email, expires_at=datetime.now() + timedelta(days=30))
                    else:
                        cookie_manager.delete("saved_email")
                    
                    st.rerun()
                else: st.error("정보가 틀렸습니다.")
        with menu[1]:
            reg_em = st.text_input("새 이메일", key="r_em")
            reg_pw = st.text_input("새 비밀번호", type="password", key="r_pw")
            reg_nm = st.text_input("닉네임", key="r_nm")
            if st.button("가입하기", use_container_width=True):
                if reg_em and reg_pw and reg_nm:
                    try:
                        auth.create_user(email=reg_em, password=reg_pw, display_name=reg_nm)
                        st.success("가입 성공! 로그인해주세요.")
                    except Exception as e: st.error(f"가입 실패: {e}")
    else:
        st.image(st.session_state.user_info['photo'], width=60)
        st.success(f"✅ {st.session_state.user_info['name']}님")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.user_info = None
            st.rerun()

    st.markdown("---")
    st.subheader("📁 놀이터 목록")
    if st.button("🏠 전체 메인 피드", use_container_width=True):
        st.session_state.current_playground = "전체"
        st.rerun()
    
    pg_list_side = db.collection("playgrounds").order_by("created_at", direction=google_firestore.Query.DESCENDING).stream()
    is_admin = st.session_state.user_info and st.session_state.user_info['email'] == ADMIN_EMAIL
    
    existing_pg_names = []
    for pg in pg_list_side:
        pg_name = pg.id
        existing_pg_names.append(pg_name)
        if is_admin:
            c1, c2 = st.columns([0.8, 0.2])
            with c1:
                if st.button(f"🎡 {pg_name}", key=f"side_l_{pg_name}", use_container_width=True):
                    st.session_state.current_playground = pg_name; st.rerun()
            with c2:
                if st.button("🗑️", key=f"side_del_pg_{pg_name}"):
                    db.collection("playgrounds").document(pg_name).delete(); st.rerun()
        else:
            if st.button(f"🎡 {pg_name}", key=f"side_l_{pg_name}", use_container_width=True):
                st.session_state.current_playground = pg_name; st.rerun()

# --- 7. 데이터 집계 (랭킹/인기글) ---
all_posts_data = list(db.collection("posts").stream())
post_list = []
playground_counts = {}

for p in all_posts_data:
    d = p.to_dict(); d['id'] = p.id
    pg_n = d.get('playground')
    if pg_n in existing_pg_names:
        d['score'] = len(d.get('upvotes', [])) - len(d.get('downvotes', []))
        post_list.append(d)
        playground_counts[pg_n] = playground_counts.get(pg_n, 0) + 1

sorted_pg_ranks = sorted(playground_counts.items(), key=lambda x: x[1], reverse=True)
hot_posts = sorted(post_list, key=lambda x: x['score'], reverse=True)[:5]

# --- 8. 검색 및 이동 ---
col_s, col_b = st.columns([0.8, 0.2])
with col_s:
    s_in = st.text_input("놀이터 검색", placeholder="가고 싶은 놀이터...", key="search_bar", label_visibility="collapsed")
with col_b:
    if st.button("이동", use_container_width=True):
        if s_in in existing_pg_names: 
            st.session_state.current_playground = s_in
            st.session_state.search_target = ""
        else: st.session_state.search_target = s_in
        st.rerun()

if st.session_state.search_target:
    st.markdown(f'<div class="not-found-box">⚠️ \'{st.session_state.search_target}\' 놀이터가 존재하지 않습니다.</div>', unsafe_allow_html=True)
    if st.session_state.user_info and st.button(f"🏗️ '{st.session_state.search_target}' 놀이터 지금 만들기", use_container_width=True):
        db.collection("playgrounds").document(st.session_state.search_target).set({"created_at": datetime.now()})
        st.session_state.current_playground = st.session_state.search_target
        st.session_state.search_target = ""
        st.rerun()

# --- 9. 메인 콘텐츠 ---
curr = st.session_state.current_playground

if curr == "전체":
    st.title("🏛️ OurNoliter 광장")
    st.subheader("🔥 실시간 인기 게시글")
    for idx, hp in enumerate(hot_posts):
        if hp['score'] > 0:
            st.markdown(f'<div class="hot-post-container"><span class="hot-badge">TOP {idx+1}</span><b>[{hp.get("playground")}] {hp.get("title")}</b> <span style="float:right;">⭐ {hp["score"]}</span></div>', unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏆 놀이터 랭킹")
        for i, (name, count) in enumerate(sorted_pg_ranks[:10]):
            st.markdown(f'<div class="rank-item"><span><span class="rank-badge">{i+1}위</span> 🎡 {name}</span><span style="color:gray; font-size:13px;">{count} posts</span></div>', unsafe_allow_html=True)
    with col2:
        st.subheader("🎡 놀이터 바로가기")
        for pg_name in existing_pg_names:
            if is_admin:
                c_a, c_b = st.columns([0.8, 0.2])
                with c_a:
                    if st.button(f"🎡 {pg_name}", key=f"main_l_{pg_name}", use_container_width=True):
                        st.session_state.current_playground = pg_name; st.rerun()
                with c_b:
                    if st.button("🗑️", key=f"main_del_pg_{pg_name}"):
                        db.collection("playgrounds").document(pg_name).delete(); st.rerun()
            else:
                if st.button(f"🎡 {pg_name}", key=f"main_l_{pg_name}", use_container_width=True):
                    st.session_state.current_playground = pg_name; st.rerun()
else:
    # --- 특정 놀이터 피드 ---
    st.markdown(f"<div class='playground-title'>{curr} 놀이터</div>", unsafe_allow_html=True)
    if st.session_state.user_info:
        with st.expander("📝 새 글 작성"):
            with st.form("p_form", clear_on_submit=True):
                t, u, c = st.text_input("제목"), st.text_input("이미지 URL"), st.text_area("내용")
                if st.form_submit_button("등록") and t and c:
                    if not is_valid_image_url(u): st.error("이미지 링크 오류")
                    else:
                        db.collection("posts").add({
                            "playground": curr, "title": t, "content": c, "image": u,
                            "author": st.session_state.user_info['name'], "author_email": st.session_state.user_info['email'],
                            "author_photo": st.session_state.user_info['photo'], "created_at": datetime.now(),
                            "upvotes": [], "downvotes": [], "comments": []
                        })
                        st.rerun()

    posts = db.collection("posts").where("playground", "==", curr).order_by("created_at", direction=google_firestore.Query.DESCENDING).stream()
    for post in posts:
        p, pid = post.to_dict(), post.id
        with st.container():
            h_col, d_col = st.columns([0.85, 0.15])
            with h_col:
                photo = p.get('author_photo', DEFAULT_AVATAR)
                admin_tag = '<span class="admin-badge">ADMIN</span>' if p.get('author_email') == ADMIN_EMAIL else ""
                st.markdown(f'<img src="{photo}" class="profile-img"> <b>{p.get("author")}</b>{admin_tag} <small>• {p["created_at"].strftime("%m/%d %H:%M")}</small>', unsafe_allow_html=True)
            with d_col:
                if st.session_state.user_info and (st.session_state.user_info['email'] in [ADMIN_EMAIL, p.get('author_email')]):
                    if st.button("🗑️", key=f"del_{pid}"):
                        db.collection("posts").document(pid).delete(); st.rerun()
            
            st.subheader(p.get('title'))
            if p.get('image'): st.image(p['image'], use_container_width=True)
            st.write(p.get('content'))
            
            up_l, down_l = p.get('upvotes', []), p.get('downvotes', [])
            _, v1, v2, _ = st.columns([0.3, 0.2, 0.2, 0.3]) 
            with v1:
                if st.button(f"👍 {len(up_l)}", key=f"up_{pid}") and st.session_state.user_info:
                    email = st.session_state.user_info['email']
                    if email in up_l: db.collection("posts").document(pid).update({"upvotes": google_firestore.ArrayRemove([email])})
                    else: db.collection("posts").document(pid).update({"upvotes": google_firestore.ArrayUnion([email]), "downvotes": google_firestore.ArrayRemove([email])})
                    st.rerun()
            with v2:
                if st.button(f"👎 {len(down_l)}", key=f"dw_{pid}") and st.session_state.user_info:
                    email = st.session_state.user_info['email']
                    if email in down_l: db.collection("posts").document(pid).update({"downvotes": google_firestore.ArrayRemove([email])})
                    else: db.collection("posts").document(pid).update({"downvotes": google_firestore.ArrayUnion([email]), "upvotes": google_firestore.ArrayRemove([email])})
                    st.rerun()
            
            comments = p.get('comments', [])
            with st.expander(f"💬 댓글 {len(comments)}개"):
                for idx, com in enumerate(comments):
                    c_hearts = com.get('hearts', [])
                    c_col1, c_col2 = st.columns([0.85, 0.15])
                    with c_col1: st.markdown(f'<b>{com["author"]}</b>: {com["text"]}', unsafe_allow_html=True)
                    with c_col2:
                        if st.button(f"❤️ {len(c_hearts)}", key=f"h_com_{pid}_{idx}"):
                            if st.session_state.user_info:
                                user_email = st.session_state.user_info['email']
                                if user_email in c_hearts: c_hearts.remove(user_email)
                                else: c_hearts.append(user_email)
                                comments[idx]['hearts'] = c_hearts
                                db.collection("posts").document(pid).update({"comments": comments})
                                st.rerun()
                if st.session_state.user_info:
                    with st.form(key=f"f_{pid}", clear_on_submit=True):
                        c_txt = st.text_input("댓글 입력", label_visibility="collapsed")
                        if st.form_submit_button("댓글 등록") and c_txt:
                            new_comment = {"author": st.session_state.user_info['name'], "text": c_txt, "hearts": []}
                            db.collection("posts").document(pid).update({"comments": google_firestore.ArrayUnion([new_comment])})
                            st.rerun()