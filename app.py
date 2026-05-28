import streamlit as st
import requests
from dotenv import load_dotenv
import os

load_dotenv("/Users/inishiesaburou/Desktop/claudefolder/.env")

def get_secret(key, default=""):
    try:
        return st.secrets[key]
    except:
        return os.getenv(key, default)

API_KEY         = get_secret("NOTION_API_KEY")
CLIENT_DB_ID    = get_secret("NOTION_CLIENT_DB_ID")
PROJECT_DB_ID   = get_secret("NOTION_PROJECT_DB_ID")
TASK_DB_ID      = get_secret("NOTION_TASK_DB_ID")
INVOICE_DB_ID   = get_secret("NOTION_INVOICE_DB_ID")
EMPLOYEE_DB_ID  = get_secret("NOTION_EMPLOYEE_DB_ID")
ATTENDANCE_DB_ID = get_secret("NOTION_ATTENDANCE_DB_ID")
PAYROLL_DB_ID   = get_secret("NOTION_PAYROLL_DB_ID")
HR_PASSWORD     = get_secret("HR_PASSWORD", "initie2026")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

STATUS_COLORS = {
    "商談中": "🔵", "受注": "🟣", "進行中": "🟡", "完了": "🟢", "失注": "🔴",
    "未着手": "⚪", "未請求": "⚪", "請求済": "🟡", "入金済": "🟢"
}

st.set_page_config(page_title="イニシエ 管理システム", page_icon="🎬", layout="wide")

# ---- ヘルパー ----
def get_text(prop, key):
    try:
        items = prop.get(key, {})
        t = items.get("type")
        if t == "title":   return items["title"][0]["text"]["content"] if items["title"] else ""
        if t == "rich_text": return items["rich_text"][0]["text"]["content"] if items["rich_text"] else ""
        if t == "email":   return items.get("email") or ""
        if t == "phone_number": return items.get("phone_number") or ""
        if t == "number":  return items.get("number")
        if t == "url":     return items.get("url") or ""
        if t == "date":    return items["date"]["start"] if items.get("date") else ""
        if t == "select":  return items["select"]["name"] if items.get("select") else ""
    except:
        return ""
    return ""

def query_db(db_id, filters=None, sorts=None):
    body = {}
    if filters: body["filter"] = filters
    if sorts:   body["sorts"] = sorts
    res = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query", headers=HEADERS, json=body)
    return res.json().get("results", [])

def create_page(db_id, props):
    requests.post("https://api.notion.com/v1/pages", headers=HEADERS,
        json={"parent": {"database_id": db_id}, "properties": props})

def update_page(page_id, props):
    requests.patch(f"https://api.notion.com/v1/pages/{page_id}", headers=HEADERS, json={"properties": props})

# ---- データ取得 ----
def get_clients():
    return query_db(CLIENT_DB_ID, sorts=[{"property": "会社名", "direction": "ascending"}])

def get_projects(status_filter=None):
    f = {"property": "ステータス", "select": {"equals": status_filter}} if status_filter else None
    return query_db(PROJECT_DB_ID, filters=f, sorts=[{"property": "納期", "direction": "ascending"}])

def get_tasks_by_project(project_id):
    return query_db(TASK_DB_ID, filters={"property": "案件", "relation": {"contains": project_id}})

def get_projects_by_client(client_id):
    return query_db(PROJECT_DB_ID, filters={"property": "クライアント", "relation": {"contains": client_id}})

# ---- ナビゲーション ----
st.title("🎬 イニシエ 管理システム")
page = st.sidebar.radio("メニュー", ["👥 クライアント管理", "📁 案件管理", "🔒 人事管理", "👤 給与明細"])
st.sidebar.markdown("---")
st.sidebar.caption("イニシエ株式会社")

