import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(
    page_title="SQL 교육자료 | 주택금융",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .section-header {
        font-size: 1.7rem; font-weight: 800; color: #1a1a2e;
        border-bottom: 3px solid #1565C0;
        padding-bottom: 0.4rem; margin-bottom: 1.2rem;
    }
    .tip-box {
        background: #E3F2FD; border-left: 4px solid #1565C0;
        padding: 0.75rem 1rem; border-radius: 0 8px 8px 0; margin: 0.6rem 0;
    }
    .warn-box {
        background: #FFF8E1; border-left: 4px solid #F9A825;
        padding: 0.75rem 1rem; border-radius: 0 8px 8px 0; margin: 0.6rem 0;
    }
    .good-box {
        background: #E8F5E9; border-left: 4px solid #2E7D32;
        padding: 0.75rem 1rem; border-radius: 0 8px 8px 0; margin: 0.6rem 0;
    }
    .syntax-box {
        background: #F3E5F5; border-left: 4px solid #6A1B9A;
        padding: 0.75rem 1rem; border-radius: 0 8px 8px 0; margin: 0.6rem 0;
        font-family: monospace; font-size: 0.92rem; line-height: 1.7;
    }
    .quiz-box {
        background: #FFF3E0; border: 2px dashed #FB8C00;
        padding: 1rem 1.2rem; border-radius: 10px; margin: 0.8rem 0;
    }
    .dict-box {
        background: #F8F9FA; border: 1px solid #DEE2E6;
        border-radius: 10px; padding: 1rem 1.2rem; margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# DB 초기화 — 실제 업무 컬럼명 기반
# ══════════════════════════════════════════════════════════════
@st.cache_resource
def get_db():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.executescript("""
        -- TA_COA311M_CDBSC: 지역 마스터 (CD_GRP_ID='COA0083')
        CREATE TABLE TA_COA311M_CDBSC (
            CD_ID        TEXT PRIMARY KEY,   -- 지역코드
            CD_NM        TEXT NOT NULL,       -- 지역명
            CD_GRP_ID    TEXT,               -- 코드그룹 (COA0083=지역)
            ZONE_TYPE    TEXT                -- 권역 구분 (수도권/지방)
        );

        -- TW_RGG102M_GRNTCRST_DD: 보증 현황 일별 (주택보증)
        CREATE TABLE TW_RGG102M_GRNTCRST_DD (
            BASIS_DY             TEXT NOT NULL,  -- 기준일자 (YYYYMMDD)
            GRNT_NO              TEXT NOT NULL,  -- 보증번호
            HS_LOC_ZONE_DVCD     TEXT,           -- 주택소재지역코드 (CD_ID 참조)
            PNSN_GV_METH_DVCD   TEXT,           -- 지급방식코드 (07=전세/08=구입/09=중도금)
            GRNT_SPLY_CNT        INTEGER,        -- 공급건수
            GRNT_GEN_CNCL_CNT   INTEGER,        -- 일반해지건수
            GRNT_UNEX_CNCL_CNT  INTEGER,        -- 미실행해지건수
            GRNT_PRMS_RETR_CNCL_CNT INTEGER,    -- 약정채무상환해지건수
            APRS_EVAL_AMT        REAL            -- 감정평가금액(주택가격, 억원)
        );

        -- TW_RGG101M_GRNTREQCNSL_DD: 보증금액 상담 일별
        CREATE TABLE TW_RGG101M_GRNTREQCNSL_DD (
            BASIS_DY      TEXT NOT NULL,  -- 기준일자
            GRNT_NO       TEXT NOT NULL,  -- 보증번호
            GRNT_AMT      REAL,           -- 보증금액 (억원)
            LAST_CNCL_DY  TEXT            -- 최종해지일자
        );

        -- TB_RGE303M_GRNTRVEWAMT: 연금 최초월지급금
        CREATE TABLE TB_RGE303M_GRNTRVEWAMT (
            GRNT_NO       TEXT NOT NULL,  -- 보증번호
            MM_PYAT_AMT   REAL            -- 월지급금액 (만원)
        );

        -- TB_RGE301M_GRNTRVEHUMNMAT: 연금 가입자 인적사항
        CREATE TABLE TB_RGE301M_GRNTRVEHUMNMAT (
            GRNT_NO       TEXT NOT NULL,  -- 보증번호
            AGE_YRCT      INTEGER         -- 연령
        );

        -- TB_RGR011M_HSPRC: 시세 정보
        CREATE TABLE TB_RGR011M_HSPRC (
            BASIS_YM          TEXT,   -- 기준연월 (YYYYMM)
            GRNT_NO           TEXT,   -- 보증번호
            KAB_TRD_AVG_PRC   REAL,   -- KB거래평균가격
            KB_TRD_AVG_PRC    REAL,   -- KB시세평균가격
            KAB_SISE_RSCH_DY  TEXT    -- KB시세조사일 (0이면 부동산원)
        );

        -- ─── 데이터 삽입 ───────────────────────────────────────
        -- 지역 마스터
        INSERT INTO TA_COA311M_CDBSC VALUES
            ('11','서울','COA0083','수도권'),
            ('41','경기','COA0083','수도권'),
            ('28','인천','COA0083','수도권'),
            ('26','부산','COA0083','지방'),
            ('27','대구','COA0083','지방'),
            ('29','광주','COA0083','지방'),
            ('30','대전','COA0083','지방'),
            ('51','강원','COA0083','지방');

        -- 보증 현황 (BASIS_DY: 20200101~20250630 범위 샘플)
        INSERT INTO TW_RGG102M_GRNTCRST_DD VALUES
            ('20200630','G-2020-0001','11','07',12400,120,30,10,4.2),
            ('20200630','G-2020-0002','11','08',8200,80,20,5,3.1),
            ('20200630','G-2020-0003','11','09',5100,50,10,3,2.4),
            ('20200630','G-2020-0004','41','07',18700,180,40,12,3.8),
            ('20200630','G-2020-0005','41','08',11500,110,25,8,4.2),
            ('20200630','G-2020-0006','28','07',5800,55,12,4,2.1),
            ('20200630','G-2020-0007','26','07',4200,40,10,3,1.9),
            ('20200630','G-2020-0008','26','08',2900,28,7,2,1.7),
            ('20210630','G-2021-0001','11','07',13200,130,32,11,4.5),
            ('20210630','G-2021-0002','11','08',9100,90,22,6,3.4),
            ('20210630','G-2021-0003','11','07',22000,220,50,15,4.8),
            ('20210630','G-2021-0004','41','07',20100,200,45,13,4.1),
            ('20210630','G-2021-0005','41','08',13200,130,30,9,5.1),
            ('20210630','G-2021-0006','28','07',6400,62,14,5,2.6),
            ('20210630','G-2021-0007','27','07',3100,30,8,2,2.0),
            ('20210630','G-2021-0008','29','08',1800,17,4,1,1.8),
            ('20220630','G-2022-0001','11','07',11800,115,28,9,4.8),
            ('20220630','G-2022-0002','11','08',8600,84,21,6,3.3),
            ('20220630','G-2022-0003','11','07',25000,250,55,18,5.2),
            ('20220630','G-2022-0004','41','07',19200,190,43,12,4.3),
            ('20220630','G-2022-0005','41','09',8400,82,18,6,3.1),
            ('20220630','G-2022-0006','26','07',4500,44,11,3,1.9),
            ('20220630','G-2022-0007','30','07',2100,20,5,2,1.6),
            ('20220630','G-2022-0008','51','08',980,9,2,1,1.5),
            ('20230630','G-2023-0001','11','07',10500,102,25,8,5.1),
            ('20230630','G-2023-0002','11','08',7800,76,19,5,3.9),
            ('20230630','G-2023-0003','11','07',27500,275,60,20,5.8),
            ('20230630','G-2023-0004','41','07',17900,175,40,11,4.5),
            ('20230630','G-2023-0005','41','08',12100,118,28,8,4.8),
            ('20230630','G-2023-0006','28','07',5200,50,12,4,3.0),
            ('20230630','G-2023-0007','27','08',2400,23,6,2,2.1),
            ('20230630','G-2023-0008','29','07',1900,18,5,1,1.9);

        -- 보증금액 상담
        INSERT INTO TW_RGG101M_GRNTREQCNSL_DD VALUES
            ('20200630','G-2020-0001',1850.5,'20241201'),
            ('20200630','G-2020-0002',3120.0,NULL),
            ('20200630','G-2020-0003',2340.0,'20231015'),
            ('20200630','G-2020-0004',2100.0,NULL),
            ('20200630','G-2020-0005',4200.0,NULL),
            ('20200630','G-2020-0006',980.0,'20250101'),
            ('20200630','G-2020-0007',540.0,NULL),
            ('20200630','G-2020-0008',870.0,NULL),
            ('20210630','G-2021-0001',2050.0,NULL),
            ('20210630','G-2021-0002',3560.0,NULL),
            ('20210630','G-2021-0003',4100.0,NULL),
            ('20210630','G-2021-0004',2450.0,'20250301'),
            ('20210630','G-2021-0005',5100.0,NULL),
            ('20210630','G-2021-0006',1100.0,NULL),
            ('20210630','G-2021-0007',420.0,'20240601'),
            ('20210630','G-2021-0008',510.0,NULL),
            ('20220630','G-2022-0001',1920.0,NULL),
            ('20220630','G-2022-0002',3300.0,NULL),
            ('20220630','G-2022-0003',4800.0,NULL),
            ('20220630','G-2022-0004',2280.0,NULL),
            ('20220630','G-2022-0005',3100.0,NULL),
            ('20220630','G-2022-0006',580.0,NULL),
            ('20220630','G-2022-0007',310.0,NULL),
            ('20220630','G-2022-0008',220.0,NULL),
            ('20230630','G-2023-0001',1750.0,NULL),
            ('20230630','G-2023-0002',3050.0,NULL),
            ('20230630','G-2023-0003',5200.0,NULL),
            ('20230630','G-2023-0004',2100.0,NULL),
            ('20230630','G-2023-0005',4800.0,NULL),
            ('20230630','G-2023-0006',920.0,NULL),
            ('20230630','G-2023-0007',680.0,NULL),
            ('20230630','G-2023-0008',280.0,NULL);

        -- 연금 최초월지급금
        INSERT INTO TB_RGE303M_GRNTRVEWAMT VALUES
            ('G-2020-0001',124.5),('G-2020-0002',198.0),('G-2020-0003',NULL),
            ('G-2020-0004',142.0),('G-2020-0005',210.0),('G-2020-0006',85.0),
            ('G-2021-0001',138.0),('G-2021-0002',215.0),('G-2021-0003',NULL),
            ('G-2021-0004',158.0),('G-2021-0005',NULL),('G-2021-0006',92.0),
            ('G-2022-0001',145.0),('G-2022-0002',220.0),('G-2022-0003',312.0),
            ('G-2022-0004',162.0),('G-2022-0005',NULL),('G-2022-0006',NULL),
            ('G-2023-0001',155.0),('G-2023-0002',235.0),('G-2023-0003',320.0),
            ('G-2023-0004',170.0),('G-2023-0005',NULL),('G-2023-0006',98.0);

        -- 연금 가입자 인적사항 (나이)
        INSERT INTO TB_RGE301M_GRNTRVEHUMNMAT VALUES
            ('G-2020-0001',68),('G-2020-0002',72),('G-2020-0003',65),
            ('G-2020-0004',70),('G-2020-0005',75),('G-2020-0006',63),
            ('G-2021-0001',69),('G-2021-0002',73),('G-2021-0003',66),
            ('G-2021-0004',71),('G-2021-0005',76),('G-2021-0006',64),
            ('G-2022-0001',70),('G-2022-0002',74),('G-2022-0003',67),
            ('G-2022-0004',72),('G-2022-0005',77),('G-2022-0006',65),
            ('G-2023-0001',71),('G-2023-0002',75),('G-2023-0003',68),
            ('G-2023-0004',73),('G-2023-0005',78),('G-2023-0006',66);

        -- 시세 정보
        INSERT INTO TB_RGR011M_HSPRC VALUES
            ('202512','G-2023-0001',5.1,5.0,'1'),
            ('202512','G-2023-0002',3.9,3.8,'0'),
            ('202512','G-2023-0003',5.8,5.7,'1'),
            ('202512','G-2023-0004',4.5,4.4,'1'),
            ('202512','G-2023-0005',4.8,4.7,'0'),
            ('202512','G-2022-0001',4.8,4.7,'1'),
            ('202512','G-2022-0002',3.3,3.2,'0'),
            ('202512','G-2022-0003',5.2,5.1,'1'),
            ('202512','G-2022-0004',4.3,4.2,'1');
    """)
    conn.commit()
    return conn


def run_sql(conn, sql):
    try:
        df = pd.read_sql_query(sql, conn)
        return df, None
    except Exception as e:
        return None, str(e)


def show_result(conn, sql, key):
    if st.button("▶ 실행", key=key):
        df, err = run_sql(conn, sql)
        if err:
            st.error(f"오류: {err}")
        else:
            st.success(f"✅ {len(df)}행 반환")
            st.dataframe(df, use_container_width=True, hide_index=True)


def practice_block(conn, question, answer_sql, key_prefix, hint=None):
    st.markdown(f'<div class="quiz-box">🎯 <b>실습 문제</b><br>{question}</div>',
                unsafe_allow_html=True)
    if hint:
        with st.expander("💡 힌트 보기"):
            st.info(hint)
    user_sql = st.text_area("SQL 직접 작성", height=120, key=f"{key_prefix}_input",
                             placeholder="여기에 SQL을 작성해보세요...")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("▶ 내 답안 실행", key=f"{key_prefix}_run", type="primary"):
            if user_sql.strip():
                df, err = run_sql(conn, user_sql)
                if err:
                    st.error(f"오류: {err}")
                else:
                    st.success(f"✅ {len(df)}행 반환")
                    st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.warning("SQL을 입력해주세요.")
    with col2:
        if st.button("📋 정답 보기", key=f"{key_prefix}_ans"):
            st.markdown('<div class="good-box">✅ <b>정답 쿼리</b></div>',
                        unsafe_allow_html=True)
            st.code(answer_sql, language="sql")
            df, err = run_sql(conn, answer_sql)
            if not err:
                st.caption(f"정답 결과 — {len(df)}행")
                st.dataframe(df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════
# 사이드바
# ══════════════════════════════════════════════════════════════
SECTIONS = [
    "🏠 개요 & 학습 순서",
    "📖 SQL 기본 문법",
    "🗂️ 데이터 사전 (컬럼 참조)",
    "🛠️ 실습 환경 구축",
    "① SELECT — 데이터 조회",
    "② WHERE — 조건 필터",
    "③ LIKE — 패턴 검색",
    "④ ORDER BY — 정렬",
    "⑤ GROUP BY — 집계",
    "⑥ JOIN — 테이블 결합",
    "⑦ CASE WHEN & COALESCE",
    " 복합 쿼리 실전",
    " 자유 실습 & 연습문제",
]

with st.sidebar:
    st.title("🏠 SQL 교육자료")
    st.caption("주택금융 실무 데이터로 배우는 ANSI SQL")
    st.divider()
    st.markdown("""
**📚 학습 단계**

STEP 1. 개요 & 기본 문법
STEP 2. 데이터 사전 확인 
STEP 3. 실습 환경 구축
STEP 4. SELECT → WHERE → LIKE
STEP 5. ORDER BY → GROUP BY → JOIN
STEP 6. CASE WHEN & COALESCE 
STEP 7. 복합 쿼리 & 자유 실습
""")
    st.divider()
    section = st.radio("단원 선택", SECTIONS, label_visibility="collapsed")

conn = get_db()


# ══════════════════════════════════════════════════════════════
# 0. 개요
# ══════════════════════════════════════════════════════════════
if section == SECTIONS[0]:
    st.markdown('<div class="section-header">🏠 SQL 교육자료 — 주택금융 실무 데이터로 배우는 ANSI SQL</div>',
                unsafe_allow_html=True)
    st.markdown("이 자료는 **주택금융 실무 테이블명·컬럼명**을 그대로 사용한 실습 데이터로 SQL을 단계별로 익힙니다.")
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
### 📋 학습 순서
| 단계 | 내용 |
|------|------|
| **STEP 1** | SQL이란? 기본 문법 구조 |
| **STEP 2** | 데이터 사전 — 테이블·컬럼 한눈에 보기 |
| **STEP 3** | 실습 환경 구축 & 데이터 확인 |
| **STEP 4** | SELECT / WHERE / LIKE |
| **STEP 5** | ORDER BY / GROUP BY / JOIN |
| **STEP 6** | CASE WHEN & COALESCE |
| **STEP 7** | 복합 쿼리 & 자유 실습 |
        """)
    with col2:
        st.markdown("""
### 🗂️ 실습 테이블 (실무명 기반)
| 테이블 | 내용 |
|--------|------|
| `TA_COA311M_CDBSC` | 지역 코드 마스터 |
| `TW_RGG102M_GRNTCRST_DD` | 보증 현황 일별 |
| `TW_RGG101M_GRNTREQCNSL_DD` | 보증금액 상담 일별 |
| `TB_RGE303M_GRNTRVEWAMT` | 연금 최초월지급금 |
| `TB_RGE301M_GRNTRVEHUMNMAT` | 연금 가입자 인적사항 |
| `TB_RGR011M_HSPRC` | 시세 정보 |
        """)
    st.divider()
    st.markdown("### 🔑 핵심 SQL 키워드")
    kw_cols = st.columns(7)
    kw_data = [
        ("SELECT","조회","#1565C0"),("WHERE","조건","#2E7D32"),
        ("LIKE","패턴","#6A1B9A"),("ORDER BY","정렬","#E65100"),
        ("GROUP BY","집계","#AD1457"),("JOIN","결합","#00695C"),
        ("CASE WHEN","분기","#BF360C"),
    ]
    for col, (kw, desc, color) in zip(kw_cols, kw_data):
        col.markdown(f"""<div style="background:{color};color:white;border-radius:10px;
            padding:18px 8px;text-align:center;">
            <div style="font-size:0.9rem;font-weight:700;">{kw}</div>
            <div style="font-size:0.75rem;opacity:0.9;">{desc}</div></div>""",
            unsafe_allow_html=True)
    st.divider()
    st.markdown("""<div class="tip-box">💡 <b>활용법</b> — 모르는 컬럼이 생기면 <b>🗂️ 데이터 사전</b>을 먼저 확인하세요!
    각 예제의 <b>▶ 실행</b> 버튼으로 결과를 확인하고,
    <b>🎯 실습 문제</b>에서 직접 SQL을 작성한 뒤 <b>📋 정답 보기</b>로 비교해보세요.</div>""",
    unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# 1. SQL 기본 문법
# ══════════════════════════════════════════════════════════════
elif section == SECTIONS[1]:
    st.markdown('<div class="section-header">📖 SQL 기본 문법</div>', unsafe_allow_html=True)

    st.markdown("## SQL이란?")
    st.markdown("""
**SQL(Structured Query Language)** 은 관계형 데이터베이스(RDBMS)에서 데이터를 **조회·삽입·수정·삭제**하기 위한 표준 언어입니다.

관계형 DB는 데이터를 **테이블(표)** 형태로 저장하고, 여러 테이블을 **관계(Relation)** 로 연결해 관리합니다.
SQL은 이 테이블들을 대상으로 원하는 데이터를 뽑아내는 질의(Query)를 작성하는 언어입니다.

- **표준화**: ANSI/ISO SQL 표준이 존재하며 Oracle·MySQL·PostgreSQL·SQLite 등 거의 모든 DB에서 동일하게 동작합니다.
- **선언적 언어**: "어떻게(HOW)"가 아닌 "무엇을(WHAT)" 원하는지 기술하면 DB 엔진이 최적의 방법으로 실행합니다.
    """)

    st.divider()
    st.markdown("## SQL 명령어 분류")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""<div style="background:#E3F2FD;border-radius:10px;padding:16px;">
        <b>📥 DML — 데이터 조작</b><br><small>Data Manipulation Language</small><br><br>
        • <code>SELECT</code> — 데이터 조회<br>
        • <code>INSERT</code> — 데이터 삽입<br>
        • <code>UPDATE</code> — 데이터 수정<br>
        • <code>DELETE</code> — 데이터 삭제<br><br>
        <small>⭐ 이 자료에서 집중적으로 다룹니다</small></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div style="background:#F3E5F5;border-radius:10px;padding:16px;">
        <b>🏗️ DDL — 데이터 정의</b><br><small>Data Definition Language</small><br><br>
        • <code>CREATE</code> — 테이블 생성<br>
        • <code>ALTER</code> — 구조 변경<br>
        • <code>DROP</code> — 테이블 삭제<br>
        • <code>TRUNCATE</code> — 전체 삭제</div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""<div style="background:#E8F5E9;border-radius:10px;padding:16px;">
        <b>🔐 DCL — 데이터 제어</b><br><small>Data Control Language</small><br><br>
        • <code>GRANT</code> — 권한 부여<br>
        • <code>REVOKE</code> — 권한 회수<br>
        • <code>COMMIT</code> — 트랜잭션 확정<br>
        • <code>ROLLBACK</code> — 트랜잭션 취소</div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("## SELECT 전체 문법 구조")
    st.code("""-- [ ] 안은 선택 요소 (생략 가능)
SELECT   [DISTINCT] 컬럼1, 컬럼2, 집계함수, ...   -- ⑥ 여섯 번째 실행
FROM     테이블명  [AS 별칭]                        -- ① 가장 먼저 실행
[JOIN    다른테이블  ON 조인조건]                    -- ②
[WHERE   행 필터 조건]                              -- ③ 집계 전 필터
[GROUP BY 그룹 기준 컬럼]                           -- ④
[HAVING  집계 결과 필터]                            -- ⑤ 집계 후 필터
[ORDER BY 정렬 컬럼  [ASC|DESC]]                   -- ⑦
[LIMIT   n];                                       -- ⑧""", language="sql")

    st.markdown("""<div class="warn-box">⚠️ <b>SQL 실행 순서는 작성 순서와 다릅니다!</b><br><br>
    작성 순서: SELECT → FROM → WHERE → GROUP BY → HAVING → ORDER BY<br>
    실행 순서: FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → ORDER BY<br><br>
    이 차이가 중요한 이유: WHERE는 GROUP BY 이전에 실행되기 때문에,
    WHERE 절에서는 집계함수(SUM, AVG 등)를 사용할 수 없습니다.
    집계 결과를 필터링하려면 반드시 HAVING을 사용해야 합니다.</div>""",
    unsafe_allow_html=True)

    st.divider()
    st.markdown("## 주요 데이터 타입 & 핵심 개념")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
| 타입 | 설명 | 실습 예시 |
|------|------|-----------|
| `INTEGER` | 정수 | GRNT_SPLY_CNT, AGE_YRCT |
| `REAL` / `FLOAT` | 실수 | GRNT_AMT, MM_PYAT_AMT |
| `TEXT` / `VARCHAR` | 문자열 | GRNT_NO, CD_NM |
| `DATE` | 날짜 | '20230101' (YYYYMMDD) |
        """)
    with col2:
        st.markdown("""
| 개념 | 설명 |
|------|------|
| `NULL` | 값이 없음 (0·빈 문자열과 전혀 다름) |
| `PRIMARY KEY (PK)` | 각 행을 유일하게 식별하는 컬럼 |
| `FOREIGN KEY (FK)` | 다른 테이블의 PK를 참조하는 컬럼 |
| `AS (Alias)` | 컬럼·테이블에 읽기 쉬운 별칭 부여 |
| `DISTINCT` | 중복된 행 제거 |
        """)

    st.divider()
    st.markdown("## 연산자 & 집계함수")
    tab1, tab2, tab3 = st.tabs(["비교 연산자", "논리 연산자", "집계 함수"])
    with tab1:
        st.markdown("""
| 연산자 | 의미 | 예시 |
|--------|------|------|
| `=` | 같다 | `BASIS_DY = '20230630'` |
| `<>` 또는 `!=` | 다르다 | `PNSN_GV_METH_DVCD <> '07'` |
| `>` / `<` | 크다 / 작다 | `GRNT_SPLY_CNT > 10000` |
| `>=` / `<=` | 이상 / 이하 | `BASIS_DY >= '20220101'` |
| `BETWEEN a AND b` | a 이상 b 이하 (양 끝 포함) | `BASIS_DY BETWEEN '20200101' AND '20250630'` |
| `IN (...)` | 목록 중 하나 | `PNSN_GV_METH_DVCD IN ('07', '08', '09')` |
| `IS NULL` | 값이 NULL | `LAST_CNCL_DY IS NULL` |
| `IS NOT NULL` | NULL이 아님 | `MM_PYAT_AMT IS NOT NULL` |
        """)
    with tab2:
        st.markdown("""
| 연산자 | 의미 | 예시 |
|--------|------|------|
| `AND` | 두 조건 모두 참 | `BASIS_DY = '20230630' AND GRNT_SPLY_CNT > 5000` |
| `OR` | 둘 중 하나 참 | `PNSN_GV_METH_DVCD = '07' OR PNSN_GV_METH_DVCD = '08'` |
| `NOT` | 조건 부정 | `NOT PNSN_GV_METH_DVCD = '09'` |
| `LIKE` | 패턴 매칭 | `GRNT_NO LIKE 'G-2023%'` |

**우선순위**: `NOT` > `AND` > `OR` — 괄호로 명시적으로 묶는 것을 권장합니다.
        """)
    with tab3:
        st.markdown("""
| 함수 | 설명 | NULL 처리 |
|------|------|-----------|
| `COUNT(*)` | 전체 행 수 | NULL 포함 |
| `COUNT(col)` | 특정 컬럼 행 수 | NULL 제외 |
| `SUM(col)` | 합계 | NULL 무시 |
| `AVG(col)` | 평균 | NULL 무시 |
| `MAX(col)` | 최댓값 | NULL 무시 |
| `MIN(col)` | 최솟값 | NULL 무시 |
| `ROUND(값, n)` | 소수점 n자리 반올림 | — |
| `COALESCE(a, b)` | a가 NULL이면 b 반환 | NULL 대체 |
        """)


# ══════════════════════════════════════════════════════════════
# 2. 데이터 사전 
# ══════════════════════════════════════════════════════════════
elif section == SECTIONS[2]:
    st.markdown('<div class="section-header">🗂️ 데이터 사전 — 컬럼 참조표</div>', unsafe_allow_html=True)
    st.markdown("쿼리 작성 중 **'이 컬럼이 뭐였지?'** 싶을 때 바로 여기서 확인하세요.")
    st.divider()

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📍 TA_COA311M_CDBSC",
        "📋 TW_RGG102M_GRNTCRST_DD",
        "💰 TW_RGG101M_GRNTREQCNSL_DD",
        "🏦 TB_RGE303M_GRNTRVEWAMT",
        "👤 TB_RGE301M_GRNTRVEHUMNMAT",
        "📈 TB_RGR011M_HSPRC",
    ])

    with tab1:
        st.markdown("### 📍 TA_COA311M_CDBSC — 지역 코드 마스터")
        st.markdown("공통코드 테이블. `CD_GRP_ID = 'COA0083'` 조건으로 지역 코드를 필터합니다.")
        st.markdown("""
| 컬럼명 | 타입 | 설명 | 예시값 |
|--------|------|------|--------|
| `CD_ID` | TEXT | **지역코드 (PK)** | `'11'`=서울, `'41'`=경기, `'28'`=인천 |
| `CD_NM` | TEXT | 지역명 | `'서울'`, `'경기'`, `'부산'` |
| `CD_GRP_ID` | TEXT | 코드그룹 ID | `'COA0083'` (지역 그룹) |
| `ZONE_TYPE` | TEXT | 권역 구분 | `'수도권'`, `'지방'` |
        """)
        st.markdown("""<div class="tip-box">💡 실무 쿼리에서는 <code>WHERE CD_GRP_ID = 'COA0083' AND CD_ID = B.HS_LOC_ZONE_DVCD</code>
        형태로 보증 테이블과 조인해 지역명을 가져옵니다.</div>""", unsafe_allow_html=True)
        df, _ = run_sql(conn, "SELECT * FROM TA_COA311M_CDBSC")
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("### 📋 TW_RGG102M_GRNTCRST_DD — 보증 현황 일별")
        st.markdown("보증 상태를 기준일자별로 기록한 핵심 테이블입니다.")
        st.markdown("""
| 컬럼명 | 타입 | 설명 | 예시값 |
|--------|------|------|--------|
| `BASIS_DY` | TEXT | **기준일자** (YYYYMMDD) | `'20230630'` |
| `GRNT_NO` | TEXT | **보증번호** | `'G-2023-0001'` |
| `HS_LOC_ZONE_DVCD` | TEXT | 주택소재지역코드 → TA_COA311M_CDBSC.CD_ID | `'11'`=서울 |
| `PNSN_GV_METH_DVCD` | TEXT | **지급방식코드** | `'07'`=전세, `'08'`=구입, `'09'`=중도금 |
| `GRNT_SPLY_CNT` | INTEGER | **공급건수** | `12400` |
| `GRNT_GEN_CNCL_CNT` | INTEGER | 일반해지건수 | `120` |
| `GRNT_UNEX_CNCL_CNT` | INTEGER | 미실행해지건수 | `30` |
| `GRNT_PRMS_RETR_CNCL_CNT` | INTEGER | 약정채무상환해지건수 | `10` |
| `APRS_EVAL_AMT` | REAL | 감정평가금액(주택가격, 억원) | `4.2` |
        """)
        st.markdown("""<div class="tip-box">💡 해지건수 합계 = <code>GRNT_GEN_CNCL_CNT + GRNT_UNEX_CNCL_CNT + GRNT_PRMS_RETR_CNCL_CNT</code>
        → 실무 쿼리에서 "해지건수"로 자주 집계됩니다.</div>""", unsafe_allow_html=True)
        df, _ = run_sql(conn, "SELECT * FROM TW_RGG102M_GRNTCRST_DD ORDER BY BASIS_DY, GRNT_NO")
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab3:
        st.markdown("### 💰 TW_RGG101M_GRNTREQCNSL_DD — 보증금액 상담 일별")
        st.markdown("보증금액 및 최종 해지일을 관리합니다.")
        st.markdown("""
| 컬럼명 | 타입 | 설명 | 예시값 |
|--------|------|------|--------|
| `BASIS_DY` | TEXT | 기준일자 (YYYYMMDD) | `'20230630'` |
| `GRNT_NO` | TEXT | 보증번호 (FK → TW_RGG102M) | `'G-2023-0001'` |
| `GRNT_AMT` | REAL | **보증금액** (억원) | `1750.0` |
| `LAST_CNCL_DY` | TEXT | 최종해지일자 (NULL=미해지) | `'20241201'`, NULL |
        """)
        st.markdown("""<div class="warn-box">⚠️ <code>LAST_CNCL_DY IS NULL</code>이면 아직 해지되지 않은 활성 보증입니다.
        NULL 여부를 반드시 확인하세요.</div>""", unsafe_allow_html=True)
        df, _ = run_sql(conn, "SELECT * FROM TW_RGG101M_GRNTREQCNSL_DD ORDER BY BASIS_DY, GRNT_NO")
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab4:
        st.markdown("### 🏦 TB_RGE303M_GRNTRVEWAMT — 연금 최초월지급금")
        st.markdown("주택연금 가입 시 확정된 월지급금 정보입니다.")
        st.markdown("""
| 컬럼명 | 타입 | 설명 | 예시값 |
|--------|------|------|--------|
| `GRNT_NO` | TEXT | 보증번호 (FK) | `'G-2023-0001'` |
| `MM_PYAT_AMT` | REAL | **월지급금액** (만원, NULL 가능) | `155.0`, NULL |
        """)
        st.markdown("""<div class="tip-box">💡 <code>MM_PYAT_AMT</code>가 NULL인 경우 <code>COALESCE(MM_PYAT_AMT, 0)</code>으로
        0 처리하면 집계 시 오류를 방지할 수 있습니다.</div>""", unsafe_allow_html=True)
        df, _ = run_sql(conn, "SELECT * FROM TB_RGE303M_GRNTRVEWAMT")
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab5:
        st.markdown("### 👤 TB_RGE301M_GRNTRVEHUMNMAT — 연금 가입자 인적사항")
        st.markdown("가입자의 연령 정보를 담고 있습니다.")
        st.markdown("""
| 컬럼명 | 타입 | 설명 | 예시값 |
|--------|------|------|--------|
| `GRNT_NO` | TEXT | 보증번호 (FK) | `'G-2023-0001'` |
| `AGE_YRCT` | INTEGER | **연령** | `68`, `72` |
        """)
        st.markdown("""<div class="tip-box">💡 실무 쿼리에서 <code>MIN(AGE_YRCT)</code>로 최저연령을 구합니다.</div>""",
        unsafe_allow_html=True)
        df, _ = run_sql(conn, "SELECT * FROM TB_RGE301M_GRNTRVEHUMNMAT")
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab6:
        st.markdown("### 📈 TB_RGR011M_HSPRC — 시세 정보")
        st.markdown("KB 시세 또는 부동산원 시세를 월별로 관리합니다.")
        st.markdown("""
| 컬럼명 | 타입 | 설명 | 예시값 |
|--------|------|------|--------|
| `BASIS_YM` | TEXT | 기준연월 (YYYYMM) | `'202512'` |
| `GRNT_NO` | TEXT | 보증번호 (FK) | `'G-2023-0001'` |
| `KAB_TRD_AVG_PRC` | REAL | KB거래평균가격 (억원) | `5.1` |
| `KB_TRD_AVG_PRC` | REAL | KB시세평균가격 (억원) | `5.0` |
| `KAB_SISE_RSCH_DY` | TEXT | KB시세조사일 | `'0'`=부동산원, `'1'`=KB |
        """)
        st.markdown("""<div class="tip-box">💡 실무 쿼리에서 시세 우선순위:
        <code>COALESCE(KAB_TRD_AVG_PRC, KB_TRD_AVG_PRC, 0) * 10000</code>으로
        억원→만원 환산하고, NULL이면 0으로 대체합니다.
        <br>KAB_SISE_RSCH_DY가 '0'이 아니면 KB시세, '0'이면 부동산원 시세입니다.</div>""",
        unsafe_allow_html=True)
        df, _ = run_sql(conn, "SELECT * FROM TB_RGR011M_HSPRC")
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### 🔗 테이블 관계 (ERD)")
    st.code("""
  TA_COA311M_CDBSC (지역 마스터, CD_GRP_ID='COA0083')
  ┌──────────────────────┐
  │ CD_ID (PK)           │◀──────────────────────────────────────┐
  │ CD_NM (지역명)        │                                       │
  │ ZONE_TYPE (수도권/지방)│                                       │
  └──────────────────────┘                                       │
                                                                  │
  TW_RGG102M_GRNTCRST_DD (보증현황)                              │
  ┌───────────────────────────────┐                              │
  │ BASIS_DY  (기준일자)           │                              │
  │ GRNT_NO   (보증번호)          │─── GRNT_NO ──▶ TB_RGE303M_GRNTRVEWAMT
  │ HS_LOC_ZONE_DVCD (지역코드) ──┘──────────────────────────────┘
  │ PNSN_GV_METH_DVCD (지급방식)  │─── GRNT_NO ──▶ TB_RGE301M_GRNTRVEHUMNMAT
  │ GRNT_SPLY_CNT  (공급건수)     │
  │ GRNT_*_CNCL_CNT (해지건수들)  │
  │ APRS_EVAL_AMT (감정가)        │
  └───────────────────────────────┘
          │ BASIS_DY + GRNT_NO
          ▼
  TW_RGG101M_GRNTREQCNSL_DD (보증금액)      TB_RGR011M_HSPRC (시세)
  ┌───────────────────────┐                  ┌────────────────────┐
  │ BASIS_DY              │                  │ BASIS_YM           │
  │ GRNT_NO               │                  │ GRNT_NO            │
  │ GRNT_AMT (보증금액)   │                  │ KAB_TRD_AVG_PRC    │
  │ LAST_CNCL_DY (해지일) │                  │ KB_TRD_AVG_PRC     │
  └───────────────────────┘                  └────────────────────┘
    """, language="text")


