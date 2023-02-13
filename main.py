import os 
import pandas as pd
import streamlit as st
from metabase import User
from metabase import Metabase

st.title("Metabase Actvity")

username = st.secrets["username"]
password = st.secrets["password"]

#Get all users
def get_all_users():
    #Log in too metabase.
    metabase = Metabase(
    host= st.secrets["host"],
    user=username,
    password=password,
    )
    
    #Get all users in metabase
    users = User.list(using=metabase)
    return(users)

#Load all Data into streamlit
def load_all_user_data():
    #get users Data
    users = get_all_users()

    #Extract data for all users
    user_id = []
    user_first_name = []
    user_last_name = []
    user_email = []
    user_is_active = []
    user_last_log_in = []
    user_date_joined = []
    user_groups = []

    for metabase_user in range(len(users)):
        user_id.append(users[metabase_user].id)
        user_first_name.append(users[metabase_user].first_name)
        user_last_name.append(users[metabase_user].last_name)
        user_email.append(users[metabase_user].email)
        user_is_active.append(users[metabase_user].is_active)
        user_last_log_in.append(users[metabase_user].last_login)
        user_date_joined.append(users[metabase_user].date_joined)
        user_groups.append(users[metabase_user].group_ids)
    
    #Combine all the data
    all_data = {"user_id":user_id, "first_name":user_first_name, "last_name":user_last_name, "email":user_email,
            "is_active":user_is_active, "last_log_in":user_last_log_in, "date_joined":user_date_joined}

    all_data = pd.DataFrame(all_data)
    return(all_data)

def load_user_groups():
    #get users Data
    users = get_all_users()

    #get users Data
    user_id = []
    user_groups = []
    user_email = []

    for metabase_user in range(len(users)):
        user_id.append(users[metabase_user].id)
        user_groups.append(users[metabase_user].group_ids)
        user_email.append(users[metabase_user].email)

    #Get user groups #### 
    d1 = {"groups":user_groups}
    df2 = pd.DataFrame(d1)
    df2[['grp1','grp2', 'grp3']] = pd.DataFrame(df2.groups.tolist(), index= df2.index)

    #combine data
    user_ids = pd.DataFrame({"id":user_id})
    user_emails = pd.DataFrame({"email":user_email})
    group_data = pd.concat([user_ids,user_emails,df2], axis=1)
    group_data = group_data[['id','email','grp1','grp2','grp3']]

    #Reset data ###
    group_data = group_data.reset_index()
    group_data = pd.melt(group_data, id_vars=['id','email'], value_vars=['grp1', 'grp2', 'grp3'])

    #Final group data
    group_data = group_data[['id','email','value']]
    group_data = group_data[group_data['value'].notna()]

    #Return data
    return(group_data)



#App main logic
#Load all data
all_data = load_all_user_data()
#Load all group data
group_data = load_user_groups()
#Get In active users.
inactive_users = all_data[all_data['last_log_in'].isnull()]

#Define group inactive and active computations
def group_activity(group_id):
    #Get all group members
    grouped_data = group_data[group_data['value'] == group_id]
    count_grouped_data = grouped_data.id.nunique()
    #Get inactive group members
    inactive_grouped_data = grouped_data[grouped_data['id'].isin(inactive_users['user_id'])]
    count_inactive_grouped_data = inactive_grouped_data.id.nunique()
    #Return data
    return([count_grouped_data,count_inactive_grouped_data,grouped_data])

#Create intial metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("All Users Invited:", len(all_data.index))
col1.metric("All Inactive Users:", len(inactive_users.index))
#Group Activity metrics - Duka officers
col2.metric("All DO'S Invited:", group_activity(3)[0])
col2.metric("All Inactive DO'S:", group_activity(3)[1])

#Group Activity metrics - Deputy Duka officers
col3.metric("All DDO'S Invited:", group_activity(4)[0])
col3.metric("All Inactive DDO'S:", group_activity(4)[1])

#Group Activity metrics - Area managers
col4.metric("All AM'S Invited:", group_activity(5)[0])
col4.metric("All Inactive AM'S:", group_activity(5)[1])

#Show Last Week Activity
all_data['last_log_in']= pd.to_datetime(all_data['last_log_in'])
all_data['last_log_in'] = all_data['last_log_in'].dt.date

all_data = all_data[["user_id" , "last_log_in"]]
all_data = all_data.dropna()

from datetime import date, timedelta   
today = date.today()
week_prior =  today - timedelta(weeks=1)

df_last_week = all_data[all_data['last_log_in'] <= week_prior]
df_last_week['last_log_in'] = pd.to_datetime(df_last_week['last_log_in'])
df_last_week['day_week'] = df_last_week['last_log_in'].dt.day_name()
df_last_week = df_last_week.groupby(['day_week']).size().reset_index(name='count_users')
cats = [ 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
df_last_week['day_week'] = pd.Categorical(df_last_week['day_week'], categories=cats, ordered=True)
df_last_week = df_last_week.sort_values('day_week')

import plotly.express as px
fig = px.bar(df_last_week, x='day_week', y='count_users', title="Daily Active Users for the Last week:")
st.plotly_chart(fig, use_container_width=True)


@st.cache
def convert_df_to_csv(df):
  # IMPORTANT: Cache the conversion to prevent computation on every rerun
  return df.to_csv().encode('utf-8')

#Add 4 Download Buttons
col1, col2, col3, col4 = st.columns(4)
col1.download_button(
    label="Download Inactive Users",
    data= convert_df_to_csv(inactive_users[['email']]),
    file_name='inactive_users.csv',
    mime='text/csv',
)

col2.download_button(
    label="Download Inactive DO",
    data= convert_df_to_csv(group_activity(3)[2][['email']]),
    file_name='inactive_DO.csv',
    mime='text/csv',
)

col3.download_button(
    label="Download Inactive DDO",
    data= convert_df_to_csv(group_activity(4)[2][['email']]),
    file_name='inactive_DDO.csv',
    mime='text/csv',
)

col4.download_button(
    label="Download Inactive AM",
    data= convert_df_to_csv(group_activity(5)[2][['email']]),
    file_name='inactive_AM.csv',
    mime='text/csv',
)




