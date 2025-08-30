"""
Base classes for the flow system
"""

import asyncio
import warnings
import copy
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class ScanContext:
    """Context shared across all scan nodes"""
    repo_url: str
    branch: str
    git_token: Optional[str] = None
    scan_id: Optional[str] = None
    repo_path: Optional[str] = None
    cd_repo_path: Optional[str] = None
    common_folder: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    vector_data: Optional[Dict[str, Any]] = None
    patterns: Optional[Dict[str, Any]] = None
    expected_implementations: Optional[Dict[str, Any]] = None
    gate_results: Optional[List[Any]] = None
    post_analysis: Optional[Dict[str, Any]] = None
    scan_results: Optional[Dict[str, Any]] = None
    report_data: Optional[Dict[str, Any]] = None


class BaseNode:
    """Base node for the flow system"""
    
    def __init__(self):
        self.params: Dict[str, Any] = {}
        self.successors: Dict[str, 'BaseNode'] = {}
    
    def set_params(self, params: Dict[str, Any]):
        """Set node parameters"""
        self.params = params
    
    def next(self, node: 'BaseNode', action: str = "default") -> 'BaseNode':
        """Set next node in the flow"""
        if action in self.successors:
            warnings.warn(f"Overwriting successor for action '{action}'")
        self.successors[action] = node
        return node
    
    def prep(self, context: ScanContext) -> Any:
        """Prepare node execution"""
        pass
    
    def exec(self, prep_res: Any) -> str:
        """Execute node logic"""
        pass
    
    def post(self, context: ScanContext, prep_res: Any, exec_res: str) -> str:
        """Post-execution processing"""
        pass
    
    def _exec(self, prep_res: Any) -> str:
        """Internal execution method"""
        return self.exec(prep_res)
    
    def _run(self, context: ScanContext) -> str:
        """Internal run method"""
        p = self.prep(context)
        e = self._exec(p)
        return self.post(context, p, e)
    
    def run(self, context: ScanContext) -> str:
        """Run the node"""
        if self.successors:
            warnings.warn("Node won't run successors. Use Flow.")
        return self._run(context)
    
    def __rshift__(self, other: 'BaseNode') -> 'BaseNode':
        """Flow operator"""
        return self.next(other)
    
    def __sub__(self, action: str):
        """Conditional transition operator"""
        if isinstance(action, str):
            return _ConditionalTransition(self, action)
        raise TypeError("Action must be a string")


class _ConditionalTransition:
    """Conditional transition helper"""
    
    def __init__(self, src: BaseNode, action: str):
        self.src = src
        self.action = action
    
    def __rshift__(self, tgt: BaseNode) -> BaseNode:
        return self.src.next(tgt, self.action)


class Node(BaseNode):
    """Standard node with retry logic"""
    
    def __init__(self, max_retries: int = 1, wait: float = 0):
        super().__init__()
        self.max_retries = max_retries
        self.wait = wait
    
    def exec_fallback(self, prep_res: Any, exc: Exception) -> str:
        """Fallback execution on error"""
        raise exc
    
    def _exec(self, prep_res: Any) -> str:
        """Execute with retry logic"""
        for self.cur_retry in range(self.max_retries):
            try:
                return self.exec(prep_res)
            except Exception as e:
                if self.cur_retry == self.max_retries - 1:
                    return self.exec_fallback(prep_res, e)
                if self.wait > 0:
                    time.sleep(self.wait)