# ══════════════════════════════════════════════════════════════
# 3. 실습 환경
# ══════════════════════════════════════════════════════════════
elif section == SECTIONS[3]:
    st.markdown('<div class="section-header">🛠️ 실습 환경 구축</div>', unsafe_allow_html=True)

    st.markdown("## Python + SQLite 실습 환경")
    st.markdown("Python 내장 모듈 `sqlite3`와 `pandas`를 사용합니다. 별도 DB 서버 없이 로컬에서 즉시 실행 가능합니다.")
    st.code("""import sqlite3
import pandas as pd

conn = sqlite3.connect(":memory:")   # 인메모리 DB (임시)
# 실무에서는 Trino 엔진 사용:
# engine = create_engine("trino://user@host:port/iceberg/bronze")

def run(sql):
    \"\"\"SQL 실행 후 DataFrame 반환\"\"\"
    return pd.read_sql_query(sql, conn)""", language="python")

    st.divider()
    st.markdown("## 📋 실습 데이터 미리보기")
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "TA_COA311M_CDBSC",
        "TW_RGG102M_GRNTCRST_DD",
        "TW_RGG101M_GRNTREQCNSL_DD",
        "TB_RGE303M_GRNTRVEWAMT",
        "TB_RGE301M_GRNTRVEHUMNMAT",
        "TB_RGR011M_HSPRC",
    ])
    with tab1:
        df, _ = run_sql(conn, "SELECT * FROM TA_COA311M_CDBSC")
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption("8개 지역 | ZONE_TYPE: 수도권(서울·경기·인천) / 지방(부산·대구·광주·대전·강원)")
    with tab2:
        df, _ = run_sql(conn, "SELECT * FROM TW_RGG102M_GRNTCRST_DD ORDER BY BASIS_DY, GRNT_NO")
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption("32건 | BASIS_DY: 20200630~20230630 | PNSN_GV_METH_DVCD: 07=전세/08=구입/09=중도금")
    with tab3:
        df, _ = run_sql(conn, "SELECT * FROM TW_RGG101M_GRNTREQCNSL_DD ORDER BY BASIS_DY, GRNT_NO")
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption("32건 | GRNT_AMT 단위: 억원 | LAST_CNCL_DY=NULL이면 미해지(활성)")
    with tab4:
        df, _ = run_sql(conn, "SELECT * FROM TB_RGE303M_GRNTRVEWAMT")
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption("24건 | MM_PYAT_AMT 단위: 만원 | NULL=지급금 미확정")
    with tab5:
        df, _ = run_sql(conn, "SELECT * FROM TB_RGE301M_GRNTRVEHUMNMAT")
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption("24건 | AGE_YRCT: 가입자 연령(세)")
    with tab6:
        df, _ = run_sql(conn, "SELECT * FROM TB_RGR011M_HSPRC")
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption("9건 | BASIS_YM=202512 샘플 | KAB_SISE_RSCH_DY: '0'=부동산원, '1'=KB")

    st.markdown("""<div class="good-box">✅ 환경 구축 완료! 모르는 컬럼은 <b>🗂️ 데이터 사전</b>에서 확인하고 <b>① SELECT</b>부터 시작하세요.</div>""",
    unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# 4. SELECT
# ══════════════════════════════════════════════════════════════
elif section == SECTIONS[4]:
    st.markdown('<div class="section-header">① SELECT — 데이터 조회</div>', unsafe_allow_html=True)

    st.markdown("""
`SELECT` 는 SQL의 핵심 명령으로, **테이블에서 원하는 데이터를 읽어오는** 구문입니다.
조회 결과는 항상 새로운 가상 테이블(Result Set) 형태로 반환됩니다.
    """)
    st.markdown("""<div class="syntax-box">
SELECT  [DISTINCT]  컬럼1, 컬럼2, ...  &nbsp;← 조회할 컬럼 (* 는 전체 컬럼)<br>
FROM    테이블명;                       &nbsp;← 어떤 테이블에서 가져올지
</div>""", unsafe_allow_html=True)

    st.divider()
    exs = [
        ("예제 1 — 전체 컬럼 조회 (SELECT *)",
         "`*`는 모든 컬럼을 의미합니다. 테이블 구조를 처음 파악할 때 편리합니다.",
         "SELECT *\nFROM   TW_RGG102M_GRNTCRST_DD;",
         "warn", "⚠️ 실무에서는 <code>SELECT *</code> 대신 필요한 컬럼만 명시하세요."),
        ("예제 2 — 특정 컬럼만 조회",
         "보증번호·기준일자·지급방식코드·공급건수만 가져옵니다.",
         "SELECT GRNT_NO, BASIS_DY, PNSN_GV_METH_DVCD, GRNT_SPLY_CNT\nFROM   TW_RGG102M_GRNTCRST_DD;",
         None, None),
        ("예제 3 — 별칭(AS) + 산술 연산",
         "`AS`로 한글 별칭을 붙이고, 해지건수 합계를 계산합니다.",
         """SELECT
    GRNT_NO                                                  AS 보증번호,
    BASIS_DY                                                 AS 기준일자,
    GRNT_SPLY_CNT                                            AS 공급건수,
    GRNT_GEN_CNCL_CNT + GRNT_UNEX_CNCL_CNT
        + GRNT_PRMS_RETR_CNCL_CNT                           AS 해지건수합계,
    APRS_EVAL_AMT                                            AS "감정가(억)"
FROM TW_RGG102M_GRNTCRST_DD;""",
         "tip", "💡 별칭(AS)은 SELECT에서 정의되므로 같은 SELECT의 WHERE 절에서는 쓸 수 없습니다. ORDER BY에서는 사용 가능합니다."),
        ("예제 4 — DISTINCT 중복 제거",
         "어떤 지급방식코드가 있는지 고유한 값만 조회합니다.",
         "SELECT DISTINCT PNSN_GV_METH_DVCD AS 지급방식코드\nFROM   TW_RGG102M_GRNTCRST_DD;",
         None, None),
        ("예제 5 — LIMIT으로 상위 N행만",
         "처음 5행만 빠르게 확인합니다.",
         "SELECT GRNT_NO, BASIS_DY, GRNT_SPLY_CNT\nFROM   TW_RGG102M_GRNTCRST_DD\nLIMIT  5;",
         "tip", "💡 Oracle은 <code>WHERE ROWNUM &lt;= 5</code>, SQL Server는 <code>SELECT TOP 5</code>를 사용합니다."),
    ]
    for title, desc, sql, box_type, box_msg in exs:
        with st.expander(title, expanded=True):
            st.caption(desc)
            if box_type == "warn":
                st.markdown(f'<div class="warn-box">{box_msg}</div>', unsafe_allow_html=True)
            elif box_type == "tip":
                st.markdown(f'<div class="tip-box">{box_msg}</div>', unsafe_allow_html=True)
            st.code(sql, language="sql")
            show_result(conn, sql, f"sel_{title}")

    st.divider()
    practice_block(conn,
        "TW_RGG102M_GRNTCRST_DD 에서 보증번호·기준일자·지급방식코드·공급건수와 함께\n"
        "해지건수 합계(일반+미실행+약정채무상환)를 '해지건수합계' 별칭으로 조회하세요.",
        """SELECT
    GRNT_NO                                                   AS 보증번호,
    BASIS_DY                                                  AS 기준일자,
    PNSN_GV_METH_DVCD                                         AS 지급방식코드,
    GRNT_SPLY_CNT                                             AS 공급건수,
    GRNT_GEN_CNCL_CNT + GRNT_UNEX_CNCL_CNT
        + GRNT_PRMS_RETR_CNCL_CNT                            AS 해지건수합계
FROM TW_RGG102M_GRNTCRST_DD;""",
        "p_select",
        hint="세 컬럼을 + 연산자로 더하고 AS로 별칭을 붙이세요.")


# ══════════════════════════════════════════════════════════════
# 5. WHERE
# ══════════════════════════════════════════════════════════════
elif section == SECTIONS[5]:
    st.markdown('<div class="section-header">② WHERE — 조건 필터</div>', unsafe_allow_html=True)

    st.markdown("""
`WHERE` 절은 FROM으로 불러온 전체 데이터 중 **조건을 만족하는 행(Row)만** 남기는 필터입니다.
집계함수(`SUM`, `AVG` 등)는 WHERE에서 사용 불가 — 집계 조건은 반드시 `HAVING`을 사용합니다.
    """)
    st.markdown("""<div class="syntax-box">
SELECT 컬럼 FROM 테이블<br>
WHERE  조건식;  &nbsp;← TRUE인 행만 결과에 포함
</div>""", unsafe_allow_html=True)

    st.divider()
    exs = [
        ("예제 1 — 특정 기준일자",
         "20230630 기준 보증 데이터만 조회합니다.",
         "SELECT GRNT_NO, BASIS_DY, PNSN_GV_METH_DVCD, GRNT_SPLY_CNT\nFROM   TW_RGG102M_GRNTCRST_DD\nWHERE  BASIS_DY = '20230630';", None, None),
        ("예제 2 — 비교 연산자 (공급건수 1만 건 이상)",
         "공급건수가 10,000건 이상인 대규모 보증 건만 조회합니다.",
         "SELECT GRNT_NO, BASIS_DY, GRNT_SPLY_CNT, APRS_EVAL_AMT\nFROM   TW_RGG102M_GRNTCRST_DD\nWHERE  GRNT_SPLY_CNT >= 10000;", None, None),
        ("예제 3 — AND로 두 조건 동시 적용",
         "20230630 기준이면서 공급건수 5,000건 이상인 건. AND는 두 조건 모두 참일 때만 포함합니다.",
         "SELECT GRNT_NO, BASIS_DY, PNSN_GV_METH_DVCD, GRNT_SPLY_CNT\nFROM   TW_RGG102M_GRNTCRST_DD\nWHERE  BASIS_DY = '20230630'\n  AND  GRNT_SPLY_CNT >= 5000;", None, None),
        ("예제 4 — IN으로 지급방식 필터",
         "지급방식코드가 07(전세) 또는 08(구입)인 상품을 조회합니다. 실무 쿼리에서 IN ('07','08','09')처럼 자주 사용합니다.",
         "SELECT GRNT_NO, PNSN_GV_METH_DVCD, GRNT_SPLY_CNT\nFROM   TW_RGG102M_GRNTCRST_DD\nWHERE  PNSN_GV_METH_DVCD IN ('07', '08');",
         "tip", "💡 IN 목록이 길어지면 서브쿼리와 결합 가능: <code>WHERE HS_LOC_ZONE_DVCD IN (SELECT CD_ID FROM TA_COA311M_CDBSC WHERE ZONE_TYPE = '수도권')</code>"),
        ("예제 5 — BETWEEN 날짜 범위 조건",
         "20200101~20250630 사이 데이터. 실무 쿼리에서 자주 보이는 날짜 범위 조건입니다.",
         "SELECT GRNT_NO, BASIS_DY, GRNT_SPLY_CNT\nFROM   TW_RGG102M_GRNTCRST_DD\nWHERE  BASIS_DY BETWEEN '20200101' AND '20250630';",
         "tip", "💡 날짜가 TEXT이지만 'YYYYMMDD' 형식이면 BETWEEN으로 범위 비교가 올바르게 동작합니다."),
        ("예제 6 — IS NULL / IS NOT NULL",
         "LAST_CNCL_DY가 NULL이면 아직 해지되지 않은 활성 보증입니다.",
         "-- 미해지(활성) 보증\nSELECT GRNT_NO, GRNT_AMT, LAST_CNCL_DY\nFROM   TW_RGG101M_GRNTREQCNSL_DD\nWHERE  LAST_CNCL_DY IS NULL;\n\n-- 이미 해지된 보증\nSELECT GRNT_NO, GRNT_AMT, LAST_CNCL_DY\nFROM   TW_RGG101M_GRNTREQCNSL_DD\nWHERE  LAST_CNCL_DY IS NOT NULL;",
         "warn", "⚠️ <code>= NULL</code>은 항상 FALSE를 반환합니다. NULL 비교는 반드시 <code>IS NULL</code>을 사용하세요."),
    ]
    for title, desc, sql, box_type, box_msg in exs:
        with st.expander(title, expanded=True):
            st.caption(desc)
            if box_type == "warn":
                st.markdown(f'<div class="warn-box">{box_msg}</div>', unsafe_allow_html=True)
            elif box_type == "tip":
                st.markdown(f'<div class="tip-box">{box_msg}</div>', unsafe_allow_html=True)
            st.code(sql, language="sql")
            show_result(conn, sql, f"wh_{title}")

    st.divider()
    practice_block(conn,
        "TW_RGG102M_GRNTCRST_DD 에서 BASIS_DY가 '20220101'~'20250630' 사이이고,\n"
        "지급방식코드가 '07'(전세) 이며, 공급건수가 10,000건 이상인 건을 공급건수 내림차순으로 조회하세요.",
        """SELECT GRNT_NO, BASIS_DY, PNSN_GV_METH_DVCD, GRNT_SPLY_CNT
FROM   TW_RGG102M_GRNTCRST_DD
WHERE  BASIS_DY BETWEEN '20220101' AND '20250630'
  AND  PNSN_GV_METH_DVCD = '07'
  AND  GRNT_SPLY_CNT >= 10000
ORDER BY GRNT_SPLY_CNT DESC;""",
        "p_where",
        hint="BETWEEN, =, >= 를 AND로 조합하고 ORDER BY를 추가하세요.")


# ══════════════════════════════════════════════════════════════
# 6. LIKE
# ══════════════════════════════════════════════════════════════
elif section == SECTIONS[6]:
    st.markdown('<div class="section-header">③ LIKE — 패턴 검색</div>', unsafe_allow_html=True)

    st.markdown("""
`LIKE` 는 문자열 컬럼에서 **특정 패턴**에 맞는 값을 검색합니다.
정확한 값을 모르거나, 값의 일부만 알 때 사용합니다.
    """)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""<div class="syntax-box">
WHERE 컬럼 LIKE '패턴'<br><br>
%  : 0개 이상의 임의 문자<br>
_  : 정확히 1개의 임의 문자
</div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
| 패턴 | 의미 | 보증번호 매칭 예 |
|------|------|------|
| `'G-2023%'` | G-2023으로 시작 | G-2023-0001 ✅ |
| `'%-0005'` | -0005로 끝남 | G-2021-0005 ✅ |
| `'%2022%'` | 2022 포함 | G-2022-0003 ✅ |
| `'G-____-%'` | G- + 4자리 + - | 모든 보증번호 ✅ |
        """)

    st.divider()
    exs = [
        ("예제 1 — 특정 연도 보증번호 검색",
         "보증번호가 'G-2023'으로 시작하는 건만 조회합니다.",
         "SELECT GRNT_NO, BASIS_DY, PNSN_GV_METH_DVCD, GRNT_SPLY_CNT\nFROM   TW_RGG102M_GRNTCRST_DD\nWHERE  GRNT_NO LIKE 'G-2023%';",
         "tip", "💡 인덱스 활용 가능: <code>LIKE '값%'</code> / 인덱스 미사용(Full Scan): <code>LIKE '%값%'</code>"),
        ("예제 2 — 특정 번호로 끝나는 검색",
         "일련번호가 0003으로 끝나는 건을 모든 연도에서 찾습니다.",
         "SELECT GRNT_NO, BASIS_DY, GRNT_SPLY_CNT\nFROM   TW_RGG102M_GRNTCRST_DD\nWHERE  GRNT_NO LIKE '%-0003';", None, None),
        ("예제 3 — 지역명 포함 검색",
         "지역명에 '서' 가 포함된 지역(서울 등)을 찾습니다.",
         "SELECT DISTINCT CD_ID, CD_NM, ZONE_TYPE\nFROM   TA_COA311M_CDBSC\nWHERE  CD_NM LIKE '%서%';",
         "warn", "⚠️ <code>LIKE '%값%'</code>(앞에 %)는 Full Table Scan이 발생합니다."),
        ("예제 4 — _ 와일드카드 (글자 수 고정)",
         "'G-YYYY-NNNN' 형식인 보증번호를 검증합니다. _는 정확히 1글자입니다.",
         "SELECT GRNT_NO\nFROM   TW_RGG102M_GRNTCRST_DD\nWHERE  GRNT_NO LIKE 'G-____-____';", None, None),
    ]
    for title, desc, sql, box_type, box_msg in exs:
        with st.expander(title, expanded=True):
            st.caption(desc)
            if box_type == "warn":
                st.markdown(f'<div class="warn-box">{box_msg}</div>', unsafe_allow_html=True)
            elif box_type == "tip":
                st.markdown(f'<div class="tip-box">{box_msg}</div>', unsafe_allow_html=True)
            st.code(sql, language="sql")
            show_result(conn, sql, f"lk_{title}")

    st.divider()
    practice_block(conn,
        "'G-2021' 또는 'G-2022'로 시작하는 보증번호 중 공급건수가 5,000건 이상인 건을 공급건수 내림차순으로 조회하세요.",
        """SELECT GRNT_NO, BASIS_DY, PNSN_GV_METH_DVCD, GRNT_SPLY_CNT
FROM   TW_RGG102M_GRNTCRST_DD
WHERE  (GRNT_NO LIKE 'G-2021%' OR GRNT_NO LIKE 'G-2022%')
  AND  GRNT_SPLY_CNT >= 5000
ORDER BY GRNT_SPLY_CNT DESC;""",
        "p_like",
        hint="LIKE 조건 두 개를 OR로 묶고 괄호로 감싼 뒤 AND로 공급건수 조건을 추가하세요.")


# ══════════════════════════════════════════════════════════════
# 7. ORDER BY
# ══════════════════════════════════════════════════════════════
elif section == SECTIONS[7]:
    st.markdown('<div class="section-header">④ ORDER BY — 정렬</div>', unsafe_allow_html=True)

    st.markdown("""
`ORDER BY` 는 결과를 원하는 기준으로 **정렬**합니다.
SQL 실행 순서상 **가장 마지막**에 적용되므로, SELECT에서 정의한 별칭(AS)을 ORDER BY에서 사용할 수 있습니다.
    """)
    st.markdown("""<div class="syntax-box">
SELECT 컬럼 FROM 테이블<br>
ORDER BY 컬럼1 [ASC|DESC], 컬럼2 [ASC|DESC];<br><br>
ASC  : 오름차순 (기본값, 생략 가능)<br>
DESC : 내림차순
</div>""", unsafe_allow_html=True)

    st.divider()
    exs = [
        ("예제 1 — 공급건수 내림차순",
         "가장 많이 공급된 보증 건부터 정렬합니다.",
         "SELECT GRNT_NO, BASIS_DY, PNSN_GV_METH_DVCD, GRNT_SPLY_CNT\nFROM   TW_RGG102M_GRNTCRST_DD\nORDER BY GRNT_SPLY_CNT DESC;"),
        ("예제 2 — 다중 정렬 (기준일자↑ + 보증금액↓)",
         "기준일자 오름차순으로 먼저 정렬하고, 같은 일자 내에서는 보증금액이 큰 순으로 정렬합니다.",
         "SELECT A.BASIS_DY, A.GRNT_NO, B.GRNT_AMT\nFROM   TW_RGG102M_GRNTCRST_DD A\nJOIN   TW_RGG101M_GRNTREQCNSL_DD B ON A.GRNT_NO = B.GRNT_NO\nORDER BY A.BASIS_DY ASC, B.GRNT_AMT DESC;"),
        ("예제 3 — SELECT 별칭으로 정렬",
         "SELECT에서 정의한 별칭(총공급건수)을 ORDER BY에서 바로 사용합니다.",
         "SELECT BASIS_DY AS 기준일자, SUM(GRNT_SPLY_CNT) AS 총공급건수\nFROM   TW_RGG102M_GRNTCRST_DD\nGROUP BY BASIS_DY\nORDER BY 총공급건수 DESC;"),
        ("예제 4 — WHERE + ORDER BY 조합",
         "20230630 기준 보증 데이터를 공급건수 높은 순으로 정렬합니다.",
         "SELECT GRNT_NO, PNSN_GV_METH_DVCD, GRNT_SPLY_CNT, APRS_EVAL_AMT\nFROM   TW_RGG102M_GRNTCRST_DD\nWHERE  BASIS_DY = '20230630'\nORDER BY GRNT_SPLY_CNT DESC;"),
    ]
    for title, desc, sql in exs:
        with st.expander(title, expanded=True):
            st.caption(desc)
            st.code(sql, language="sql")
            show_result(conn, sql, f"ord_{title}")

    st.divider()
    practice_block(conn,
        "TB_RGE303M_GRNTRVEWAMT 에서 MM_PYAT_AMT(월지급금)이 NULL이 아닌 건만 조회하되,\n월지급금 내림차순으로 정렬하세요.",
        """SELECT GRNT_NO AS 보증번호, MM_PYAT_AMT AS "월지급금(만원)"
FROM   TB_RGE303M_GRNTRVEWAMT
WHERE  MM_PYAT_AMT IS NOT NULL
ORDER BY MM_PYAT_AMT DESC;""",
        "p_order",
        hint="IS NOT NULL 조건과 ORDER BY DESC를 조합하세요.")


# ══════════════════════════════════════════════════════════════
# 8. GROUP BY
# ══════════════════════════════════════════════════════════════
elif section == SECTIONS[8]:
    st.markdown('<div class="section-header">⑤ GROUP BY — 집계</div>', unsafe_allow_html=True)

    st.markdown("""
`GROUP BY` 는 특정 컬럼의 값이 같은 행들을 **하나의 그룹으로 묶고**, 각 그룹에 집계함수를 적용합니다.
예) 기준일자별 공급건수 합계, 지급방식별 평균 감정가.