# ========== クライアント管理 ==========
if page == "👥 クライアント管理":
    st.subheader("👥 クライアント管理")
    tab1, tab2 = st.tabs(["📋 一覧", "➕ 新規登録"])

    with tab1:
        search = st.text_input("🔍 会社名で検索", placeholder="例：株式会社〇〇")
        clients = get_clients()
        if search:
            clients = [c for c in clients if search in get_text(c["properties"], "会社名")]
        st.write(f"**{len(clients)} 件**")

        for client in clients:
            p = client["properties"]
            name    = get_text(p, "会社名")
            contact = get_text(p, "担当者名")
            email   = get_text(p, "メール")
            phone   = get_text(p, "電話番号")
            address = get_text(p, "住所")
            notes   = get_text(p, "備考")

            with st.expander(f"🏢 {name}"):
                col1, col2 = st.columns(2)
                with col1:
                    new_name    = st.text_input("会社名",   value=name,    key=f"n_{client['id']}")
                    new_contact = st.text_input("担当者名", value=contact, key=f"c_{client['id']}")
                    new_email   = st.text_input("メール",   value=email,   key=f"e_{client['id']}")
                with col2:
                    new_phone   = st.text_input("電話番号", value=phone,   key=f"p_{client['id']}")
                    new_address = st.text_input("住所",     value=address, key=f"a_{client['id']}")
                    new_notes   = st.text_input("備考",     value=notes,   key=f"no_{client['id']}")

                if st.button("💾 保存", key=f"s_{client['id']}"):
                    update_page(client["id"], {
                        "会社名":   {"title": [{"text": {"content": new_name}}]},
                        "担当者名": {"rich_text": [{"text": {"content": new_contact}}]},
                        "メール":   {"email": new_email or None},
                        "電話番号": {"phone_number": new_phone or None},
                        "住所":     {"rich_text": [{"text": {"content": new_address}}]},
                        "備考":     {"rich_text": [{"text": {"content": new_notes}}]},
                    })
                    st.success("保存しました")
                    st.rerun()

                projects = get_projects_by_client(client["id"])
                if projects:
                    st.markdown("**関連案件**")
                    for pj in projects:
                        pj_name = get_text(pj["properties"], "案件名")
                        status  = get_text(pj["properties"], "ステータス")
                        icon    = STATUS_COLORS.get(status, "⚪")
                        st.write(f"　{icon} {pj_name}　`{status}`")

    with tab2:
        st.markdown("### 新規クライアント登録")
        col1, col2 = st.columns(2)
        with col1:
            n_name    = st.text_input("会社名 *")
            n_contact = st.text_input("担当者名")
            n_email   = st.text_input("メール")
        with col2:
            n_phone   = st.text_input("電話番号")
            n_address = st.text_input("住所")
            n_notes   = st.text_input("備考")

        if st.button("➕ 登録する", type="primary"):
            if not n_name:
                st.error("会社名は必須です")
            else:
                props = {"会社名": {"title": [{"text": {"content": n_name}}]}}
                if n_contact: props["担当者名"] = {"rich_text": [{"text": {"content": n_contact}}]}
                if n_email:   props["メール"] = {"email": n_email}
                if n_phone:   props["電話番号"] = {"phone_number": n_phone}
                if n_address: props["住所"] = {"rich_text": [{"text": {"content": n_address}}]}
                if n_notes:   props["備考"] = {"rich_text": [{"text": {"content": n_notes}}]}
                create_page(CLIENT_DB_ID, props)
                st.success(f"「{n_name}」を登録しました")
                st.rerun()