class AsyncNode(BaseNode):
    """Async node for asynchronous operations"""
    
    def __init__(self, max_retries: int = 1, wait: float = 0):
        super().__init__()
        self.max_retries = max_retries
        self.wait = wait
        self.context: Optional[ScanContext] = None
    
    async def prep_async(self, context: ScanContext) -> Any:
        """Async preparation"""
        pass
    
    async def exec_async(self, prep_res: Any) -> str:
        """Async execution"""
        pass
    
    async def exec_fallback_async(self, prep_res: Any, exc: Exception) -> str:
        """Async fallback execution"""
        raise exc
    
    async def post_async(self, context: ScanContext, prep_res: Any, exec_res: str) -> str:
        """Async post-processing"""
        pass
    
    async def _exec_async(self, prep_res: Any) -> str:
        """Internal async execution with retry"""
        for i in range(self.max_retries):
            try:
                return await self.exec_async(prep_res)
            except Exception as e:
                if i == self.max_retries - 1:
                    return await self.exec_fallback_async(prep_res, e)
                if self.wait > 0:
                    await asyncio.sleep(self.wait)
    
    async def run_async(self, context: ScanContext) -> str:
        """Run async node"""
        if self.successors:
            warnings.warn("Node won't run successors. Use AsyncFlow.")
        return await self._run_async(context)
    
    async def _run_async(self, context: ScanContext) -> str:
        """Internal async run"""
        p = await self.prep_async(context)
        e = await self._exec_async(p)
        return await self.post_async(context, p, e)
    
    def _run(self, context: ScanContext) -> str:
        """Prevent synchronous execution of async nodes"""
        raise RuntimeError("Use run_async.")


class Flow(BaseNode):
    """Flow orchestrator"""
    
    def __init__(self, start: Optional[BaseNode] = None):
        super().__init__()
        self.start_node = start
    
    def start(self, start: BaseNode) -> BaseNode:
        """Set start node"""
        self.start_node = start
        return start
    
    def get_next_node(self, curr: BaseNode, action: str) -> Optional[BaseNode]:
        """Get next node based on action"""
        # Handle error actions gracefully
        if action == "error":
            # Try to find an error handler, otherwise use default
            nxt = curr.successors.get("error") or curr.successors.get("default")
            if not nxt and curr.successors:
                # If no error handler and no default, use the first available successor
                nxt = list(curr.successors.values())[0]
        else:
            nxt = curr.successors.get(action or "default")
        
        if not nxt and curr.successors:
            warnings.warn(f"Flow ends: '{action}' not found in {list(curr.successors)}")
        return nxt
    
    def _orch(self, context: ScanContext, params: Optional[Dict[str, Any]] = None) -> str:
        """Orchestrate flow execution"""
        curr = copy.copy(self.start_node)
        p = params or {**self.params}
        last_action = None
        
        while curr:
            curr.set_params(p)
            last_action = curr._run(context)
            curr = copy.copy(self.get_next_node(curr, last_action))
        
        return last_action
    
    def _run(self, context: ScanContext) -> str:
        """Run the flow"""
        p = self.prep(context)
        o = self._orch(context)
        return self.post(context, p, o)
    
    def post(self, context: ScanContext, prep_res: Any, exec_res: str) -> str:
        """Post-flow processing"""
        return exec_res


class AsyncFlow(Flow, AsyncNode):
    """Async flow orchestrator"""
    
    async def _orch_async(self, context: ScanContext, params: Optional[Dict[str, Any]] = None) -> str:
        """Async orchestration"""
        curr = copy.copy(self.start_node)
        p = params or {**self.params}
        last_action = None
        
        while curr:
            curr.set_params(p)
            
            # Set context for async nodes
            if isinstance(curr, AsyncNode):
                curr.context = context
            
            try:
                if isinstance(curr, AsyncNode):
                    last_action = await curr._run_async(context)
                else:
                    last_action = curr._run(context)
            except Exception as e:
                print(f"❌ Node execution failed: {e}")
                last_action = "error"
            
            curr = copy.copy(self.get_next_node(curr, last_action))
        
        return last_action
    
    async def _run_async(self, context: ScanContext) -> str:
        """Async flow execution"""
        p = await self.prep_async(context)
        o = await self._orch_async(context)
        return await self.post_async(context, p, o)
    
    async def post_async(self, context: ScanContext, prep_res: Any, exec_res: str) -> str:
        """Async post-flow processing"""
        return exec_res