`HAVING` 은 GROUP BY로 만들어진 **그룹에 대해 조건을 필터링**합니다.
    """)
    st.markdown("""<div class="syntax-box">
SELECT   그룹컬럼, 집계함수(컬럼)<br>
FROM     테이블<br>
[WHERE   집계 전 행 필터]    ← 먼저 적용됨<br>
GROUP BY 그룹컬럼<br>
[HAVING  집계 후 그룹 필터]  ← 나중에 적용됨<br>
[ORDER BY ...];
</div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**WHERE vs HAVING**")
        st.markdown("""
| 구분 | WHERE | HAVING |
|------|-------|--------|
| 적용 시점 | GROUP BY **이전** | GROUP BY **이후** |
| 필터 대상 | 개별 **행** | 집계된 **그룹** |
| 집계함수 | ❌ 사용 불가 | ✅ 사용 가능 |
        """)
    with col2:
        st.markdown("""<div class="warn-box">
⚠️ <b>GROUP BY 핵심 규칙</b><br><br>
SELECT에 있는 컬럼 중 집계함수로 감싸지 않은 컬럼은<br>
반드시 GROUP BY에도 포함해야 합니다.<br><br>
✅ 올바른 예:<br>
<code>SELECT BASIS_DY, PNSN_GV_METH_DVCD, COUNT(*)</code><br>
<code>GROUP BY BASIS_DY, PNSN_GV_METH_DVCD</code><br><br>
❌ 오류:<br>
<code>SELECT BASIS_DY, PNSN_GV_METH_DVCD, COUNT(*)</code><br>
<code>GROUP BY BASIS_DY</code>  ← PNSN_GV_METH_DVCD 누락!
</div>""", unsafe_allow_html=True)

    st.divider()
    exs = [
        ("예제 1 — 기준일자별 총 공급건수",
         "기준일자별로 전체 보증 공급건수와 보증 건수를 구합니다.",
         """SELECT
    BASIS_DY                    AS 기준일자,
    COUNT(*)                    AS 보증건수,
    SUM(GRNT_SPLY_CNT)          AS 총공급건수,
    ROUND(SUM(APRS_EVAL_AMT),1) AS "총감정가(억)"
FROM   TW_RGG102M_GRNTCRST_DD
GROUP BY BASIS_DY
ORDER BY BASIS_DY;"""),
        ("예제 2 — 지급방식별 통계",
         "지급방식코드별 평균·최대·최소 공급건수를 비교합니다.",
         """SELECT
    PNSN_GV_METH_DVCD               AS 지급방식코드,
    COUNT(*)                         AS 데이터건수,
    ROUND(AVG(GRNT_SPLY_CNT), 0)    AS 평균공급건수,
    MAX(GRNT_SPLY_CNT)               AS 최대공급건수,
    MIN(GRNT_SPLY_CNT)               AS 최소공급건수
FROM   TW_RGG102M_GRNTCRST_DD
GROUP BY PNSN_GV_METH_DVCD
ORDER BY 평균공급건수 DESC;"""),
        ("예제 3 — HAVING으로 집계 결과 필터",
         "평균 공급건수가 5,000건 이상인 지급방식만 조회합니다.",
         """SELECT
    PNSN_GV_METH_DVCD,
    ROUND(AVG(GRNT_SPLY_CNT), 0) AS 평균공급건수
FROM   TW_RGG102M_GRNTCRST_DD
GROUP BY PNSN_GV_METH_DVCD
HAVING AVG(GRNT_SPLY_CNT) >= 5000
ORDER BY 평균공급건수 DESC;"""),
        ("예제 4 — WHERE + GROUP BY + HAVING 조합",
         "20220101 이후 데이터 중, 지역코드별 공급건수 합계가 30,000건 이상인 지역.",
         """SELECT
    HS_LOC_ZONE_DVCD                AS 지역코드,
    SUM(GRNT_SPLY_CNT)              AS 총공급건수,
    ROUND(SUM(APRS_EVAL_AMT),1)     AS "총감정가(억)"
FROM   TW_RGG102M_GRNTCRST_DD
WHERE  BASIS_DY >= '20220101'
GROUP BY HS_LOC_ZONE_DVCD
HAVING SUM(GRNT_SPLY_CNT) >= 30000
ORDER BY 총공급건수 DESC;"""),
    ]
    for title, desc, sql in exs:
        with st.expander(title, expanded=True):
            st.caption(desc)
            st.code(sql, language="sql")
            show_result(conn, sql, f"grp_{title}")

    st.divider()
    practice_block(conn,
        "20210101~20250630 기간 데이터에서 기준일자·지급방식코드별로 공급건수 합계를 구하고,\n"
        "합계가 15,000건 이상인 경우만 내림차순으로 조회하세요.",
        """SELECT
    BASIS_DY               AS 기준일자,
    PNSN_GV_METH_DVCD      AS 지급방식코드,
    SUM(GRNT_SPLY_CNT)     AS 총공급건수
FROM   TW_RGG102M_GRNTCRST_DD
WHERE  BASIS_DY BETWEEN '20210101' AND '20250630'
GROUP BY BASIS_DY, PNSN_GV_METH_DVCD
HAVING SUM(GRNT_SPLY_CNT) >= 15000
ORDER BY 총공급건수 DESC;""",
        "p_group",
        hint="GROUP BY에 두 컬럼을 함께 쓰고 HAVING으로 합계를 필터하세요.")