# ========== 案件管理 ==========
elif page == "📁 案件管理":
    st.subheader("📁 案件管理")
    tab1, tab2 = st.tabs(["📋 一覧", "➕ 新規登録"])

    with tab1:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            search = st.text_input("🔍 案件名で検索")
        with col_f2:
            status_filter = st.selectbox("ステータスで絞り込み",
                ["すべて", "商談中", "受注", "進行中", "完了", "失注"])

        projects = get_projects(None if status_filter == "すべて" else status_filter)
        if search:
            projects = [p for p in projects if search in get_text(p["properties"], "案件名")]

        # サマリー
        status_counts = {}
        for pj in get_projects():
            s = get_text(pj["properties"], "ステータス")
            status_counts[s] = status_counts.get(s, 0) + 1

        cols = st.columns(5)
        for i, (label, key) in enumerate([("商談中","商談中"),("受注","受注"),("進行中","進行中"),("完了","完了"),("失注","失注")]):
            cols[i].metric(f"{STATUS_COLORS.get(key,'')} {label}", status_counts.get(key, 0))

        st.write(f"**{len(projects)} 件**")

        for pj in projects:
            p = pj["properties"]
            name    = get_text(p, "案件名")
            status  = get_text(p, "ステータス")
            kind    = get_text(p, "種別")
            amount  = p.get("受注金額", {}).get("number")
            deadline = get_text(p, "納期")
            drive_url = get_text(p, "Google Driveリンク")
            icon    = STATUS_COLORS.get(status, "⚪")

            amount_str = f"¥{amount:,.0f}" if amount else "未設定"

            with st.expander(f"{icon} {name}　`{status}`　{amount_str}"):
                col1, col2 = st.columns(2)
                with col1:
                    new_name   = st.text_input("案件名", value=name, key=f"pn_{pj['id']}")
                    new_kind   = st.selectbox("種別", ["映像制作","展示会・イベント","クリエイティブ制作","TikTok・SNS運用"],
                        index=["映像制作","展示会・イベント","クリエイティブ制作","TikTok・SNS運用"].index(kind) if kind in ["映像制作","展示会・イベント","クリエイティブ制作","TikTok・SNS運用"] else 0,
                        key=f"pk_{pj['id']}")
                    new_status = st.selectbox("ステータス", ["商談中","受注","進行中","完了","失注"],
                        index=["商談中","受注","進行中","完了","失注"].index(status) if status in ["商談中","受注","進行中","完了","失注"] else 0,
                        key=f"ps_{pj['id']}")
                with col2:
                    new_amount   = st.number_input("受注金額（円）", value=float(amount) if amount else 0.0, step=1000.0, key=f"pa_{pj['id']}")
                    new_deadline = st.text_input("納期（例: 2026-06-30）", value=deadline, key=f"pd_{pj['id']}")
                    new_drive    = st.text_input("Google DriveリンクURL", value=drive_url, key=f"pdr_{pj['id']}")

                col_btn1, col_btn2 = st.columns([1, 4])
                with col_btn1:
                    if st.button("💾 保存", key=f"pv_{pj['id']}"):
                        props = {
                            "案件名":  {"title": [{"text": {"content": new_name}}]},
                            "種別":    {"select": {"name": new_kind}},
                            "ステータス": {"select": {"name": new_status}},
                            "受注金額": {"number": new_amount if new_amount > 0 else None},
                        }
                        if new_deadline: props["納期"] = {"date": {"start": new_deadline}}
                        if new_drive:    props["Google Driveリンク"] = {"url": new_drive}
                        update_page(pj["id"], props)
                        st.success("保存しました")
                        st.rerun()
                with col_btn2:
                    if new_drive:
                        st.link_button("📁 Google Driveを開く", new_drive)

                tasks = get_tasks_by_project(pj["id"])
                if tasks:
                    st.markdown("**タスク**")
                    for t in tasks:
                        t_name   = get_text(t["properties"], "タスク名")
                        t_status = get_text(t["properties"], "ステータス")
                        t_due    = get_text(t["properties"], "期日")
                        t_icon   = STATUS_COLORS.get(t_status, "⚪")
                        due_str  = f"　期日: {t_due}" if t_due else ""
                        st.write(f"　{t_icon} {t_name}　`{t_status}`{due_str}")

    with tab2:
        st.markdown("### 新規案件登録")
        clients = get_clients()
        client_options = {get_text(c["properties"], "会社名"): c["id"] for c in clients}

        col1, col2 = st.columns(2)
        with col1:
            new_name     = st.text_input("案件名 *")
            new_client   = st.selectbox("クライアント", ["未選択"] + list(client_options.keys()))
            new_kind     = st.selectbox("種別", ["映像制作","展示会・イベント","クリエイティブ制作","TikTok・SNS運用"])
            new_status   = st.selectbox("ステータス", ["商談中","受注","進行中","完了","失注"])
        with col2:
            new_amount   = st.number_input("受注金額（円）", min_value=0.0, step=1000.0)
            new_deadline = st.text_input("納期（例: 2026-06-30）")
            new_drive    = st.text_input("Google DriveリンクURL")

        if st.button("➕ 登録する", type="primary"):
            if not new_name:
                st.error("案件名は必須です")
            else:
                props = {
                    "案件名":     {"title": [{"text": {"content": new_name}}]},
                    "種別":       {"select": {"name": new_kind}},
                    "ステータス": {"select": {"name": new_status}},
                }
                if new_client != "未選択":
                    props["クライアント"] = {"relation": [{"id": client_options[new_client]}]}
                if new_amount > 0:
                    props["受注金額"] = {"number": new_amount}
                if new_deadline:
                    props["納期"] = {"date": {"start": new_deadline}}
                if new_drive:
                    props["Google Driveリンク"] = {"url": new_drive}
                create_page(PROJECT_DB_ID, props)
                st.success(f"「{new_name}」を登録しました")
                st.rerun()

