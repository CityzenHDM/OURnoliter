import streamlit as st
from firebase_admin import auth

def show_user_list():
    st.subheader("👥 전체 유저 관리 (Admin Only)")
    
    try:
        # Firebase에서 모든 유저 가져오기
        page = auth.list_users()
        users = page.users
        
        if not users:
            st.info("가입된 유저가 없습니다.")
            return

        for user in users:
            col1, col2, col3 = st.columns([0.4, 0.4, 0.2])
            with col1:
                st.write(f"**닉네임:** {user.display_name}")
            with col2:
                st.write(f"**이메일:** {user.email}")
            with col3:
                # 어드민 본인은 지울 수 없게 설정 (안전장치)
                if user.email != "hoodman10@yahoo.com":
                    if st.button("🔴 삭제", key=f"del_user_{user.uid}"):
                        auth.delete_user(user.uid)
                        st.success(f"{user.display_name} 유저 삭제 완료!")
                        st.rerun()
            st.markdown("---")
            
    except Exception as e:
        st.error(f"유저 목록을 불러오는 중 오류 발생: {e}")

    if st.button("🏠 돌아가기"):
        st.session_state.admin_view = "main"
        st.rerun()