# ══════════════════════════════════════════════════════════════
# 9. JOIN
# ══════════════════════════════════════════════════════════════
elif section == SECTIONS[9]:
    st.markdown('<div class="section-header">⑥ JOIN — 테이블 결합</div>', unsafe_allow_html=True)

    st.markdown("""
`JOIN` 은 **두 개 이상의 테이블을 공통 컬럼(키)을 기준으로 결합**해 하나의 결과로 만드는 연산입니다.

예를 들어 `TW_RGG102M_GRNTCRST_DD`에는 `HS_LOC_ZONE_DVCD`(지역코드, 숫자)만 있고 지역명은 없습니다.
지역명을 함께 보려면 `TA_COA311M_CDBSC` 테이블을 JOIN해야 합니다.
    """)
    st.markdown("""<div class="syntax-box">
SELECT  a.컬럼, b.컬럼<br>
FROM    테이블A  AS a<br>
[JOIN종류]  테이블B  AS b  ON  a.공통컬럼 = b.공통컬럼;<br><br>
⚠️ ON 조건을 빠뜨리면 카테시안 곱(모든 행의 조합)이 발생합니다!
</div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("## JOIN 종류별 동작 원리")
    tab_inner, tab_left, tab_right, tab_full = st.tabs(
        ["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL OUTER JOIN"])

    with tab_inner:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("#### 개념")
            st.markdown("두 테이블에서 **ON 조건이 일치하는 행만** 반환합니다.")
            st.code("""
  TW_RGG102M     TA_COA311M_CDBSC
  ┌───────────┐   ┌────────────┐
  │ CD_ID='11'│──▶│ CD_ID='11' │ ✅ 포함
  │ CD_ID='41'│──▶│ CD_ID='41' │ ✅ 포함
  │ CD_ID='99'│ ✗ │ (없음)     │ ❌ 제외
  └───────────┘   └────────────┘
            """, language="text")
        with col2:
            st.markdown("#### 예제")
            sql = """SELECT
    A.GRNT_NO             AS 보증번호,
    A.BASIS_DY            AS 기준일자,
    C.CD_NM               AS 지역명,
    A.PNSN_GV_METH_DVCD   AS 지급방식코드,
    A.GRNT_SPLY_CNT       AS 공급건수
FROM TW_RGG102M_GRNTCRST_DD A
INNER JOIN TA_COA311M_CDBSC C
    ON A.HS_LOC_ZONE_DVCD = C.CD_ID
   AND C.CD_GRP_ID = 'COA0083'
ORDER BY A.BASIS_DY, C.CD_NM;"""
            st.code(sql, language="sql")
            show_result(conn, sql, "join_inner")

    with tab_left:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("#### 개념")
            st.markdown("**왼쪽 테이블 전체** + 오른쪽에서 매칭되는 행. 오른쪽에 없으면 NULL.")
            st.code("""
  TA_COA311M (왼쪽)  TW_RGG102M (오른쪽)
  ┌──────────┐       ┌─────────────┐
  │ CD_ID=11 │ ────▶ │ 데이터 있음 │ ✅
  │ CD_ID=99 │ ────▶ │ 데이터 없음 │ ✅(NULL)
  └──────────┘       └─────────────┘
            """, language="text")
        with col2:
            st.markdown("#### 예제 — 보증 없는 지역도 포함")
            sql = """SELECT
    C.CD_NM              AS 지역명,
    C.ZONE_TYPE          AS 권역,
    A.BASIS_DY           AS 기준일자,
    A.GRNT_SPLY_CNT      AS 공급건수
FROM TA_COA311M_CDBSC C
LEFT JOIN TW_RGG102M_GRNTCRST_DD A
    ON C.CD_ID = A.HS_LOC_ZONE_DVCD
ORDER BY C.CD_NM, A.BASIS_DY;"""
            st.code(sql, language="sql")
            show_result(conn, sql, "join_left")

    with tab_right:
        st.markdown("#### 개념")
        st.markdown("**오른쪽 테이블 전체** + 왼쪽에서 매칭되는 행. SQLite는 RIGHT JOIN을 지원하지 않아 LEFT JOIN으로 대체합니다.")
        st.code("""-- RIGHT JOIN (SQLite 미지원 → 테이블 순서를 바꿔 LEFT JOIN으로 대체)
SELECT C.CD_NM, A.GRNT_NO, A.GRNT_SPLY_CNT
FROM TA_COA311M_CDBSC C
LEFT JOIN TW_RGG102M_GRNTCRST_DD A
    ON C.CD_ID = A.HS_LOC_ZONE_DVCD;""", language="sql")

    with tab_full:
        st.markdown("#### 개념")
        st.markdown("**양쪽 테이블 전체**를 포함합니다. SQLite는 UNION으로 구현합니다.")
        st.code("""-- FULL OUTER JOIN (SQLite 미지원 → UNION으로 구현)
SELECT C.CD_NM, A.GRNT_NO, A.GRNT_SPLY_CNT
FROM TA_COA311M_CDBSC C
LEFT JOIN TW_RGG102M_GRNTCRST_DD A ON C.CD_ID = A.HS_LOC_ZONE_DVCD

UNION

SELECT C.CD_NM, A.GRNT_NO, A.GRNT_SPLY_CNT
FROM TW_RGG102M_GRNTCRST_DD A
LEFT JOIN TA_COA311M_CDBSC C ON C.CD_ID = A.HS_LOC_ZONE_DVCD;""", language="sql")

    st.divider()
    st.markdown("## 3개 테이블 JOIN — 실무 쿼리 패턴")
    sql_3tbl = """-- 보증현황 + 보증금액 + 지역명 동시 조회 (실무 쿼리 패턴)
SELECT
    C.CD_NM                AS 지역명,
    A.BASIS_DY             AS 기준일자,
    A.GRNT_NO              AS 보증번호,
    A.PNSN_GV_METH_DVCD    AS 지급방식코드,
    A.GRNT_SPLY_CNT        AS 공급건수,
    B.GRNT_AMT             AS "보증금액(억)",
    A.APRS_EVAL_AMT        AS "감정가(억)"
FROM TW_RGG102M_GRNTCRST_DD A
JOIN TW_RGG101M_GRNTREQCNSL_DD B
    ON A.GRNT_NO = B.GRNT_NO
    AND A.BASIS_DY = B.BASIS_DY
JOIN TA_COA311M_CDBSC C
    ON A.HS_LOC_ZONE_DVCD = C.CD_ID
    AND C.CD_GRP_ID = 'COA0083'
WHERE A.BASIS_DY BETWEEN '20200101' AND '20250630'
ORDER BY A.BASIS_DY, C.CD_NM;"""
    with st.expander("예제 — 3개 테이블 JOIN (실무 패턴)", expanded=True):
        st.code(sql_3tbl, language="sql")
        show_result(conn, sql_3tbl, "join_3tbl")

    st.divider()
    practice_block(conn,
        "TA_COA311M_CDBSC와 TW_RGG102M_GRNTCRST_DD를 JOIN하여 '수도권' 지역의\n"
        "20220101~20250630 전세(PNSN_GV_METH_DVCD='07') 보증을\n"
        "지역명·기준일자·보증번호·공급건수로 조회하고 공급건수 내림차순으로 정렬하세요.",
        """SELECT
    C.CD_NM              AS 지역명,
    A.BASIS_DY           AS 기준일자,
    A.GRNT_NO            AS 보증번호,
    A.GRNT_SPLY_CNT      AS 공급건수
FROM TW_RGG102M_GRNTCRST_DD A
JOIN TA_COA311M_CDBSC C
    ON A.HS_LOC_ZONE_DVCD = C.CD_ID
    AND C.CD_GRP_ID = 'COA0083'
WHERE  C.ZONE_TYPE = '수도권'
  AND  A.BASIS_DY BETWEEN '20220101' AND '20250630'
  AND  A.PNSN_GV_METH_DVCD = '07'
ORDER BY A.GRNT_SPLY_CNT DESC;""",
        "p_join",
        hint="JOIN 후 WHERE에서 ZONE_TYPE, BASIS_DY BETWEEN, PNSN_GV_METH_DVCD 세 조건을 AND로 연결하세요.")


# ══════════════════════════════════════════════════════════════
# 10. CASE WHEN & COALESCE 
# ══════════════════════════════════════════════════════════════
elif section == SECTIONS[10]:
    st.markdown('<div class="section-header">⑦ CASE WHEN & COALESCE — 조건부 처리</div>', unsafe_allow_html=True)

    st.markdown("""
데이터를 가공하거나 NULL을 처리할 때 가장 많이 쓰이는 두 가지 함수입니다.
실무 쿼리에서 `PNSN_GV_METH_DVCD`(코드) → 한글명 변환, 시세 우선순위 처리 등에 빠짐없이 등장합니다.
    """)

    tab_case, tab_coalesce = st.tabs(["CASE WHEN — 조건 분기", "COALESCE — NULL 대체"])

    with tab_case:
        st.markdown("## CASE WHEN")
        st.markdown("""
`CASE WHEN`은 SQL의 **if-else 문**입니다. 조건에 따라 다른 값을 반환합니다.
SELECT, WHERE, ORDER BY, GROUP BY 어디서든 사용 가능합니다.
        """)
        st.markdown("""<div class="syntax-box">
-- 단순 CASE (값 비교)<br>
CASE 컬럼<br>
&nbsp;&nbsp;WHEN 값1 THEN 결과1<br>
&nbsp;&nbsp;WHEN 값2 THEN 결과2<br>
&nbsp;&nbsp;ELSE 기본값<br>
END<br><br>
-- 검색 CASE (조건식)<br>
CASE<br>
&nbsp;&nbsp;WHEN 조건1 THEN 결과1<br>
&nbsp;&nbsp;WHEN 조건2 THEN 결과2<br>
&nbsp;&nbsp;ELSE 기본값<br>
END
</div>""", unsafe_allow_html=True)

        st.markdown("""<div class="tip-box">💡 <b>실무 활용 포인트</b><br>
• 코드값 → 한글명 변환: <code>CASE PNSN_GV_METH_DVCD WHEN '07' THEN '전세' WHEN '08' THEN '구입' END</code><br>
• 시세 출처 구분: <code>CASE WHEN KAB_SISE_RSCH_DY &lt;&gt; '0' THEN '부동산원인터넷시세' ELSE '국민은행인터넷시세' END</code><br>
• 조건부 집계: <code>SUM(CASE WHEN ZONE_TYPE = '수도권' THEN GRNT_SPLY_CNT ELSE 0 END)</code>
</div>""", unsafe_allow_html=True)

        st.divider()
        exs_case = [
            ("예제 1 — 지급방식코드 → 한글명 변환",
             "PNSN_GV_METH_DVCD 코드를 읽기 쉬운 한글명으로 변환합니다. 보고서 작성 시 필수 패턴입니다.",
             """SELECT
    GRNT_NO          AS 보증번호,
    BASIS_DY         AS 기준일자,
    PNSN_GV_METH_DVCD AS 지급방식코드,
    CASE PNSN_GV_METH_DVCD
        WHEN '07' THEN '전세'
        WHEN '08' THEN '구입'
        WHEN '09' THEN '중도금'
        ELSE '기타'
    END              AS 지급방식명,
    GRNT_SPLY_CNT    AS 공급건수
FROM TW_RGG102M_GRNTCRST_DD
LIMIT 10;"""),
            ("예제 2 — 시세 출처 구분 (실무 쿼리 패턴)",
             "KAB_SISE_RSCH_DY가 '0'이 아니면 부동산원, '0'이면 국민은행 시세입니다. 실무 쿼리에서 그대로 사용됩니다.",
             """SELECT
    GRNT_NO,
    BASIS_YM,
    CASE
        WHEN KAB_SISE_RSCH_DY <> '0' THEN '부동산원인터넷시세'
        ELSE '국민은행인터넷시세'
    END AS 시세평가,
    KAB_TRD_AVG_PRC AS KB거래평균가격,
    KB_TRD_AVG_PRC  AS KB시세평균가격
FROM TB_RGR011M_HSPRC;"""),
            ("예제 3 — 공급건수 규모 구분",
             "공급건수 크기에 따라 대형/중형/소형으로 구분합니다.",
             """SELECT
    GRNT_NO,
    GRNT_SPLY_CNT AS 공급건수,
    CASE
        WHEN GRNT_SPLY_CNT >= 20000 THEN '대형'
        WHEN GRNT_SPLY_CNT >= 10000 THEN '중형'
        ELSE '소형'
    END AS 규모구분
FROM TW_RGG102M_GRNTCRST_DD
ORDER BY GRNT_SPLY_CNT DESC;"""),
            ("예제 4 — 조건부 집계 (수도권 vs 지방 피벗)",
             "JOIN 후 CASE WHEN으로 수도권/지방 공급건수를 열로 분리합니다. 실무 피벗 리포트 패턴입니다.",
             """SELECT
    A.BASIS_DY AS 기준일자,
    SUM(CASE WHEN C.ZONE_TYPE = '수도권' THEN A.GRNT_SPLY_CNT ELSE 0 END) AS 수도권공급건수,
    SUM(CASE WHEN C.ZONE_TYPE = '지방'   THEN A.GRNT_SPLY_CNT ELSE 0 END) AS 지방공급건수,
    SUM(A.GRNT_SPLY_CNT)                                                   AS 전국공급건수
FROM TW_RGG102M_GRNTCRST_DD A
JOIN TA_COA311M_CDBSC C
    ON A.HS_LOC_ZONE_DVCD = C.CD_ID
    AND C.CD_GRP_ID = 'COA0083'
GROUP BY A.BASIS_DY
ORDER BY A.BASIS_DY;"""),
        ]
        for title, desc, sql in exs_case:
            with st.expander(title, expanded=True):
                st.caption(desc)
                st.code(sql, language="sql")
                show_result(conn, sql, f"cw_{title}")

        st.divider()
        practice_block(conn,
            "TW_RGG102M_GRNTCRST_DD 에서 기준일자별로\n"
            "지급방식코드 '07'(전세) 공급건수 합계와 '08'(구입) 공급건수 합계를 열로 나란히 조회하세요.\n"
            "(CASE WHEN + SUM 조건부 집계 패턴 활용)",
            """SELECT
    BASIS_DY AS 기준일자,
    SUM(CASE WHEN PNSN_GV_METH_DVCD = '07' THEN GRNT_SPLY_CNT ELSE 0 END) AS 전세공급건수,
    SUM(CASE WHEN PNSN_GV_METH_DVCD = '08' THEN GRNT_SPLY_CNT ELSE 0 END) AS 구입공급건수,
    SUM(GRNT_SPLY_CNT)                                                       AS 전체공급건수
FROM TW_RGG102M_GRNTCRST_DD
GROUP BY BASIS_DY
ORDER BY BASIS_DY;""",
            "p_casewhen",
            hint="SUM(CASE WHEN 조건 THEN 값 ELSE 0 END) 패턴으로 조건부 합계를 구하세요.")

    with tab_coalesce:
        st.markdown("## COALESCE")
        st.markdown("""
`COALESCE(값1, 값2, 값3, ...)` 는 **왼쪽부터 순서대로 확인해 첫 번째 NULL이 아닌 값을 반환**합니다.
NULL이 있는 컬럼을 집계하거나 기본값을 설정할 때 필수적으로 사용합니다.
        """)
        st.markdown("""<div class="syntax-box">
COALESCE(컬럼1, 컬럼2, ..., 기본값)<br><br>
-- 동작 원리:<br>
-- 컬럼1이 NULL이 아니면 → 컬럼1 반환<br>
-- 컬럼1이 NULL이고 컬럼2가 NULL이 아니면 → 컬럼2 반환<br>
-- 모두 NULL이면 → 기본값 반환
</div>""", unsafe_allow_html=True)

        st.markdown("""<div class="tip-box">💡 <b>실무 활용 포인트</b><br>
• NULL 대신 0 처리: <code>COALESCE(MM_PYAT_AMT, 0)</code><br>
• 시세 우선순위: <code>COALESCE(KAB_TRD_AVG_PRC, KB_TRD_AVG_PRC, 0) * 10000</code><br>
&nbsp;&nbsp;→ KB거래가 있으면 KB거래, 없으면 KB시세, 둘 다 없으면 0으로 처리 후 만원 단위로 환산<br>
• 텍스트 NULL 대체: <code>COALESCE(LAST_CNCL_DY, '미해지')</code>
</div>""", unsafe_allow_html=True)

        st.divider()
        exs_coal = [
            ("예제 1 — NULL을 0으로 대체 (월지급금)",
             "MM_PYAT_AMT가 NULL인 경우 0으로 처리합니다. NULL이 있으면 SUM/AVG 계산에서 해당 행이 제외되므로 주의하세요.",
             """SELECT
    GRNT_NO                           AS 보증번호,
    MM_PYAT_AMT                       AS "원래월지급금(만원)",
    COALESCE(MM_PYAT_AMT, 0)          AS "NULL→0처리(만원)"
FROM TB_RGE303M_GRNTRVEWAMT
ORDER BY GRNT_NO;"""),
            ("예제 2 — 시세 우선순위 처리 (실무 쿼리 패턴)",
             "KB거래평균가격 → KB시세평균가격 순으로 우선순위를 두고, 억원을 만원으로 환산합니다.",
             """SELECT
    GRNT_NO,
    BASIS_YM,
    KAB_TRD_AVG_PRC                           AS KB거래평균가격,
    KB_TRD_AVG_PRC                            AS KB시세평균가격,
    COALESCE(KAB_TRD_AVG_PRC,
             KB_TRD_AVG_PRC, 0) * 10000      AS "HSPRC(만원)"
FROM TB_RGR011M_HSPRC;"""),
            ("예제 3 — NULL을 텍스트로 대체",
             "LAST_CNCL_DY가 NULL이면 '미해지'로 표시합니다. 보고서 출력 시 NULL이 빈 칸으로 보이는 것을 방지합니다.",
             """SELECT
    GRNT_NO                               AS 보증번호,
    GRNT_AMT                              AS "보증금액(억)",
    LAST_CNCL_DY                          AS 최종해지일자_원본,
    COALESCE(LAST_CNCL_DY, '미해지')      AS 최종해지일자
FROM TW_RGG101M_GRNTREQCNSL_DD
ORDER BY GRNT_NO;"""),
            ("예제 4 — COALESCE + CASE WHEN 조합 (실무 쿼리 패턴)",
             "시세 처리 후 시세 출처도 함께 표시합니다. 실제 사용하는 복합 패턴입니다.",
             """SELECT
    GRNT_NO,
    BASIS_YM,
    COALESCE(KAB_TRD_AVG_PRC, KB_TRD_AVG_PRC, 0) * 10000 AS "HSPRC(만원)",
    CASE
        WHEN KAB_SISE_RSCH_DY <> '0' THEN '부동산원인터넷시세'
        ELSE '국민은행인터넷시세'
    END AS 시세평가
FROM TB_RGR011M_HSPRC;"""),
        ]
        for title, desc, sql in exs_coal:
            with st.expander(title, expanded=True):
                st.caption(desc)
                st.code(sql, language="sql")
                show_result(conn, sql, f"coal_{title}")

        st.divider()
        practice_block(conn,
            "TB_RGE303M_GRNTRVEWAMT와 TW_RGG102M_GRNTCRST_DD를 GRNT_NO로 JOIN하여\n"
            "보증번호·지급방식명(CASE WHEN으로 코드→한글 변환)·월지급금(NULL이면 0)을 조회하세요.",
            """SELECT
    A.GRNT_NO                         AS 보증번호,
    CASE A.PNSN_GV_METH_DVCD
        WHEN '07' THEN '전세'
        WHEN '08' THEN '구입'
        WHEN '09' THEN '중도금'
        ELSE '기타'
    END                               AS 지급방식명,
    COALESCE(B.MM_PYAT_AMT, 0)        AS "월지급금(만원)"
FROM TW_RGG102M_GRNTCRST_DD A
LEFT JOIN TB_RGE303M_GRNTRVEWAMT B
    ON A.GRNT_NO = B.GRNT_NO
ORDER BY A.GRNT_NO;""",
            "p_coalesce",
            hint="LEFT JOIN 후 CASE WHEN으로 코드 변환, COALESCE로 NULL→0 처리하세요.")


# ══════════════════════════════════════════════════════════════
# 11. 복합 쿼리 실전
# ══════════════════════════════════════════════════════════════
elif section == SECTIONS[11]:
    st.markdown('<div class="section-header">🚀 복합 쿼리 실전</div>', unsafe_allow_html=True)
    st.markdown("""
지금까지 배운 모든 키워드를 조합하는 실전 문제입니다.
실무 쿼리 사진 속 패턴과 동일한 구조로 구성했습니다.
**먼저 직접 SQL을 작성해 실행해보고**, 📋 정답 보기로 비교해보세요.
    """)
    st.markdown("""<div class="tip-box">💡 <b>풀이 순서 추천</b><br>
① 어떤 테이블이 필요한지 파악 → ② JOIN 구조 결정 → ③ WHERE 조건 작성
→ ④ GROUP BY / HAVING → ⑤ CASE WHEN / COALESCE 가공 → ⑥ SELECT 컬럼 & 별칭 정리 → ⑦ ORDER BY</div>""",
    unsafe_allow_html=True)
    st.divider()

    practice_block(conn,
        "📌 실전 1 — 기준일자·지역별 보증 현황 리포트\n\n"
        "기준일자·지역명·권역·지급방식명(CASE WHEN 코드→한글)별로\n"
        "공급건수 합계와 감정가 합계(소수점 1자리)를 구하고,\n"
        "기준일자 내림차순 → 공급건수 합계 내림차순으로 정렬하세요.",
        """SELECT
    A.BASIS_DY                        AS 기준일자,
    C.CD_NM                           AS 지역명,
    C.ZONE_TYPE                       AS 권역,
    CASE A.PNSN_GV_METH_DVCD
        WHEN '07' THEN '전세'
        WHEN '08' THEN '구입'
        WHEN '09' THEN '중도금'
        ELSE '기타'
    END                               AS 지급방식명,
    SUM(A.GRNT_SPLY_CNT)              AS 총공급건수,
    ROUND(SUM(A.APRS_EVAL_AMT), 1)   AS "총감정가(억)"
FROM TW_RGG102M_GRNTCRST_DD A
JOIN TA_COA311M_CDBSC C
    ON A.HS_LOC_ZONE_DVCD = C.CD_ID
    AND C.CD_GRP_ID = 'COA0083'
GROUP BY A.BASIS_DY, C.CD_NM, C.ZONE_TYPE, A.PNSN_GV_METH_DVCD
ORDER BY A.BASIS_DY DESC, 총공급건수 DESC;""",
        "adv1",
        hint="JOIN 후 CASE WHEN으로 지급방식명 변환, 4개 컬럼으로 GROUP BY, SUM·ROUND로 집계하세요.")

    st.divider()
    practice_block(conn,
        "📌 실전 2 — 보증·연금 통합 조회 (COALESCE + JOIN)\n\n"
        "TW_RGG102M_GRNTCRST_DD, TW_RGG101M_GRNTREQCNSL_DD, TB_RGE303M_GRNTRVEWAMT를 GRNT_NO로 JOIN하여\n"
        "20230101 이후 데이터의 보증번호·지역명·보증금액·월지급금(NULL이면 0)·감정가를 조회하세요.",
        """SELECT
    A.GRNT_NO                              AS 보증번호,
    C.CD_NM                                AS 지역명,
    B.GRNT_AMT                             AS "보증금액(억)",
    COALESCE(E.MM_PYAT_AMT, 0)             AS "월지급금(만원,NULL→0)",
    A.APRS_EVAL_AMT                        AS "감정가(억)"
FROM TW_RGG102M_GRNTCRST_DD A
JOIN TW_RGG101M_GRNTREQCNSL_DD B
    ON A.GRNT_NO = B.GRNT_NO AND A.BASIS_DY = B.BASIS_DY
JOIN TA_COA311M_CDBSC C
    ON A.HS_LOC_ZONE_DVCD = C.CD_ID AND C.CD_GRP_ID = 'COA0083'
LEFT JOIN TB_RGE303M_GRNTRVEWAMT E
    ON A.GRNT_NO = E.GRNT_NO
WHERE A.BASIS_DY >= '20230101'
ORDER BY A.GRNT_NO;""",
        "adv2",
        hint="월지급금 테이블은 LEFT JOIN(없는 행도 포함)하고 COALESCE로 NULL→0 처리하세요.")

    st.divider()
    practice_block(conn,
        "📌 실전 3 — 수도권 vs 지방 연도별 보증 비교 (CASE WHEN 피벗)\n\n"
        "기준일자별로 수도권 공급건수 합계, 지방 공급건수 합계, 전국 합계를 나란히 조회하세요.",
        """SELECT
    A.BASIS_DY AS 기준일자,
    SUM(CASE WHEN C.ZONE_TYPE = '수도권' THEN A.GRNT_SPLY_CNT ELSE 0 END) AS 수도권공급건수,
    SUM(CASE WHEN C.ZONE_TYPE = '지방'   THEN A.GRNT_SPLY_CNT ELSE 0 END) AS 지방공급건수,
    SUM(A.GRNT_SPLY_CNT)                                                   AS 전국공급건수
FROM TW_RGG102M_GRNTCRST_DD A
JOIN TA_COA311M_CDBSC C
    ON A.HS_LOC_ZONE_DVCD = C.CD_ID AND C.CD_GRP_ID = 'COA0083'
GROUP BY A.BASIS_DY
ORDER BY A.BASIS_DY;""",
        "adv3",
        hint="SUM(CASE WHEN 조건 THEN 값 ELSE 0 END) 패턴으로 조건부 합계를 구하세요.")

    st.divider()
    practice_block(conn,
        "📌 실전 4 — 시세 + 가입자 연령 통합 조회\n\n"
        "TB_RGR011M_HSPRC와 TB_RGE301M_GRNTRVEHUMNMAT를 GRNT_NO로 JOIN하여\n"
        "시세(COALESCE로 우선순위 처리, 만원 단위), 시세평가(CASE WHEN), 가입자 연령을 조회하세요.",
        """SELECT
    H.GRNT_NO,
    H.BASIS_YM                                       AS 기준연월,
    COALESCE(H.KAB_TRD_AVG_PRC,
             H.KB_TRD_AVG_PRC, 0) * 10000           AS "HSPRC(만원)",
    CASE
        WHEN H.KAB_SISE_RSCH_DY <> '0' THEN '부동산원인터넷시세'
        ELSE '국민은행인터넷시세'
    END                                              AS 시세평가,
    P.AGE_YRCT                                       AS 가입자연령
FROM TB_RGR011M_HSPRC H
LEFT JOIN TB_RGE301M_GRNTRVEHUMNMAT P
    ON H.GRNT_NO = P.GRNT_NO
ORDER BY H.GRNT_NO;""",
        "adv4",
        hint="COALESCE로 시세 우선순위 처리 후 *10000, CASE WHEN으로 시세 출처 구분하세요.")


# ══════════════════════════════════════════════════════════════
# 12. 자유 실습 & 연습문제
# ══════════════════════════════════════════════════════════════
elif section == SECTIONS[12]:
    st.markdown('<div class="section-header">✏️ 자유 실습 & 연습문제</div>', unsafe_allow_html=True)

    tab_free, tab_quiz = st.tabs(["🔓 자유 실습", "📝 연습문제 (정답 포함)"])

    with tab_free:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📋 테이블 & 주요 컬럼**")
            st.markdown("""
- `TA_COA311M_CDBSC` : CD_ID(지역코드), CD_NM(지역명), ZONE_TYPE(권역)
- `TW_RGG102M_GRNTCRST_DD` : BASIS_DY(기준일자), GRNT_NO(보증번호), HS_LOC_ZONE_DVCD(지역코드), PNSN_GV_METH_DVCD(지급방식), GRNT_SPLY_CNT(공급건수), APRS_EVAL_AMT(감정가)
- `TW_RGG101M_GRNTREQCNSL_DD` : BASIS_DY, GRNT_NO, GRNT_AMT(보증금액), LAST_CNCL_DY(해지일)
- `TB_RGE303M_GRNTRVEWAMT` : GRNT_NO, MM_PYAT_AMT(월지급금)
- `TB_RGE301M_GRNTRVEHUMNMAT` : GRNT_NO, AGE_YRCT(연령)
- `TB_RGR011M_HSPRC` : BASIS_YM(기준연월), GRNT_NO, KAB_TRD_AVG_PRC, KB_TRD_AVG_PRC, KAB_SISE_RSCH_DY
            """)
        with col2:
            st.markdown("**⚡ 빠른 참조**")
            st.code("""-- 지역명 조인
JOIN TA_COA311M_CDBSC C
  ON A.HS_LOC_ZONE_DVCD = C.CD_ID
 AND C.CD_GRP_ID = 'COA0083'

-- 지급방식 코드 변환
CASE PNSN_GV_METH_DVCD
  WHEN '07' THEN '전세'
  WHEN '08' THEN '구입'
  WHEN '09' THEN '중도금'
END

-- 시세 우선순위
COALESCE(KAB_TRD_AVG_PRC, KB_TRD_AVG_PRC, 0)*10000

-- 날짜 범위
BASIS_DY BETWEEN '20200101' AND '20250630'""", language="sql")

        presets = [
            "직접 입력",
            "SELECT * FROM TA_COA311M_CDBSC",
            "SELECT * FROM TW_RGG102M_GRNTCRST_DD LIMIT 10",
            "SELECT BASIS_DY, SUM(GRNT_SPLY_CNT) AS 총공급건수 FROM TW_RGG102M_GRNTCRST_DD GROUP BY BASIS_DY ORDER BY BASIS_DY",
            "SELECT A.GRNT_NO, C.CD_NM, A.PNSN_GV_METH_DVCD, A.GRNT_SPLY_CNT FROM TW_RGG102M_GRNTCRST_DD A JOIN TA_COA311M_CDBSC C ON A.HS_LOC_ZONE_DVCD = C.CD_ID AND C.CD_GRP_ID = 'COA0083' WHERE A.BASIS_DY = '20230630'",
            "SELECT GRNT_NO, MM_PYAT_AMT, COALESCE(MM_PYAT_AMT, 0) AS 월지급금_NULL대체 FROM TB_RGE303M_GRNTRVEWAMT",
        ]
        preset = st.selectbox("예제 불러오기", presets)
        default = "" if preset == "직접 입력" else preset
        user_sql = st.text_area("SQL 입력", value=default, height=160, placeholder="SELECT ...")
        if st.button("▶ 실행", type="primary"):
            if user_sql.strip():
                df, err = run_sql(conn, user_sql)
                if err:
                    st.error(f"오류: {err}")
                else:
                    st.success(f"✅ {len(df)}행 반환")
                    st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.warning("SQL을 입력해주세요.")

    with tab_quiz:
        st.markdown("아래 5개 문제를 직접 풀어보고 📋 정답 보기로 확인하세요.")
        st.divider()

        quizzes = [
            {
                "no": "1", "level": "🟢 기초",
                "q": "TW_RGG102M_GRNTCRST_DD 에서 20230630 기준 보증 데이터를 공급건수 내림차순으로 조회하세요.\n(보증번호·지급방식코드·공급건수·감정가 컬럼 포함)",
                "hint": "WHERE BASIS_DY = '20230630' 후 ORDER BY GRNT_SPLY_CNT DESC",
                "answer": """SELECT
    GRNT_NO              AS 보증번호,
    PNSN_GV_METH_DVCD    AS 지급방식코드,
    GRNT_SPLY_CNT        AS 공급건수,
    APRS_EVAL_AMT        AS "감정가(억)"
FROM   TW_RGG102M_GRNTCRST_DD
WHERE  BASIS_DY = '20230630'
ORDER BY GRNT_SPLY_CNT DESC;""",
            },
            {
                "no": "2", "level": "🟢 기초",
                "q": "TW_RGG101M_GRNTREQCNSL_DD 에서 LAST_CNCL_DY가 NULL이 아닌(이미 해지된) 건을 COALESCE로 해지일 NULL→'미해지' 처리하여 조회하세요.",
                "hint": "WHERE LAST_CNCL_DY IS NOT NULL 후 COALESCE(LAST_CNCL_DY, '미해지')",
                "answer": """SELECT
    GRNT_NO                                AS 보증번호,
    GRNT_AMT                               AS "보증금액(억)",
    COALESCE(LAST_CNCL_DY, '미해지')       AS 최종해지일자
FROM   TW_RGG101M_GRNTREQCNSL_DD
WHERE  LAST_CNCL_DY IS NOT NULL
ORDER BY LAST_CNCL_DY;""",
            },
            {
                "no": "3", "level": "🟡 중급",
                "q": "기준일자·지급방식코드별 공급건수 합계를 구하되, 지급방식코드를 CASE WHEN으로 한글명(07→전세, 08→구입, 09→중도금)으로 변환하여 조회하세요.",
                "hint": "GROUP BY BASIS_DY, PNSN_GV_METH_DVCD 후 CASE WHEN으로 한글 변환",
                "answer": """SELECT
    BASIS_DY              AS 기준일자,
    CASE PNSN_GV_METH_DVCD
        WHEN '07' THEN '전세'
        WHEN '08' THEN '구입'
        WHEN '09' THEN '중도금'
        ELSE '기타'
    END                   AS 지급방식명,
    SUM(GRNT_SPLY_CNT)    AS 총공급건수
FROM   TW_RGG102M_GRNTCRST_DD
GROUP BY BASIS_DY, PNSN_GV_METH_DVCD
ORDER BY BASIS_DY, 총공급건수 DESC;""",
            },
            {
                "no": "4", "level": "🟡 중급",
                "q": "TW_RGG102M_GRNTCRST_DD와 TA_COA311M_CDBSC를 JOIN하여 '수도권' 지역의 20230630 기준 보증 현황을 지역명·지급방식코드·공급건수로 조회하고, 공급건수 내림차순으로 정렬하세요.",
                "hint": "INNER JOIN 후 WHERE ZONE_TYPE = '수도권' AND BASIS_DY = '20230630'",
                "answer": """SELECT
    C.CD_NM               AS 지역명,
    A.PNSN_GV_METH_DVCD   AS 지급방식코드,
    A.GRNT_SPLY_CNT        AS 공급건수
FROM TW_RGG102M_GRNTCRST_DD A
JOIN TA_COA311M_CDBSC C
    ON A.HS_LOC_ZONE_DVCD = C.CD_ID
    AND C.CD_GRP_ID = 'COA0083'
WHERE  C.ZONE_TYPE = '수도권'
  AND  A.BASIS_DY = '20230630'
ORDER BY A.GRNT_SPLY_CNT DESC;""",
            },
            {
                "no": "5", "level": "🔴 심화",
                "q": "기준일자별로 수도권 공급건수 합계, 지방 공급건수 합계, 전체 합계를 구하고\n전체 합계가 전체 데이터 평균 이상인 기준일자만 전체 합계 내림차순으로 조회하세요.",
                "hint": "CASE WHEN 피벗 + HAVING SUM(...) > (SELECT AVG(...) 서브쿼리)",
                "answer": """SELECT
    A.BASIS_DY AS 기준일자,
    SUM(CASE WHEN C.ZONE_TYPE = '수도권' THEN A.GRNT_SPLY_CNT ELSE 0 END) AS 수도권공급건수,
    SUM(CASE WHEN C.ZONE_TYPE = '지방'   THEN A.GRNT_SPLY_CNT ELSE 0 END) AS 지방공급건수,
    SUM(A.GRNT_SPLY_CNT)                                                   AS 전국공급건수
FROM TW_RGG102M_GRNTCRST_DD A
JOIN TA_COA311M_CDBSC C
    ON A.HS_LOC_ZONE_DVCD = C.CD_ID AND C.CD_GRP_ID = 'COA0083'
GROUP BY A.BASIS_DY
HAVING SUM(A.GRNT_SPLY_CNT) >= (
    SELECT AVG(sub.total) FROM (
        SELECT SUM(GRNT_SPLY_CNT) AS total
        FROM TW_RGG102M_GRNTCRST_DD
        GROUP BY BASIS_DY
    ) sub
)
ORDER BY 전국공급건수 DESC;""",
            },
        ]

        for q in quizzes:
            st.markdown(f"### 문제 {q['no']} &nbsp; {q['level']}")
            practice_block(conn, q["q"], q["answer"],
                           f"quiz_{q['no']}", hint=q["hint"])
            st.divider()

        st.markdown("""<div class="tip-box">
✅ <b>실수 방지 최종 체크리스트</b><br>
• NULL 비교 → <code>IS NULL</code> 사용 (<code>= NULL</code>은 항상 FALSE)<br>
• NULL이 있는 컬럼 집계 → <code>COALESCE(컬럼, 0)</code>으로 대체<br>
• 집계함수 조건 → <code>WHERE</code> 아닌 <code>HAVING</code>에 작성<br>
• GROUP BY → SELECT의 비집계 컬럼 모두 포함<br>
• CASE WHEN → 반드시 <code>END</code>로 닫기, ELSE 생략 시 NULL 반환<br>
• JOIN → <code>ON</code> 조건 누락 시 카테시안 곱 발생<br>
• TA_COA311M_CDBSC JOIN 시 → <code>AND CD_GRP_ID = 'COA0083'</code> 조건 필수<br>
• <code>LIKE '%값%'</code> → 대용량에서 Full Scan 발생 주의
</div>""", unsafe_allow_html=True)
