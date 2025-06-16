import sqlite3
from datetime import datetime, timedelta
import random
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import math

class CandidateAnalyzer:
    def __init__(self, db_name='candidate_analysis.db'):
        self.db_name = db_name
        self._initialize_db()
        if self.is_database_empty():
            self.generate_fake_data(50)

    def is_database_empty(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM candidates')
            return cursor.fetchone()[0] == 0

    def _initialize_db(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
                    job_role TEXT,
                    status TEXT CHECK(status IN ('Selected', 'Rejected', 'Declined by Candidate', 'Declined by Panel')),
                    company TEXT,
                    interview_date DATE
                )
            ''')
            conn.commit()

    def add_candidate(self, name, gender, job_role, status, company, interview_date):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO candidates (name, gender, job_role, status, company, interview_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, gender, job_role, status, company, interview_date))
            conn.commit()

    def generate_fake_data(self, num_candidates=50):
        first_names = ['John', 'Jane', 'Alex', 'Sarah', 'Mike', 'Emily', 'David', 'Lisa',
                      'Robert', 'Maria', 'James', 'Jennifer', 'Michael', 'Linda']
        last_names = ['Doe', 'Smith', 'Johnson', 'Williams', 'Brown', 'Davis', 'Miller', 'Wilson']
        companies = ['Cred', 'Amazon', 'Google', 'Navi', 'Quince', 'Rupeek', 'Salesforce', 'Adobe', 'Zee', 'Thoughtspot']
        job_roles = ['SDE III', 'SDET I', 'EM']
        genders = ['Male', 'Female']
        start_date = datetime(2025, 4, 1)
        for _ in range(num_candidates):
            gender = random.choice(genders)
            first_name = random.choice(first_names[:6] if gender == 'Male' else first_names[6:])
            name = f"{first_name} {random.choice(last_names)}"
            job_role = random.choice(job_roles)
            status = random.choices(
                ['Selected', 'Rejected', 'Declined by Candidate', 'Declined by Panel'],
                weights=[0.3, 0.4, 0.2, 0.1]
            )[0]
            company = random.choice(companies)
            interview_date = (start_date + timedelta(days=random.randint(0, 18))).strftime('%Y-%m-%d')
            self.add_candidate(name, gender, job_role, status, company, interview_date)

    def get_client_data(self, company=None):
        with sqlite3.connect(self.db_name) as conn:
            query = '''
                SELECT 
                    company,
                    job_role,
                    gender,
                    COUNT(CASE WHEN status = 'Selected' THEN 1 END) as selected,
                    COUNT(CASE WHEN status = 'Rejected' THEN 1 END) as rejected,
                    COUNT(CASE WHEN status = 'Declined by Candidate' THEN 1 END) as declined_by_candidate,
                    COUNT(CASE WHEN status = 'Declined by Panel' THEN 1 END) as declined_by_panel,
                    COUNT(*) as total
                FROM candidates
            '''
            if company:
                query += f" WHERE company = '{company}'"
            query += '''
                GROUP BY company, job_role, gender
                ORDER BY company, job_role, gender
            '''
            return pd.read_sql(query, conn)

    def get_role_summary(self):
        with sqlite3.connect(self.db_name) as conn:
            return pd.read_sql('''
                SELECT 
                    job_role,
                    gender,
                    COUNT(CASE WHEN status = 'Selected' THEN 1 END) as selected,
                    COUNT(*) as total,
                    ROUND(COUNT(CASE WHEN status = 'Selected' THEN 1 END) * 100.0 / COUNT(*), 1) as selection_rate
                FROM candidates
                GROUP BY job_role, gender
                ORDER BY job_role, gender
            ''', conn)

    def get_company_metrics(self, company=None):
        with sqlite3.connect(self.db_name) as conn:
            query = '''
                SELECT 
                    company,
                    COUNT(*) as total_candidates,
                    COUNT(CASE WHEN status = 'Selected' THEN 1 END) as selected_count,
                    COUNT(CASE WHEN status = 'Rejected' THEN 1 END) as rejected_count,
                    COUNT(CASE WHEN status = 'Declined by Candidate' THEN 1 END) as declined_by_candidate,
                    COUNT(CASE WHEN status = 'Declined by Panel' THEN 1 END) as declined_by_panel,
                    ROUND(COUNT(CASE WHEN status = 'Selected' THEN 1 END) * 100.0 / COUNT(*), 1) as selection_rate,
                    ROUND(COUNT(CASE WHEN status = 'Rejected' THEN 1 END) * 100.0 / COUNT(*), 1) as rejection_rate,
                    COUNT(CASE WHEN gender = 'Male' THEN 1 END) as male_count,
                    COUNT(CASE WHEN gender = 'Female' THEN 1 END) as female_count,
                    COUNT(CASE WHEN gender = 'Male' AND status = 'Selected' THEN 1 END) as selected_male,
                    COUNT(CASE WHEN gender = 'Female' AND status = 'Selected' THEN 1 END) as selected_female,
                    CASE 
                        WHEN COUNT(CASE WHEN status = 'Selected' THEN 1 END) > 0 
                        THEN CEIL(COUNT(*) * 1.0 / COUNT(CASE WHEN status = 'Selected' THEN 1 END))
                        ELSE 0
                    END as selection_ratio,
                    CASE 
                        WHEN COUNT(CASE WHEN gender = 'Female' AND status = 'Selected' THEN 1 END) > 0 
                        THEN CEIL(COUNT(CASE WHEN gender = 'Male' AND status = 'Selected' THEN 1 END) * 1.0 / 
                                  COUNT(CASE WHEN gender = 'Female' AND status = 'Selected' THEN 1 END))
                        ELSE 0
                    END as selection_diversity_ratio,
                    CASE 
                        WHEN COUNT(CASE WHEN gender = 'Female' THEN 1 END) > 0 
                        THEN CEIL(COUNT(CASE WHEN gender = 'Male' THEN 1 END) * 1.0 / 
                                  COUNT(CASE WHEN gender = 'Female' THEN 1 END))
                        ELSE 0
                    END as diversity_ratio
                FROM candidates
            '''
            if company:
                query += f" WHERE company = '{company}'"
            query += '''
                GROUP BY company
                ORDER BY company
            '''
            return pd.read_sql(query, conn)


def calculate_gender_ratio(male_count, female_count):
    """Calculate Male:Female ratio."""
    if female_count == 0:
        return "N/A"
    return f"{math.ceil(male_count / female_count)}:1"


def display_ratio_details(total_candidates, selected_candidates, male_count, female_count, selected_male, selected_female):
    """Display ratio details in a structured format."""
    selection_ratio = math.ceil(total_candidates / selected_candidates) if selected_candidates > 0 else "N/A"
    selection_diversity_ratio = math.ceil(selected_male / selected_female) if selected_female > 0 else "N/A"
    gender_ratio = calculate_gender_ratio(male_count, female_count)




def main():
    st.set_page_config(page_title="Client Candidate Analysis", layout="wide")
    analyzer = CandidateAnalyzer()
    st.title("👔 Client Candidate Analysis Dashboard")
    st.markdown("View role-wise and gender-wise selection metrics for your candidates")

    # Sidebar for client filter
    with st.sidebar:
        st.header("Client Filter")
        company_data = analyzer.get_client_data()
        selected_company = st.selectbox(
            "Select Client Company",
            options=['All Clients'] + sorted(company_data['company'].unique().tolist()))
        if st.button("Generate Sample Data (50 candidates)"):
            analyzer.generate_fake_data()
            st.success("Generated 50 sample candidate records!")

    # Fetch data based on selection
    if selected_company == 'All Clients':
        client_data = analyzer.get_client_data()
        company_metrics = analyzer.get_company_metrics()

        # Aggregate metrics across all clients
        total_candidates = company_metrics['total_candidates'].sum()
        total_selected = company_metrics['selected_count'].sum()
        total_rejected = company_metrics['rejected_count'].sum()
        total_male = company_metrics['male_count'].sum()
        total_female = company_metrics['female_count'].sum()
        selected_male = company_metrics['selected_male'].sum()
        selected_female = company_metrics['selected_female'].sum()

        overall_selection_rate = (total_selected / total_candidates * 100) if total_candidates > 0 else 0
        overall_rejection_rate = (total_rejected / total_candidates * 100) if total_candidates > 0 else 0
    else:
        client_data = analyzer.get_client_data(selected_company)
        company_metrics = analyzer.get_company_metrics(selected_company)

        if not company_metrics.empty:
            row = company_metrics.iloc[0]
            total_candidates = row['total_candidates']
            total_selected = row['selected_count']
            total_rejected = row['rejected_count']
            total_male = row['male_count']
            total_female = row['female_count']
            selected_male = row['selected_male']
            selected_female = row['selected_female']

            overall_selection_rate = row['selection_rate']
            overall_rejection_rate = row['rejection_rate']

    # Display ratio details
    display_ratio_details(total_candidates, total_selected, total_male, total_female, selected_male, selected_female)

    # Role-wise summary section
    st.subheader("Role-wise Selection Summary")
    role_summary = analyzer.get_role_summary()
    if not role_summary.empty:
        pivot_table = role_summary.pivot_table(
            index='job_role',
            columns='gender',
            values=['selected', 'selection_rate'],
            aggfunc='first'
        )
        st.dataframe(pivot_table.style.format("{:.1f}%", subset=pd.IndexSlice[:, 'selection_rate']))

    # Overall Metrics Section (only shown when "All Clients" is selected)
    if selected_company == 'All Clients':
        st.subheader("Overall Metrics Across All Clients")
        cols = st.columns(4)
        cols[0].metric("Total Candidates", total_candidates)
        cols[1].metric("Selected", f"{total_selected} ({overall_selection_rate:.1f}%)")
        cols[2].metric("Rejected", f"{total_rejected} ({overall_rejection_rate:.1f}%)")

        gender_cols = st.columns(2)
        gender_cols[0].metric("Male Candidates", f"{(total_male / total_candidates * 100):.1f}%" if total_candidates > 0 else "N/A")
        gender_cols[1].metric("Female Candidates", f"{(total_female / total_candidates * 100):.1f}%" if total_candidates > 0 else "N/A")

    # Client-specific data section
    st.subheader(f"Client-wise Analysis: {selected_company if selected_company != 'All Clients' else 'All Clients'}")
    if not client_data.empty:
        # Selection Metrics
        sel_col1, sel_col2 = st.columns(2)
        with sel_col1:
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            selection_by_role = client_data.groupby('job_role')['selected'].sum().reset_index()
            selection_by_role.plot(
                x='job_role',
                y='selected',
                kind='bar',
                ax=ax1,
                color='green',
                title=f"Selected Candidates by Role ({selected_company})"
            )
            plt.xticks(rotation=45)
            st.pyplot(fig1)

        with sel_col2:
            fig2, ax2 = plt.subplots(figsize=(8, 6))
            selection_by_gender = client_data.groupby('gender')['selected'].sum().reset_index()
            selection_by_gender.plot(
                x='gender',
                y='selected',
                kind='bar',
                ax=ax2,
                color=['blue', 'pink'],
                title=f"Selected Candidates by Gender ({selected_company})"
            )
            st.pyplot(fig2)

        # Rejection Metrics
        rej_col1, rej_col2 = st.columns(2)
        with rej_col1:
            fig3, ax3 = plt.subplots(figsize=(10, 6))
            rejection_by_role = client_data.groupby('job_role')['rejected'].sum().reset_index()
            rejection_by_role.plot(
                x='job_role',
                y='rejected',
                kind='bar',
                ax=ax3,
                color='red',
                title=f"Rejected Candidates by Role ({selected_company})"
            )
            plt.xticks(rotation=45)
            st.pyplot(fig3)

        with rej_col2:
            fig4, ax4 = plt.subplots(figsize=(8, 6))
            rejection_by_gender = client_data.groupby('gender')['rejected'].sum().reset_index()
            rejection_by_gender.plot(
                x='gender',
                y='rejected',
                kind='bar',
                ax=ax4,
                color=['blue', 'pink'],
                title=f"Rejected Candidates by Gender ({selected_company})"
            )
            st.pyplot(fig4)

        # Distribution Overview (Pie Charts)
        pie_col1, pie_col2 = st.columns(2)
        with pie_col1:
            if selected_company == 'All Clients':
                status_data = company_metrics[['selected_count', 'rejected_count',
                                               'declined_by_candidate', 'declined_by_panel']].sum()
            else:
                status_data = company_metrics.iloc[0][['selected_count', 'rejected_count',
                                                       'declined_by_candidate', 'declined_by_panel']]
            fig5, ax5 = plt.subplots()
            labels = ['Selected', 'Rejected', 'Declined by Candidate', 'Declined by Panel']
            sizes = status_data.values
            ax5.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                   colors=['green', 'red', 'orange', 'yellow'])
            ax5.set_title('Candidate Status Distribution')
            st.pyplot(fig5)

        with pie_col2:
            if selected_company == 'All Clients':
                male_perc = (company_metrics['male_count'].sum() / company_metrics['total_candidates'].sum()) * 100
                female_perc = (company_metrics['female_count'].sum() / company_metrics['total_candidates'].sum()) * 100
            else:
                male_perc = (company_metrics.iloc[0]['male_count'] / company_metrics.iloc[0]['total_candidates']) * 100
                female_perc = (company_metrics.iloc[0]['female_count'] / company_metrics.iloc[0]['total_candidates']) * 100
            fig6, ax6 = plt.subplots()
            labels = ['Male', 'Female']
            sizes = [male_perc, female_perc]
            ax6.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                   colors=['lightblue', 'lightpink'])
            ax6.set_title('Gender Distribution')
            st.pyplot(fig6)

        # Detailed Metrics
        st.subheader("Detailed Company Metrics")
        if selected_company == 'All Clients':
            for _, row in company_metrics.iterrows():
                with st.expander(f"Metrics for {row['company']}"):
                    cols = st.columns(4)
                    cols[0].metric("Total Candidates", row['total_candidates'])
                    cols[1].metric("Selected", f"{row['selected_count']} ({row['selection_rate']}%)")
                    cols[2].metric("Rejected", f"{row['rejected_count']} ({row['rejection_rate']}%)")

                    gender_cols = st.columns(2)
                    gender_cols[0].metric("Male Candidates", f"{row['male_count']} ({(row['male_count']/row['total_candidates']*100):.1f}%)")
                    gender_cols[1].metric("Female Candidates", f"{row['female_count']} ({(row['female_count']/row['total_candidates']*100):.1f}%)")

                    st.subheader("Ratio Details")
                    ratio_cols = st.columns(3)
                    ratio_cols[0].metric("Selection Ratio", f"1:{int(row['selection_ratio'])}")
                    ratio_cols[1].metric("Selection Diversity Ratio",
                                        f"{int(row['selection_diversity_ratio'])}:1" if row['selection_diversity_ratio'] > 0 else "N/A")
                    ratio_cols[2].metric("Gender Ratio", f"{int(row['diversity_ratio'])}:1")
        else:
            if not company_metrics.empty:
                row = company_metrics.iloc[0]
                cols = st.columns(4)
                cols[0].metric("Total Candidates", row['total_candidates'])
                cols[1].metric("Selected", f"{row['selected_count']} ({row['selection_rate']}%)")
                cols[2].metric("Rejected", f"{row['rejected_count']} ({row['rejection_rate']}%)")

                gender_cols = st.columns(2)
                gender_cols[0].metric("Male Candidates", f"{row['male_count']} ({(row['male_count']/row['total_candidates']*100):.1f}%)")
                gender_cols[1].metric("Female Candidates", f"{row['female_count']} ({(row['female_count']/row['total_candidates']*100):.1f}%)")

                st.subheader("Ratio Details")
                ratio_cols = st.columns(3)
                ratio_cols[0].metric("Selection Ratio", f"1:{int(row['selection_ratio'])}")
                ratio_cols[1].metric("Selection Diversity Ratio",
                                    f"{int(row['selection_diversity_ratio'])}:1" if row['selection_diversity_ratio'] > 0 else "N/A")
                ratio_cols[2].metric("Gender Ratio", f"{int(row['diversity_ratio'])}:1")

        # Raw data table (optional - can be commented out if not needed)
        with st.expander("View Detailed Candidate Data"):
            st.dataframe(client_data.style.format({
                'selected': '{:.0f}',
                'rejected': '{:.0f}',
                'declined_by_candidate': '{:.0f}',
                'declined_by_panel': '{:.0f}',
                'total': '{:.0f}'
            }))
    else:
        st.warning("No data available for the selected client")


if __name__ == "__main__":
    main()
