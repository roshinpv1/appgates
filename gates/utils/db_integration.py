import urllib
import pandas as pd
from sqlalchemy import create_engine, text
import re

def fetch_alerting_integrations_status():
    # TODO: Update with actual connection details
    conn_str = (
        "mssql+pymssql://{user}:{password}@{host}:{port}/{db}"
    ).format(
        user="AD-ENTI\\asasa",
        password=urllib.parse.quote("asasa"),
        host="vistadatamart.qa.xyz.net",
        port=11001,
        db="EFTVista"
    )
    engine = create_engine(conn_str)
    status = {"Splunk": False, "AppDynamics": False, "ThousandEyes": False}
    try:
        with engine.connect() as connection:
            # Example: check for presence of integration tables or config
            for integration in status.keys():
                query = text(f"""SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%{integration.lower()}%'""")
                result = connection.execute(query).scalar()
                status[integration] = result > 0
    except Exception as ex:
        print('Error fetching alerting integration status:', ex)
    return status

def fetch_app_gid_by_app_id(app_id: str):
    # TODO: Update with actual connection details
    conn_str = (
        "mssql+pymssql://{user}:{password}@{host}:{port}/{db}"
    ).format(
        user="AD-ENTI\\asasa",
        password=urllib.parse.quote("asasa"),
        host="vistadatamart.qa.xyz.net",
        port=11001,
        db="EFTVista"
    )
    engine = create_engine(conn_str)
    guids = []
    try:
        with engine.connect() as connection:
            query = text(f"""
                select business_appliation_wf_guid
                from EFTVISTA.VW_DC_ENTRY.DC_ADOPTION_APPLICATION_STATUS_VW
                where app_id = :app_id
            """)
            result = connection.execute(query, {"app_id": app_id})
            guids = [row[0] for row in result]
    except Exception as ex:
        print('Error fetching appGID:', ex)
    return guids

def fetch_jira_stories(app_id: str = None, app_gid: str = None):
    # TODO: Update with actual connection details
    conn_str = (
        "mssql+pymssql://{user}:{password}@{host}:{port}/{db}"
    ).format(
        user="AD-ENTI\\asasa",
        password=urllib.parse.quote("asasa"),
        host="vistadatamart.qa.xyz.net",
        port=11001,
        db="EFTVista"
    )
    engine = create_engine(conn_str)
    stories = []
    try:
        with engine.connect() as connection:
            base_query = "SELECT STORY FROM EFTVISTA.VW_DC_ENTRY.JIRA_GATES_SUMMARY_VM"
            params = {}
            where_clauses = []
            if app_id:
                where_clauses.append("app_id = :app_id")
                params["app_id"] = app_id
            if app_gid:
                where_clauses.append("business_appliation_wf_guid = :app_gid")
                params["app_gid"] = app_gid
            if where_clauses:
                base_query += " WHERE " + " AND ".join(where_clauses)
            query = text(base_query)
            result = connection.execute(query, params)
            stories = [row[0] for row in result]
    except Exception as ex:
        print('Error fetching JIRA stories:', ex)
    return stories

def extract_app_id_from_url(url: str) -> str:
    match = re.search(r'/app-([^/]+)', url)
    if match:
        return match.group(1)
    return None 