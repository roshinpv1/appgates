import urllib
import pandas as pd
from sqlalchemy import create_engine, text
import re
import time

def fetch_alerting_integrations_status(app_id: str):
    print(f"   [DB] Starting fetch_alerting_integrations_status for app_id: {app_id}")
    
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
    
    print(f"   [DB] Connection string created (host: vistadatamart.qa.xyz.net)")
    
    # Add timeout parameters to prevent hanging
    print(f"   [DB] Creating SQLAlchemy engine with timeouts...")
    engine = create_engine(
        conn_str,
        connect_args={
            "timeout": 10,  # 10 second connection timeout
            "login_timeout": 10,  # 10 second login timeout
        },
        pool_timeout=10,  # 10 second pool timeout
        pool_recycle=300,  # Recycle connections after 5 minutes
    )
    
    print(f"   [DB] Engine created, attempting connection...")
    
    status = {"Splunk": False, "AppDynamics": False, "ThousandEyes": False}
    try:
        print(f"   [DB] Opening connection...")
        with engine.connect() as connection:
            print(f"   [DB] Connection opened successfully")
            
            # Actual query for monitoring maturity
            query = text("""
                SELECT TOP 5 TOOL, MATURITY_LEVEL
                FROM EFTVISTA.VW_MONITORINGMATURITY.MATURITY_SUMMARY_VW
                WHERE DISTRIBUTED_APP_ID = :app_id
            """)
            print(f"   [DB] Executing query with app_id: {app_id}")
            result = connection.execute(query, {"app_id": app_id})
            print(f"   [DB] Query executed, fetching results...")
            rows = result.fetchall()
            print(f"   [DB] Fetched {len(rows)} rows")
            
            # Map tool names to status keys
            tool_map = {
                "SPLUNK": "Splunk",
                "APPDYNAMICS": "AppDynamics",
                "THOUSANDEYES": "ThousandEyes"
            }
            positive_levels = {"In Progress", "Fundamental", "Intermediate"}
            for row in rows:
                tool = str(row[0]).strip().upper()
                maturity = str(row[1]).strip().title()
                for key, status_key in tool_map.items():
                    if key in tool and maturity in positive_levels:
                        status[status_key] = True
                        print(f"   [DB] Found integration: {status_key}")
            
            print(f"   [DB] Processing completed, final status: {status}")
            
    except Exception as ex:
        print(f'   [DB] Error fetching alerting integration status: {ex}')
    finally:
        # Ensure engine is disposed to free resources
        print(f"   [DB] Disposing engine...")
        engine.dispose()
        print(f"   [DB] Engine disposed")
    
    print(f"   [DB] Returning status: {status}")
    return status

def fetch_appdynamics_integration_status(app_id: str):
    """Fetch AppDynamics integration status from Vista database"""
    print(f"   [DB] Starting fetch_appdynamics_integration_status for app_id: {app_id}")
    
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
    
    print(f"   [DB] Connection string created (host: vistadatamart.qa.xyz.net)")
    
    # Add timeout parameters to prevent hanging
    print(f"   [DB] Creating SQLAlchemy engine with timeouts...")
    engine = create_engine(
        conn_str,
        connect_args={
            "timeout": 10,  # 10 second connection timeout
            "login_timeout": 10,  # 10 second login timeout
        },
        pool_timeout=10,  # 10 second pool timeout
        pool_recycle=300,  # Recycle connections after 5 minutes
    )
    
    print(f"   [DB] Engine created, attempting connection...")
    
    status = {
        "integrated": False,
        "application_found": False,
        "health_rules_configured": False,
        "policies_configured": False,
        "metrics_configured": False,
        "coverage_score": 0.0,
        "details": []
    }
    
    try:
        print(f"   [DB] Opening connection...")
        with engine.connect() as connection:
            print(f"   [DB] Connection opened successfully")
            
            # Query for AppDynamics integration status
            query = text("""
                SELECT TOP 10 TOOL, MATURITY_LEVEL, CONFIGURATION_STATUS, DETAILS
                FROM EFTVISTA.VW_MONITORINGMATURITY.APPDYNAMICS_INTEGRATION_VW
                WHERE DISTRIBUTED_APP_ID = :app_id
                AND TOOL = 'APPDYNAMICS'
            """)
            print(f"   [DB] Executing AppDynamics query with app_id: {app_id}")
            result = connection.execute(query, {"app_id": app_id})
            print(f"   [DB] Query executed, fetching results...")
            rows = result.fetchall()
            print(f"   [DB] Fetched {len(rows)} rows")
            
            # Process results
            positive_levels = {"In Progress", "Fundamental", "Intermediate", "Advanced"}
            configured_items = 0
            
            for row in rows:
                tool = str(row[0]).strip().upper()
                maturity = str(row[1]).strip().title()
                config_status = str(row[2]).strip().title()
                details = str(row[3]).strip() if row[3] else ""
                
                if tool == "APPDYNAMICS" and maturity in positive_levels:
                    status["integrated"] = True
                    status["application_found"] = True
                    status["details"].append(f"AppDynamics integration found with maturity level: {maturity}")
                    
                    # Check specific configurations
                    if "HEALTH_RULES" in details.upper() and config_status in positive_levels:
                        status["health_rules_configured"] = True
                        configured_items += 1
                        status["details"].append("Health rules configured")
                    
                    if "POLICIES" in details.upper() and config_status in positive_levels:
                        status["policies_configured"] = True
                        configured_items += 1
                        status["details"].append("Policies configured")
                    
                    if "METRICS" in details.upper() and config_status in positive_levels:
                        status["metrics_configured"] = True
                        configured_items += 1
                        status["details"].append("Metrics configured")
            
            # Calculate coverage score
            if status["integrated"]:
                status["coverage_score"] = (configured_items / 3.0) * 100.0
            else:
                status["details"].append("AppDynamics integration not found")
            
            print(f"   [DB] Processing completed, final status: {status}")
            
    except Exception as ex:
        print(f'   [DB] Error fetching AppDynamics integration status: {ex}')
        status["details"].append(f"Database error: {str(ex)}")
    finally:
        # Ensure engine is disposed to free resources
        print(f"   [DB] Disposing engine...")
        engine.dispose()
        print(f"   [DB] Engine disposed")
    
    print(f"   [DB] Returning AppDynamics status: {status}")
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
    
    # Add timeout parameters to prevent hanging
    engine = create_engine(
        conn_str,
        connect_args={
            "timeout": 10,  # 10 second connection timeout
            "login_timeout": 10,  # 10 second login timeout
        },
        pool_timeout=10,  # 10 second pool timeout
        pool_recycle=300,  # Recycle connections after 5 minutes
    )
    
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
    finally:
        # Ensure engine is disposed to free resources
        engine.dispose()
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
    
    # Add timeout parameters to prevent hanging
    engine = create_engine(
        conn_str,
        connect_args={
            "timeout": 10,  # 10 second connection timeout
            "login_timeout": 10,  # 10 second login timeout
        },
        pool_timeout=10,  # 10 second pool timeout
        pool_recycle=300,  # Recycle connections after 5 minutes
    )
    
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
    finally:
        # Ensure engine is disposed to free resources
        engine.dispose()
    return stories

def extract_app_id_from_url(url: str) -> str:
    match = re.search(r'/app-([^/]+)', url)
    if match:
        return match.group(1)
    return None 