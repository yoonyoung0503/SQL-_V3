import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(
    page_title="SQL 교육자료 | 주택금융 실무",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.section-header {font-size:1.6rem;font-weight:800;border-bottom:3px solid #1565C0;margin-bottom:1rem;}
.box {padding:0.7rem;border-radius:8px;margin:0.5rem 0;}
.tip {background:#E3F2FD;}
.good {background:#E8F5E9;}
.warn {background:#FFF8E1;}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_db():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.executescript("""
    CREATE TABLE data (
        id TEXT,
        date TEXT,
        region TEXT,
        product TEXT,
        cnt INTEGER,
        amt REAL
    );

    INSERT INTO data VALUES
    ('1','20230101','서울','전세',12000,2000),
    ('2','20230102','서울','구입',8000,3000),
    ('3','20230103','경기','전세',15000,NULL),
    ('4','20230104','경기','기타',3000,500);
    """)
    return conn

conn = get_db()

def run(sql):
    try:
        return pd.read_sql_query(sql, conn), None
    except Exception as e:
        return None, str(e)

st.markdown('<div class="section-header">SQL 실습</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["SELECT", "GROUP BY", "실습"])

with tab1:
    st.markdown("### SELECT + CASE WHEN")
    sql = """
    SELECT 
        id,
        product,
        CASE 
            WHEN product LIKE '%전세%' THEN '전세자금'
            WHEN product LIKE '%구입%' THEN '구입자금'
            ELSE '기타'
        END AS category
    FROM data;
    """
    st.code(sql, language="sql")
    if st.button("실행1"):
        df, err = run(sql)
        if err: st.error(err)
        else: st.dataframe(df)

with tab2:
    st.markdown("### GROUP BY + COALESCE")
    sql = """
    SELECT 
        product,
        SUM(cnt) AS total_cnt,
        SUM(COALESCE(amt,0)) AS total_amt
    FROM data
    GROUP BY product;
    """
    st.code(sql, language="sql")
    if st.button("실행2"):
        df, err = run(sql)
        if err: st.error(err)
        else: st.dataframe(df)

with tab3:
    st.markdown("### 실습 문제")
    st.markdown("금액 NULL을 0으로 바꾸고 규모 분류하세요")
    user = st.text_area("SQL 작성")

    if st.button("실행3"):
        df, err = run(user)
        if err: st.error(err)
        else: st.dataframe(df)

    if st.button("정답"):
        ans = """
        SELECT 
            id,
            cnt,
            CASE 
                WHEN cnt >= 10000 THEN '대규모'
                WHEN cnt >= 5000 THEN '중규모'
                ELSE '소규모'
            END AS scale,
            COALESCE(amt,0) AS amt
        FROM data;
        """
        st.code(ans, language="sql")
        df, _ = run(ans)
        st.dataframe(df)
