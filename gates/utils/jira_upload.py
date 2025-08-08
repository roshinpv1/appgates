import requests
import os
from utils.db_integration import fetch_jira_stories
import json
import urllib3

def _extract_report_summary(report_path):
    """
    Extracts a summary from the HTML or JSON report file.
    For HTML, returns a generic message. For JSON, extracts compliance score and gate stats.
    """
    if report_path.endswith('.json'):
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            score = data.get('overall_score') or data.get('summary', {}).get('overall_score')
            total_gates = data.get('summary', {}).get('total_gates') or len(data.get('gates', []))
            passed = data.get('summary', {}).get('passed_gates')
            failed = data.get('summary', {}).get('failed_gates')
            warning = data.get('summary', {}).get('warning_gates')
            summary = f"Hard Gate Assessment Summary:\n"
            if score is not None:
                summary += f"- Compliance Score: {score:.1f}%\n"
            if total_gates is not None:
                summary += f"- Total Gates: {total_gates}\n"
            if passed is not None:
                summary += f"- Gates Met: {passed}\n"
            if warning is not None:
                summary += f"- Partially Met: {warning}\n"
            if failed is not None:
                summary += f"- Not Met: {failed}\n"
            summary += "\nSee attached report for full details."
            return summary
        except Exception as ex:
            return f"Hard Gate Assessment completed. See attached report for details. (Summary extraction failed: {ex})"
    else:
        return "Hard Gate Assessment completed. See attached HTML report for full details."

def upload_report_to_jira(jira_url, jira_user, jira_token, app_id, report_path, report_type, 
                         jira_ticket_id=None, gate_number=None, comment=None):
    """
    Upload report to JIRA stories for the app_id, or to a specific JIRA ticket.
    Returns a dict with results for each story.
    
    Args:
        jira_url: JIRA base URL
        jira_user: JIRA username
        jira_token: JIRA API token
        app_id: Application ID to find related stories
        report_path: Path to the report file
        report_type: Type of report (html, json, pdf)
        jira_ticket_id: Optional specific JIRA ticket ID to upload to
        gate_number: Optional gate number for individual gate upload
        comment: Optional additional comment to add
    """
    import requests
    import json
    import os
    import urllib3
    from .db_integration import fetch_jira_stories
    
    # Configure SSL verification based on environment variable
    ssl_verify = os.getenv("JIRA_SSL_VERIFY", "true").lower() == "true"
    
    # Disable SSL warnings if verification is disabled
    if not ssl_verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        print("⚠️ SSL verification disabled for JIRA requests")
    else:
        print("🔒 SSL verification enabled for JIRA requests")
    
    results = []
    
    # Determine which JIRA tickets to upload to
    if jira_ticket_id:
        # Upload to specific JIRA ticket
        stories = [jira_ticket_id]
        print(f"📋 Uploading to specific JIRA ticket: {jira_ticket_id}")
    else:
        # Upload to all stories for the app_id
        stories = fetch_jira_stories(app_id=app_id)
        print(f"📋 Found {len(stories)} JIRA stories for app_id: {app_id}")
    
    if not stories:
        return {"success": False, "message": f"No JIRA stories found for app_id {app_id}", "results": []}
    
    if not os.path.exists(report_path):
        return {"success": False, "message": f"Report file not found: {report_path}", "results": []}
    
    # Read the report file
    with open(report_path, 'rb') as f:
        report_data = f.read()
    filename = os.path.basename(report_path)
    
    # Generate appropriate summary/comment
    if gate_number and comment:
        summary = f"CodeGates Gate {gate_number} Analysis\n\n{comment}\n\nSee attached report for detailed analysis."
    elif gate_number:
        summary = f"CodeGates Gate {gate_number} Analysis\n\nSee attached report for detailed security gate analysis."
    elif comment:
        summary = f"CodeGates Security Scan Report\n\n{comment}\n\nSee attached report for full details."
    else:
        summary = _extract_report_summary(report_path)
    
    # Process each JIRA story/ticket
    for story in stories:
        story_result = {"story": story}
        try:
            # 1. Add comment
            comment_url = f"{jira_url.rstrip('/')}/rest/api/3/issue/{story}/comment"
            comment_payload = {"body": summary}
            comment_resp = requests.post(
                comment_url,
                auth=(jira_user, jira_token),
                headers={"Content-Type": "application/json"},
                data=json.dumps(comment_payload),
                verify=ssl_verify,
                timeout=30
            )
            if comment_resp.status_code in (200, 201):
                story_result["comment"] = "success"
                print(f"✅ Comment added to JIRA ticket {story}")
            else:
                story_result["comment"] = f"HTTP {comment_resp.status_code}: {comment_resp.text}"
                print(f"❌ Failed to add comment to JIRA ticket {story}: {story_result['comment']}")
            
            # 2. Attach report
            attach_url = f"{jira_url.rstrip('/')}/rest/api/3/issue/{story}/attachments"
            attach_headers = {"X-Atlassian-Token": "no-check"}
            attach_files = {'file': (filename, report_data, 'application/octet-stream')}
            attach_resp = requests.post(
                attach_url,
                headers=attach_headers,
                auth=(jira_user, jira_token),
                files=attach_files,
                verify=ssl_verify,
                timeout=30
            )
            if attach_resp.status_code in (200, 201):
                story_result["attachment"] = "success"
                print(f"✅ Report attached to JIRA ticket {story}")
            else:
                story_result["attachment"] = f"HTTP {attach_resp.status_code}: {attach_resp.text}"
                print(f"❌ Failed to attach report to JIRA ticket {story}: {story_result['attachment']}")
            
            story_result["success"] = story_result["comment"] == "success" and story_result["attachment"] == "success"
            
        except Exception as ex:
            story_result["success"] = False
            story_result["error"] = str(ex)
            print(f"❌ Exception uploading to JIRA ticket {story}: {ex}")
        
        results.append(story_result)
    
    # Determine overall success
    successful_uploads = [r for r in results if r.get("success")]
    overall_success = len(successful_uploads) > 0
    
    return {
        "success": overall_success, 
        "message": f"Uploaded to {len(successful_uploads)}/{len(results)} JIRA tickets",
        "results": results
    } 