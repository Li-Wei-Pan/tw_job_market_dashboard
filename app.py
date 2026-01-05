import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3

@st.cache_data
def load_data():
    conn = sqlite3.connect("job.db")
    query = "SELECT * FROM job_listings"

    df = pd.read_sql(sql = query, con = conn)
    conn.close()
    df = df.drop_duplicates(subset= ['title', 'company'])
    df['avg_salary'] = pd.to_numeric(df['avg_salary'], errors='coerce')
    df['avg_salary'] = df['avg_salary'].fillna(0)


    return df
    
    #return pd.read_csv('jobs_data.csv')

df = load_data()

st.title('job analysis dashboard')



st.markdown(f"Exploring {len(df)} job opportunities on 104 Corp data")


# Based on location
st.sidebar.header("Filter Options")
if 'address' in df.columns:
    locations = df['address'].dropna().unique()
    selected_loc = st.sidebar.multiselect(
        "Select Location",
        options = locations,
        default= locations
    )

else:
    selected_loc = []


# Based on salary
valid_salary = df[df['avg_salary'] > 0]['avg_salary']
#print(valid_salary)
if not valid_salary.empty:
    min_salary_data = int(min(valid_salary))
    #print("min salary:", min_salary_data)
    max_salary_data = int(max(valid_salary))
    salary_threshold = st.sidebar.slider(
        "Min Monthly Salary(NTD)",
        min_value = min_salary_data,
        max_value = max_salary_data,
        value = min_salary_data,
        step = 1000
    )
else:
    salary_threshold = 0


# Keyword search
search_kw =  st.sidebar.text_input("Search Job Title (e.g. AI, Data)")
filtered_df = df.copy()

if selected_loc:
    filtered_df = filtered_df[filtered_df['address'].isin(selected_loc)]

if salary_threshold > 0:
    filtered_df = filtered_df[
        (filtered_df['avg_salary']>= salary_threshold)|
        (filtered_df['avg_salary'].isna())
    ]

if search_kw:
    filtered_df = filtered_df[filtered_df['title'].str.contains(search_kw, case = False, na = False)]


if st.checkbox("detailed dashboard"):
    st.dataframe(filtered_df)


# KPI dashboards
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        label = 'Total jobs found',
        value = len(filtered_df),
        delta = f"{len(filtered_df)} items"
    )

with col2:
    if not filtered_df.empty and filtered_df['avg_salary'].mean()>0:
        avg_sal = int(filtered_df['avg_salary'].mean())
        st.metric(
            label = 'Average monthly salary',
            value = f"{avg_sal}",
            delta = 'NTD'
        )

    else:
        st.metric(label = 'Average Salary', value = 'N/A')

with col3:
    if 'skills_tags' in filtered_df.columns:
        top_skills = filtered_df['skills_tags'].astype(str).str.split(", ").explode().value_counts().idxmax()
        st.metric(
            label = 'Top demand skills',
            value = top_skills,
            delta = 'Hot skill'
        )
    else:
        st.metric(label = 'Top demand skill', value = 'N/A')
st.markdown("-----")


st.sidebar.markdown("-----")
st.sidebar.write(f"Result: ** {len(filtered_df)} jobs found")

if not filtered_df.empty:
    st.subheader(f"display {len(filtered_df)} jobs")
    display_cols = ['title', "company", "avg_salary", 'address']
    actual_cols = [c for c in display_cols if c in filtered_df]
    st.dataframe(filtered_df[actual_cols])

    with st.expander('Show full raw data details'):
        st.dataframe(filtered_df)

else:
    st.warning("No jobs found with current filters")


# Graphs
st.subheader("Top 10 skills")
skills_series = filtered_df['skills_tags'].astype(str).str.split(", ").explode()
top_skills = skills_series.value_counts().head()
top_skills = top_skills.drop(["NA", 'nan', "不拘"], errors= "ignore")


st.bar_chart(top_skills)


st.subheader('avg salary distribution')

salary_df =filtered_df[filtered_df['avg_salary']> 0]

st.line_chart(salary_df['avg_salary'])


st.subheader('Deep Dive: Tech Stack Analysis')
st.write("keywords in descriptions")

text = ' '.join(filtered_df['description'].astype(str).tolist())
tech_keywords = {
    "Cloud & DevOps": [
        "AWS", "GCP", "Azure", "Docker", "Kubernetes", "K8s", "CI/CD", "Terraform", "Linux", "Jenkins", "Git",
        "雲端", "虛擬化", "容器", "自動化部署", "微服務"
    ],
    "Big Data": [
        "Spark", "Hadoop", "Kafka", "Airflow", "Flink", "Hive", "Databricks", "ETL",
        "大數據", "海量資料", "資料倉儲", "Data Warehouse", "資料湖", "Data Lake", "爬蟲", "數據分析"
    ],
    "Database": [
        "SQL", "NoSQL", "MongoDB", "PostgreSQL", "MySQL", "Redis", "Elasticsearch", "Oracle", "MSSQL",
        "資料庫", "數據庫", "關聯式", "優化", "Stored Procedure"
    ],
    "AI/ML Frameworks": [
        "PyTorch", "TensorFlow", "Keras", "Scikit-learn", "OpenCV", "LLM", "Transformer", "RAG", "YOLO", "HuggingFace", "LangChain", "Bert",
        "人工智慧", "機器學習", "深度學習", "自然語言", "NLP", "電腦視覺", "影像辨識", "演算法", "模型訓練", "生成式"
    ],
    "Programming & Backend": [
        "Python", "Java", "Scala", "C++", "C#", "Go", "Rust", "JavaScript", "TypeScript", "Kotlin", "Swift",
        "後端", "前端", "全端", "物件導向", "API", "RESTful"
    ]
}

stopwords = {
    "的", "及", "與", "等", "在", "並", "了", "有", "是", "或",
    "工作", "內容", "經驗", "能力", "熟悉", "具備", "相關", 
    "請", "我們", "公司", "團隊", "以上", "開發", "設計",
    "years", "experience", "work", "team", "skills"
}

category_counts = {}

text_parts = []
text_parts.append(" ".join(df['description'].dropna().astype(str).tolist()))
#text_from_desc = " ".join(df['description'].dropna().astype(str).tolist())


# if 'skills_tags' in df.columns:
#     text_parts.append(" ".join(df['skills_tags'].dropna().astype(str).tolist()))

# if 'pcSkills' in df.columns:
#     text_parts.append(" ".join(df['pcSkills'].dropna().astype(str).tolist()))

#all_desc_text = " ".join(text_parts).lower()
all_desc_text = filtered_df.to_string().lower()
st.write(f"scanned{len(all_desc_text)}units")


for category, keywords in tech_keywords.items():
    counts = {}
    for kw in keywords:
        count = all_desc_text.count(kw.lower())
        if count > 0:
            counts[kw] = count
    
    category_counts[category] = counts
tabs = st.tabs(list(tech_keywords.keys()))

for i, (category, counts) in enumerate(category_counts.items()):
    with tabs[i]:
        if counts:
            chart_df = pd.DataFrame(list(counts.items()), columns=["Tech", "Count"])
            chart_df = chart_df.sort_values(by="Count", ascending=False)
        
            st.bar_chart(chart_df.set_index("Tech"))
        else:
            st.info(f"在這個類別中沒有找到相關關鍵字")