import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth
import requests
from datetime import datetime, timedelta
import extra_streamlit_components as stx
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
cookie_manager = stx.CookieManager()

# --- 3. 검증 함수들 ---
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
    if not url.lower().endswith(image_formats): return False
    try:
        res = requests.head(url, timeout=3)
        return res.status_code == 200
    except: return False

# --- 4. CSS 디자인 ---
st.set_page_config(page_title="OurNoliter.com", page_icon="🎡", layout="centered")
st.markdown("""
    <style>
    .top-header { background-color: #808080; color: white; padding: 10px; text-align: center; font-weight: bold; border-radius: 8px; margin-bottom: 20px; }
    div.stButton > button { transform: scale(0.85); }
    div.stButton > button[key^="side_l_"], div.stButton > button[key^="main_l_"] { transform: scale(0.7); margin-left: -15%; }
    div.stButton > button[key^="up_"], div.stButton > button[key^="dw_"], div.stButton > button[key^="h_com_"] { transform: scale(0.7); display: block; margin: 0 auto; }
    .anonymous-box { background-color: #f1f5f9; border-left: 5px solid #64748b; padding: 15px; border-radius: 8px; margin-top: 10px; margin-bottom: 10px; max-height: 250px; overflow-y: auto; }
    .anon-msg { font-size: 14px; border-bottom: 1px solid #e2e8f0; padding: 5px 0; color: #334155; }
    .anon-time { color: #94a3b8; font-size: 11px; margin-left: 8px; }
    .not-found-box { background-color: #fee2e2; border: 1px solid #ef4444; color: #b91c1c; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px; font-weight: bold; }
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

# 세션 상태 초기화
if "user_info" not in st.session_state: st.session_state.user_info = None
if "current_playground" not in st.session_state: st.session_state.current_playground = "전체"
if "search_target" not in st.session_state: st.session_state.search_target = ""

# --- 5. 사이드바 (로그인/아이디저장/목록) ---
with st.sidebar:
    st.title("OurNoliter.com")
    saved_email = cookie_manager.get("saved_email") or ""

    if st.session_state.user_info is None:
        menu = st.tabs(["로그인", "회원가입"])
        with menu[0]:
            l_email = st.text_input("이메일", value=saved_email, key="l_em")
            l_pw = st.text_input("비밀번호", type="password", key="l_pw")
            rem_id = st.checkbox("아이디 저장", value=bool(saved_email), key="rem_cb")
            if st.button("로그인", use_container_width=True, type="primary"):
                if verify_password(l_email, l_pw):
                    user = auth.get_user_by_email(l_email)
                    st.session_state.user_info = {"name": user.display_name, "email": user.email, "photo": user.photo_url if user.photo_url else DEFAULT_AVATAR}
                    if rem_id: cookie_manager.set("saved_email", l_email, expires_at=datetime.now() + timedelta(days=30))
                    else: cookie_manager.delete("saved_email")
                    st.rerun()
                else: st.error("정보가 틀렸습니다.")
        with menu[1]:
            r_em = st.text_input("새 이메일", key="reg_em")
            r_pw = st.text_input("새 비밀번호", type="password", key="reg_pw")
            r_nm = st.text_input("닉네임", key="reg_nm")
            if st.button("가입하기", use_container_width=True):
                if r_em and r_pw and r_nm:
                    try: auth.create_user(email=r_em, password=r_pw, display_name=r_nm); st.success("가입 성공! 로그인해주세요.")
                    except Exception as e: st.error(f"가입 실패: {e}")
    else:
        st.image(st.session_state.user_info['photo'], width=60)
        st.success(f"✅ {st.session_state.user_info['name']}님")
        if st.button("로그아웃", use_container_width=True): st.session_state.user_info = None; st.rerun()

    st.markdown("---")
    st.subheader("📁 놀이터 목록")
    if st.button("🏠 전체 메인 피드", use_container_width=True): st.session_state.current_playground = "전체"; st.rerun()
    
    pg_list_side = db.collection("playgrounds").order_by("created_at", direction=google_firestore.Query.DESCENDING).stream()
    is_admin = st.session_state.user_info and st.session_state.user_info['email'] == ADMIN_EMAIL
    existing_pg_names = []
    for pg in pg_list_side:
        pg_name = pg.id
        existing_pg_names.append(pg_name)
        col_btn, col_del = st.columns([0.8, 0.2]) if is_admin else (st.container(), None)
        with col_btn:
            if st.button(f"🎡 {pg_name}", key=f"side_l_{pg_name}", use_container_width=True): st.session_state.current_playground = pg_name; st.rerun()
        if is_admin and col_del:
            with col_del:
                if st.button("🗑️", key=f"side_del_{pg_name}"): db.collection("playgrounds").document(pg_name).delete(); st.rerun()

# --- 6. 데이터 집계 (랭킹/인기글) ---
all_posts_data = list(db.collection("posts").stream())
post_list, playground_counts = [], {}
for p in all_posts_data:
    d = p.to_dict(); d['id'] = p.id
    pg_n = d.get('playground')
    if pg_n in existing_pg_names:
        d['score'] = len(d.get('upvotes', [])) - len(d.get('downvotes', []))
        post_list.append(d)
        playground_counts[pg_n] = playground_counts.get(pg_n, 0) + 1
sorted_pg_ranks = sorted(playground_counts.items(), key=lambda x: x[1], reverse=True)
hot_posts = sorted(post_list, key=lambda x: x['score'], reverse=True)[:5]

# --- 7. 메인 콘텐츠 ---
curr = st.session_state.current_playground

# 공통 검색바
c_s, c_b = st.columns([0.8, 0.2])
with c_s: s_in = st.text_input("놀이터 검색", placeholder="가고 싶은 놀이터...", key="search_bar", label_visibility="collapsed")
with c_b:
    if st.button("이동", use_container_width=True):
        if s_in in existing_pg_names: st.session_state.current_playground = s_in; st.session_state.search_target = ""
        else: st.session_state.search_target = s_in
        st.rerun()

if st.session_state.search_target:
    st.markdown(f'<div class="not-found-box">⚠️ \'{st.session_state.search_target}\' 놀이터가 없습니다.</div>', unsafe_allow_html=True)
    if st.session_state.user_info and st.button(f"🏗️ '{st.session_state.search_target}' 놀이터 만들기", use_container_width=True):
        db.collection("playgrounds").document(st.session_state.search_target).set({"created_at": datetime.now()})
        st.session_state.current_playground = st.session_state.search_target; st.session_state.search_target = ""; st.rerun()

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
            st.markdown(f'<div class="rank-item"><span><span class="rank-badge">{i+1}위</span> {name}</span><small>{count} posts</small></div>', unsafe_allow_html=True)
    with col2:
        st.subheader("🎡 바로가기")
        for pg_name in existing_pg_names:
            if is_admin:
                mc1, mc2 = st.columns([0.8, 0.2])
                with mc1: 
                    if st.button(f"🎡 {pg_name}", key=f"m_l_{pg_name}", use_container_width=True): st.session_state.current_playground = pg_name; st.rerun()
                with mc2:
                    if st.button("🗑️", key=f"m_del_{pg_name}"): db.collection("playgrounds").document(pg_name).delete(); st.rerun()
            else:
                if st.button(f"🎡 {pg_name}", key=f"m_l_{pg_name}", use_container_width=True): st.session_state.current_playground = pg_name; st.rerun()

    # --- [위치 이동] 익명 대화방 섹션 (메인 하단) ---
    st.markdown("---")
    st.subheader("🤫 익명 한 줄 대화")
    st.markdown('<div class="anonymous-box">', unsafe_allow_html=True)
    anon_msgs = db.collection("anonymous_chat").order_by("created_at", direction=google_firestore.Query.DESCENDING).limit(10).stream()
    for m in anon_msgs:
        md = m.to_dict()
        st.markdown(f'<div class="anon-msg">👤 익명: {md["text"]} <span class="anon-time">{md["created_at"].strftime("%H:%M")}</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    with st.form("anon_form", clear_on_submit=True):
        ac1, ac2 = st.columns([0.8, 0.2])
        with ac1: a_txt = st.text_input("메시지", placeholder="아무 말이나 남겨보세요...", label_visibility="collapsed")
        with ac2: 
            if st.form_submit_button("남기기", use_container_width=True) and a_txt:
                db.collection("anonymous_chat").add({"text": a_txt, "created_at": datetime.now()}); st.rerun()

else:
    # --- 특정 놀이터 피드 ---
    st.markdown(f"<div class='playground-title'>{curr} 놀이터</div>", unsafe_allow_html=True)
    if st.session_state.user_info:
        with st.expander("📝 새 글 작성"):
            with st.form("p_form", clear_on_submit=True):
                t, u, c = st.text_input("제목"), st.text_input("이미지 URL"), st.text_area("내용")
                if st.form_submit_button("등록") and t and c:
                    if is_valid_image_url(u):
                        db.collection("posts").add({
                            "playground": curr, "title": t, "content": c, "image": u,
                            "author": st.session_state.user_info['name'], "author_email": st.session_state.user_info['email'],
                            "author_photo": st.session_state.user_info['photo'], "created_at": datetime.now(),
                            "upvotes": [], "downvotes": [], "comments": []
                        }); st.rerun()
                    else: st.error("이미지 URL을 확인해주세요.")

    posts = db.collection("posts").where("playground", "==", curr).order_by("created_at", direction=google_firestore.Query.DESCENDING).stream()
    for post in posts:
        p, pid = post.to_dict(), post.id
        with st.container():
            h_col, d_col = st.columns([0.85, 0.15])
            with h_col:
                photo = p.get('author_photo', DEFAULT_AVATAR)
                adm = '<span class="admin-badge">ADMIN</span>' if p.get('author_email') == ADMIN_EMAIL else ""
                st.markdown(f'<img src="{photo}" class="profile-img"> <b>{p.get("author")}</b>{adm} <small>{p["created_at"].strftime("%m/%d %H:%M")}</small>', unsafe_allow_html=True)
            with d_col:
                if st.session_state.user_info and (st.session_state.user_info['email'] in [ADMIN_EMAIL, p.get('author_email')]):
                    if st.button("🗑️", key=f"del_{pid}"): db.collection("posts").document(pid).delete(); st.rerun()
            
            st.subheader(p.get('title'))
            if p.get('image'): st.image(p['image'], use_container_width=True)
            st.write(p.get('content'))
            
            up_l, dw_l = p.get('upvotes', []), p.get('downvotes', [])
            _, v1, v2, _ = st.columns([0.3, 0.2, 0.2, 0.3]) 
            with v1:
                if st.button(f"👍 {len(up_l)}", key=f"up_{pid}") and st.session_state.user_info:
                    email = st.session_state.user_info['email']
                    if email in up_l: db.collection("posts").document(pid).update({"upvotes": google_firestore.ArrayRemove([email])})
                    else: db.collection("posts").document(pid).update({"upvotes": google_firestore.ArrayUnion([email]), "downvotes": google_firestore.ArrayRemove([email])})
                    st.rerun()
            with v2:
                if st.button(f"👎 {len(dw_l)}", key=f"dw_{pid}") and st.session_state.user_info:
                    email = st.session_state.user_info['email']
                    if email in dw_l: db.collection("posts").document(pid).update({"downvotes": google_firestore.ArrayRemove([email])})
                    else: db.collection("posts").document(pid).update({"downvotes": google_firestore.ArrayUnion([email]), "upvotes": google_firestore.ArrayRemove([email])})
                    st.rerun()
            
            coms = p.get('comments', [])
            with st.expander(f"💬 댓글 {len(coms)}개"):
                for idx, com in enumerate(coms):
                    h_l = com.get('hearts', [])
                    c1, c2 = st.columns([0.85, 0.15])
                    with c1: st.markdown(f'<b>{com["author"]}</b>: {com["text"]}', unsafe_allow_html=True)
                    with c2:
                        if st.button(f"❤️ {len(h_l)}", key=f"h_com_{pid}_{idx}") and st.session_state.user_info:
                            u_em = st.session_state.user_info['email']
                            if u_em in h_l: h_l.remove(u_em)
                            else: h_l.append(u_em)
                            coms[idx]['hearts'] = h_l
                            db.collection("posts").document(pid).update({"comments": coms}); st.rerun()
                if st.session_state.user_info:
                    with st.form(key=f"fc_{pid}", clear_on_submit=True):
                        c_in = st.text_input("댓글", label_visibility="collapsed")
                        if st.form_submit_button("등록") and c_in:
                            new_c = {"author": st.session_state.user_info['name'], "text": c_in, "hearts": []}
                            db.collection("posts").document(pid).update({"comments": google_firestore.ArrayUnion([new_c])}); st.rerun()