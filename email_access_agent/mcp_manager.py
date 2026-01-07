"""
MCP (Model Context Protocol) Tool Integration
Handles access provisioning through MCP tool calling
"""

from typing import Dict, Optional, Any
import logging
import json

logger = logging.getLogger(__name__)


class MCPAccessManager:
    """
    Manages access provisioning through MCP tool calls
    """
    
    def __init__(self, mcp_client=None):
        """
        Initialize MCP access manager
        
        Args:
            mcp_client: MCP client instance for tool calling
        """
        self.mcp_client = mcp_client
        self.provisioning_history = []
    
    def provision_access(self, access_request, approval_data: Dict) -> Dict[str, Any]:
        """
        Provision access using MCP tool calling
        
        Args:
            access_request: AccessRequest object with details
            approval_data: Approval information (approver, comments, etc.)
            
        Returns:
            Dictionary with provisioning results
        """
        try:
            # Determine which MCP tool to call based on resource
            tool_name = self._select_tool(access_request.resource)
            
            # Prepare tool arguments
            tool_args = self._prepare_tool_args(access_request, approval_data)
            
            # Execute the MCP tool call
            result = self._execute_mcp_tool(tool_name, tool_args)
            
            # Record provisioning
            self.provisioning_history.append({
                "access_request": access_request.dict(),
                "approval_data": approval_data,
                "tool_name": tool_name,
                "result": result,
                "status": "success" if result.get("success") else "failed"
            })
            
            logger.info(f"Successfully provisioned {access_request.access_type} access to {access_request.resource} for {access_request.requester}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error provisioning access: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to provision access: {e}"
            }
    
    def _select_tool(self, resource: str) -> str:
        """
        Select the appropriate MCP tool based on the resource
        
        Args:
            resource: Resource name from access request
            
        Returns:
            MCP tool name to use
        """
        # Map resources to MCP tools
        # This is a simplified example - in production, you'd have a more sophisticated mapping
        resource_lower = resource.lower()
        
        if "database" in resource_lower or "db" in resource_lower:
            return "grant_database_access"
        elif "aws" in resource_lower or "s3" in resource_lower or "ec2" in resource_lower:
            return "grant_aws_access"
        elif "github" in resource_lower or "repo" in resource_lower:
            return "grant_github_access"
        elif "jira" in resource_lower:
            return "grant_jira_access"
        elif "slack" in resource_lower:
            return "grant_slack_access"
        else:
            return "grant_generic_access"
    
    def _prepare_tool_args(self, access_request, approval_data: Dict) -> Dict:
        """
        Prepare arguments for the MCP tool call
        
        Args:
            access_request: AccessRequest object
            approval_data: Approval information
            
        Returns:
            Dictionary of tool arguments
        """
        return {
            "user_id": access_request.user_id,
            "requester": access_request.requester,
            "resource": access_request.resource,
            "access_type": access_request.access_type,
            "specific_permissions": access_request.specific_permissions,
            "justification": access_request.justification,
            "approved_by": approval_data.get("approver", "unknown"),
            "approval_comments": approval_data.get("comments", ""),
            "urgency": access_request.urgency
        }
    
    def _execute_mcp_tool(self, tool_name: str, tool_args: Dict) -> Dict:
        """
        Execute an MCP tool call
        
        Args:
            tool_name: Name of the MCP tool to call
            tool_args: Arguments for the tool
            
        Returns:
            Result from the MCP tool
        """
        if self.mcp_client:
            # If we have an actual MCP client, use it
            try:
                result = self.mcp_client.call_tool(tool_name, tool_args)
                return result
            except Exception as e:
                logger.error(f"MCP tool call failed: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }
        else:
            # Simulation mode for testing/demo
            logger.info(f"[SIMULATION] MCP Tool Call: {tool_name}")
            logger.info(f"[SIMULATION] Arguments: {json.dumps(tool_args, indent=2)}")
            
            return {
                "success": True,
                "tool_name": tool_name,
                "arguments": tool_args,
                "message": f"Successfully provisioned {tool_args['access_type']} access to {tool_args['resource']} for user {tool_args['user_id']}",
                "simulation": True,
                "access_details": {
                    "user_id": tool_args["user_id"],
                    "requester": tool_args["requester"],
                    "resource": tool_args["resource"],
                    "permissions": [tool_args["access_type"]],
                    "specific_permissions": tool_args["specific_permissions"],
                    "granted_by": tool_args["approved_by"]
                }
            }
    
    def get_provisioning_history(self) -> list:
        """Get history of all provisioning operations"""
        return self.provisioning_history.copy()
    
    def revoke_access(self, access_details: Dict) -> Dict:
        """
        Revoke previously granted access
        
        Args:
            access_details: Details of access to revoke
            
        Returns:
            Result of revocation
        """
        try:
            tool_name = f"revoke_{self._select_tool(access_details['resource'])}"
            
            if self.mcp_client:
                result = self.mcp_client.call_tool(tool_name, access_details)
                return result
            else:
                logger.info(f"[SIMULATION] Revoking access: {json.dumps(access_details, indent=2)}")
                return {
                    "success": True,
                    "message": "Access revoked successfully (simulation)",
                    "simulation": True
                }
                
        except Exception as e:
            logger.error(f"Error revoking access: {e}")
            return {
                "success": False,
                "error": str(e)
            }