# ========== 人事管理 ==========
elif page == "🔒 人事管理":
    st.subheader("🔒 人事管理")

    if "hr_authenticated" not in st.session_state:
        st.session_state.hr_authenticated = False

    if not st.session_state.hr_authenticated:
        st.warning("このページはアクセス制限されています")
        pw = st.text_input("パスワードを入力", type="password")
        if st.button("ログイン"):
            if pw == HR_PASSWORD:
                st.session_state.hr_authenticated = True
                st.rerun()
            else:
                st.error("パスワードが違います")
    else:
        if st.sidebar.button("🔓 ログアウト"):
            st.session_state.hr_authenticated = False
            st.rerun()

        tab1, tab2, tab3, tab4 = st.tabs(["👤 従業員一覧", "🕐 勤怠管理", "💴 給与管理", "➕ 新規登録"])

        with tab1:
            employees = query_db(EMPLOYEE_DB_ID, sorts=[{"property": "氏名", "direction": "ascending"}])
            st.write(f"**{len(employees)} 名**")

            for emp in employees:
                p = emp["properties"]
                name     = get_text(p, "氏名")
                role     = get_text(p, "役職")
                hire     = get_text(p, "雇用形態")
                salary   = p.get("基本給", {}).get("number")
                hourly   = p.get("時給", {}).get("number")
                commute  = p.get("交通費", {}).get("number")
                bank     = get_text(p, "振込口座")
                email    = get_text(p, "メール")
                phone    = get_text(p, "電話番号")
                notes    = get_text(p, "備考")

                pay_str = f"基本給 ¥{salary:,.0f}" if salary else (f"時給 ¥{hourly:,.0f}" if hourly else "未設定")

                with st.expander(f"👤 {name}　`{role}`　{pay_str}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_name    = st.text_input("氏名",     value=name,  key=f"en_{emp['id']}")
                        new_role    = st.selectbox("役職", ["代表","社員","パート","業務委託"],
                            index=["代表","社員","パート","業務委託"].index(role) if role in ["代表","社員","パート","業務委託"] else 1,
                            key=f"er_{emp['id']}")
                        new_hire    = st.selectbox("雇用形態", ["正社員","パート","業務委託"],
                            index=["正社員","パート","業務委託"].index(hire) if hire in ["正社員","パート","業務委託"] else 0,
                            key=f"eh_{emp['id']}")
                        new_salary  = st.number_input("基本給（月額）", value=float(salary) if salary else 0.0, step=1000.0, key=f"es_{emp['id']}")
                        new_hourly  = st.number_input("時給", value=float(hourly) if hourly else 0.0, step=10.0, key=f"ew_{emp['id']}")
                    with col2:
                        new_commute = st.number_input("交通費（月額）", value=float(commute) if commute else 0.0, step=100.0, key=f"ec_{emp['id']}")
                        new_bank    = st.text_input("振込口座", value=bank,  key=f"eb_{emp['id']}")
                        new_email   = st.text_input("メール",   value=email, key=f"ee_{emp['id']}")
                        new_phone   = st.text_input("電話番号", value=phone, key=f"ep_{emp['id']}")
                        new_notes   = st.text_input("備考",     value=notes, key=f"eno_{emp['id']}")

                    if st.button("💾 保存", key=f"esv_{emp['id']}"):
                        update_page(emp["id"], {
                            "氏名":     {"title": [{"text": {"content": new_name}}]},
                            "役職":     {"select": {"name": new_role}},
                            "雇用形態": {"select": {"name": new_hire}},
                            "基本給":   {"number": new_salary if new_salary > 0 else None},
                            "時給":     {"number": new_hourly if new_hourly > 0 else None},
                            "交通費":   {"number": new_commute if new_commute > 0 else None},
                            "振込口座": {"rich_text": [{"text": {"content": new_bank}}]},
                            "メール":   {"email": new_email or None},
                            "電話番号": {"phone_number": new_phone or None},
                            "備考":     {"rich_text": [{"text": {"content": new_notes}}]},
                        })
                        st.success("保存しました")
                        st.rerun()

        with tab2:
            st.markdown("### 勤怠入力")
            employees = query_db(EMPLOYEE_DB_ID, sorts=[{"property": "氏名", "direction": "ascending"}])
            emp_options = {get_text(e["properties"], "氏名"): e["id"] for e in employees}

            col1, col2 = st.columns(2)
            with col1:
                at_emp = st.selectbox("従業員", list(emp_options.keys()), key="at_emp")
                at_month = st.text_input("対象年月（例: 2026-05-01）", key="at_month")
            with col2:
                at_days   = st.number_input("出勤日数", min_value=0, max_value=31, step=1, key="at_days")
                at_hours  = st.number_input("労働時間", min_value=0.0, step=0.5, key="at_hours")
                at_over   = st.number_input("残業時間", min_value=0.0, step=0.5, key="at_over")
                at_paid   = st.number_input("有給取得日数", min_value=0, step=1, key="at_paid")
                at_note   = st.text_input("備考", key="at_note")

            if st.button("💾 勤怠を登録", type="primary", key="at_save"):
                if not at_emp or not at_month:
                    st.error("従業員と対象年月は必須です")
                else:
                    title = f"{at_emp}_{at_month[:7]}"
                    props = {
                        "タイトル": {"title": [{"text": {"content": title}}]},
                        "従業員":   {"relation": [{"id": emp_options[at_emp]}]},
                        "対象年月": {"date": {"start": at_month}},
                        "出勤日数": {"number": at_days},
                        "労働時間": {"number": at_hours},
                        "残業時間": {"number": at_over},
                        "有給取得日数": {"number": at_paid},
                    }
                    if at_note: props["備考"] = {"rich_text": [{"text": {"content": at_note}}]}
                    create_page(ATTENDANCE_DB_ID, props)
                    st.success(f"「{title}」の勤怠を登録しました")

            st.divider()
            st.markdown("### 勤怠一覧")
            records = query_db(ATTENDANCE_DB_ID, sorts=[{"property": "対象年月", "direction": "descending"}])
            if records:
                for r in records:
                    p = r["properties"]
                    title  = get_text(p, "タイトル")
                    days   = p.get("出勤日数", {}).get("number", 0)
                    hours  = p.get("労働時間", {}).get("number", 0)
                    over   = p.get("残業時間", {}).get("number", 0)
                    st.write(f"📅 **{title}**　出勤: {days}日　労働: {hours}h　残業: {over}h")
            else:
                st.info("勤怠データがありません")

        with tab3:
            st.markdown("### 給与計算")
            employees = query_db(EMPLOYEE_DB_ID, sorts=[{"property": "氏名", "direction": "ascending"}])
            emp_map = {get_text(e["properties"], "氏名"): e for e in employees}

            col1, col2 = st.columns(2)
            with col1:
                pay_emp   = st.selectbox("従業員", list(emp_map.keys()), key="pay_emp")
                pay_month = st.text_input("対象年月（例: 2026-05-01）", key="pay_month")

            # 従業員の基本情報から自動取得
            selected_emp = emp_map.get(pay_emp, {})
            ep = selected_emp.get("properties", {})
            base_salary = ep.get("基本給", {}).get("number") or 0
            hourly_rate = ep.get("時給", {}).get("number") or 0
            default_commute = ep.get("交通費", {}).get("number") or 0

            # 勤怠から自動取得
            attendance_records = query_db(ATTENDANCE_DB_ID, filters={
                "and": [
                    {"property": "従業員", "relation": {"contains": selected_emp.get("id", "")}},
                ]
            }) if selected_emp else []
            matched_att = next((r for r in attendance_records
                if get_text(r["properties"], "タイトル").endswith(pay_month[:7] if pay_month else "")), None)

            att_hours = matched_att["properties"].get("労働時間", {}).get("number", 0) if matched_att else 0
            att_over  = matched_att["properties"].get("残業時間", {}).get("number", 0) if matched_att else 0

            # 給与計算
            if hourly_rate > 0:
                auto_base = hourly_rate * att_hours
            else:
                auto_base = base_salary

            overtime_pay = int(hourly_rate * att_over * 1.25) if hourly_rate > 0 else int(base_salary / 160 * att_over * 1.25)

            with col2:
                pay_base    = st.number_input("基本給", value=float(auto_base), step=1000.0, key="pay_base")
                pay_over    = st.number_input("残業代", value=float(overtime_pay), step=100.0, key="pay_over")
                pay_commute = st.number_input("交通費", value=float(default_commute), step=100.0, key="pay_commute")
                pay_allow   = st.number_input("各種手当", min_value=0.0, step=1000.0, key="pay_allow")
                pay_ins     = st.number_input("社会保険控除", min_value=0.0, step=100.0, key="pay_ins")
                pay_tax     = st.number_input("所得税控除", min_value=0.0, step=100.0, key="pay_tax")

            gross = pay_base + pay_over + pay_commute + pay_allow
            net   = gross - pay_ins - pay_tax

            st.markdown(f"""
            | | 金額 |
            |--|--|
            | 支給総額 | **¥{gross:,.0f}** |
            | 控除合計 | ¥{pay_ins + pay_tax:,.0f} |
            | **振込金額** | **¥{net:,.0f}** |
            """)

            pay_date   = st.text_input("振込日（例: 2026-05-25）", key="pay_date")

            if st.button("💾 給与を登録", type="primary", key="pay_save"):
                if not pay_emp or not pay_month:
                    st.error("従業員と対象年月は必須です")
                else:
                    title = f"{pay_emp}_{pay_month[:7]}"
                    props = {
                        "タイトル":     {"title": [{"text": {"content": title}}]},
                        "従業員":       {"relation": [{"id": selected_emp["id"]}]},
                        "対象年月":     {"date": {"start": pay_month}},
                        "基本給":       {"number": pay_base},
                        "残業代":       {"number": pay_over},
                        "交通費":       {"number": pay_commute},
                        "各種手当":     {"number": pay_allow},
                        "社会保険控除": {"number": pay_ins},
                        "所得税控除":   {"number": pay_tax},
                        "支給総額":     {"number": gross},
                        "振込金額":     {"number": net},
                        "振込状況":     {"select": {"name": "未振込"}},
                    }
                    if pay_date: props["振込日"] = {"date": {"start": pay_date}}
                    if matched_att: props["勤怠"] = {"relation": [{"id": matched_att["id"]}]}
                    create_page(PAYROLL_DB_ID, props)
                    st.success(f"「{title}」の給与を登録しました")

            st.divider()
            st.markdown("### 給与一覧")
            payrolls = query_db(PAYROLL_DB_ID, sorts=[{"property": "対象年月", "direction": "descending"}])
            if payrolls:
                for r in payrolls:
                    p = r["properties"]
                    title   = get_text(p, "タイトル")
                    net_amt = p.get("振込金額", {}).get("number", 0)
                    status  = get_text(p, "振込状況")
                    icon    = "🟢" if status == "振込済" else "⚪"
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.write(f"{icon} **{title}**　振込: ¥{net_amt:,.0f}　`{status}`")
                    with col_b:
                        if status == "未振込":
                            if st.button("振込済にする", key=f"paid_{r['id']}"):
                                update_page(r["id"], {"振込状況": {"select": {"name": "振込済"}}})
                                st.rerun()
            else:
                st.info("給与データがありません")

        with tab4:
            st.markdown("### 新規従業員登録")
            col1, col2 = st.columns(2)
            with col1:
                nn_name    = st.text_input("氏名 *")
                nn_role    = st.selectbox("役職", ["代表","社員","パート","業務委託"])
                nn_hire    = st.selectbox("雇用形態", ["正社員","パート","業務委託"])
                nn_salary  = st.number_input("基本給（月額）", min_value=0.0, step=1000.0)
                nn_hourly  = st.number_input("時給", min_value=0.0, step=10.0)
            with col2:
                nn_commute = st.number_input("交通費（月額）", min_value=0.0, step=100.0)
                nn_bank    = st.text_input("振込口座")
                nn_email   = st.text_input("メール")
                nn_phone   = st.text_input("電話番号")
                nn_notes   = st.text_input("備考")

            if st.button("➕ 登録する", type="primary", key="emp_add"):
                if not nn_name:
                    st.error("氏名は必須です")
                else:
                    props = {
                        "氏名":     {"title": [{"text": {"content": nn_name}}]},
                        "役職":     {"select": {"name": nn_role}},
                        "雇用形態": {"select": {"name": nn_hire}},
                    }
                    if nn_salary > 0:  props["基本給"]   = {"number": nn_salary}
                    if nn_hourly > 0:  props["時給"]     = {"number": nn_hourly}
                    if nn_commute > 0: props["交通費"]   = {"number": nn_commute}
                    if nn_bank:        props["振込口座"] = {"rich_text": [{"text": {"content": nn_bank}}]}
                    if nn_email:       props["メール"]   = {"email": nn_email}
                    if nn_phone:       props["電話番号"] = {"phone_number": nn_phone}
                    if nn_notes:       props["備考"]     = {"rich_text": [{"text": {"content": nn_notes}}]}
                    create_page(EMPLOYEE_DB_ID, props)
                    st.success(f"「{nn_name}」を登録しました")
                    st.rerun()

# ========== 給与明細（従業員ポータル） ==========
elif page == "👤 給与明細":
    st.subheader("👤 給与明細確認")

    if "emp_logged_in" not in st.session_state:
        st.session_state.emp_logged_in = False
        st.session_state.emp_id = None
        st.session_state.emp_name = ""

    if not st.session_state.emp_logged_in:
        st.info("氏名とパスワードを入力してください")
        login_name = st.text_input("氏名")
        login_pw   = st.text_input("パスワード", type="password")

        if st.button("ログイン", type="primary"):
            employees = query_db(EMPLOYEE_DB_ID)
            matched = None
            for e in employees:
                name = get_text(e["properties"], "氏名")
                pw   = get_text(e["properties"], "ログインパスワード")
                if name == login_name and pw == login_pw and pw != "":
                    matched = e
                    break
            if matched:
                st.session_state.emp_logged_in = True
                st.session_state.emp_id = matched["id"]
                st.session_state.emp_name = login_name
                st.rerun()
            else:
                st.error("氏名またはパスワードが正しくありません")
    else:
        st.success(f"ようこそ、{st.session_state.emp_name} さん")
        if st.button("ログアウト"):
            st.session_state.emp_logged_in = False
            st.session_state.emp_id = None
            st.session_state.emp_name = ""
            st.rerun()

        payrolls = query_db(PAYROLL_DB_ID,
            filters={"property": "従業員", "relation": {"contains": st.session_state.emp_id}},
            sorts=[{"property": "対象年月", "direction": "descending"}]
        )

        if not payrolls:
            st.info("給与明細がまだありません")
        else:
            for r in payrolls:
                p = r["properties"]
                month   = get_text(p, "対象年月")[:7] if get_text(p, "対象年月") else "不明"
                base    = p.get("基本給", {}).get("number", 0) or 0
                over    = p.get("残業代", {}).get("number", 0) or 0
                commute = p.get("交通費", {}).get("number", 0) or 0
                allow   = p.get("各種手当", {}).get("number", 0) or 0
                ins     = p.get("社会保険控除", {}).get("number", 0) or 0
                tax     = p.get("所得税控除", {}).get("number", 0) or 0
                gross   = p.get("支給総額", {}).get("number", 0) or 0
                net     = p.get("振込金額", {}).get("number", 0) or 0
                status  = get_text(p, "振込状況")
                pay_date = get_text(p, "振込日")
                icon    = "🟢" if status == "振込済" else "🟡"

                with st.expander(f"{icon} {month} の給与明細　振込: ¥{net:,.0f}　`{status}`"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**支給**")
                        st.write(f"基本給　¥{base:,.0f}")
                        st.write(f"残業代　¥{over:,.0f}")
                        st.write(f"交通費　¥{commute:,.0f}")
                        st.write(f"各種手当　¥{allow:,.0f}")
                        st.markdown(f"**支給総額　¥{gross:,.0f}**")
                    with col2:
                        st.markdown("**控除**")
                        st.write(f"社会保険　¥{ins:,.0f}")
                        st.write(f"所得税　¥{tax:,.0f}")
                        st.markdown(f"**控除合計　¥{ins+tax:,.0f}**")
                        st.divider()
                        st.markdown(f"### 振込金額　¥{net:,.0f}")
                        if pay_date:
                            st.write(f"振込日: {pay_date}")
