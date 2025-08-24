"""
Question service for answering questions about repositories using vector embeddings and LLM
"""

import time
from typing import Dict, List, Any, Optional
from services.vector_service import VectorService
from services.embedding_service import EmbeddingService
from services.llm_service import LLMService


class QuestionService:
    """Service for answering questions about repositories using vector embeddings"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize question service"""
        self.config = config
        self.vector_service = VectorService(config.get("vector_store", {}))
        self.embedding_service = EmbeddingService(config.get("embedding", {}))
        self.llm_service = LLMService(config.get("llm", {}))
        
        print(f"❓ QuestionService initialized")
    
    async def ask_question(
        self,
        scan_id: str,
        question: str,
        max_context_chunks: int = 8,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Ask a question about a repository using vector embeddings
        
        Args:
            scan_id: The scan ID of the repository to query
            question: The question to ask
            max_context_chunks: Maximum number of context chunks to retrieve
            include_metadata: Whether to include metadata in the response
            
        Returns:
            Dictionary containing the answer and metadata
        """
        try:
            start_time = time.time()
            
            print(f"❓ Processing question: {question}")
            print(f"📋 Scan ID: {scan_id}")
            
            # Generate embedding for the question
            question_embedding = self.embedding_service.embed_single(question)
            
            if not question_embedding:
                return {
                    "status": "error",
                    "message": "Failed to generate question embedding",
                    "data": None
                }
            
            # Search for relevant context in both main and CD collections
            context_chunks = []
            
            # Search in main repository collection
            main_collection = f"repo_{scan_id}"
            main_results = self._search_collection(
                collection_name=main_collection,
                query_vector=question_embedding,
                limit=max_context_chunks // 2,
                score_threshold=0.3
            )
            context_chunks.extend(main_results)
            
            # Search in CD repository collection if it exists
            cd_collection = f"repo_{scan_id}_cd"
            cd_results = self._search_collection(
                collection_name=cd_collection,
                query_vector=question_embedding,
                limit=max_context_chunks // 2,
                score_threshold=0.3
            )
            context_chunks.extend(cd_results)
            
            # Sort by relevance score and limit
            context_chunks.sort(key=lambda x: x["score"], reverse=True)
            context_chunks = context_chunks[:max_context_chunks]
            
            retrieval_time = (time.time() - start_time) * 1000
            
            if not context_chunks:
                return {
                    "status": "error",
                    "message": "No relevant context found for the question",
                    "data": None,
                    "metadata": {
                        "scan_id": scan_id,
                        "retrieval_time_ms": retrieval_time,
                        "chunks_retrieved": 0
                    }
                }
            
            # Prepare context for LLM
            context_text = self._prepare_context_for_llm(context_chunks)
            
            # Generate answer using LLM
            llm_start_time = time.time()
            
            answer = await self._generate_answer_with_context(question, context_text, scan_id)
            
            llm_time = (time.time() - llm_start_time) * 1000
            total_time = (time.time() - start_time) * 1000
            
            # Prepare response
            response = {
                "status": "success",
                "question": question,
                "answer": answer,
                "scan_id": scan_id,
                "context_used": {
                    "chunks_retrieved": len(context_chunks),
                    "retrieval_time_ms": retrieval_time,
                    "llm_time_ms": llm_time,
                    "total_time_ms": total_time
                }
            }
            
            if include_metadata:
                response["metadata"] = {
                    "scan_id": scan_id,
                    "question_length": len(question),
                    "answer_length": len(answer),
                    "context_chunks": [
                        {
                            "file_path": chunk["payload"].get("file_path", "Unknown"),
                            "score": chunk["score"],
                            "language": chunk["payload"].get("language", "Unknown"),
                            "symbol_name": chunk["payload"].get("symbol_name", "Unknown")
                        }
                        for chunk in context_chunks
                    ]
                }
            
            print(f"✅ Question answered successfully in {total_time:.2f}ms")
            return response
            
        except Exception as e:
            print(f"❌ Failed to answer question: {e}")
            return {
                "status": "error",
                "message": f"Failed to answer question: {str(e)}",
                "data": None
            }
    
    def _search_collection(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Search for relevant context in a collection"""
        try:
            results = self.vector_service.search_similar(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Convert to dictionary format
            chunks = []
            for result in results:
                chunks.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                })
            
            return chunks
            
        except Exception as e:
            print(f"⚠️ Failed to search collection {collection_name}: {e}")
            return []
    
    def _prepare_context_for_llm(self, context_chunks: List[Dict[str, Any]]) -> str:
        """Prepare context chunks for LLM consumption"""
        if not context_chunks:
            return ""
        
        context_parts = []
        
        for i, chunk in enumerate(context_chunks, 1):
            payload = chunk["payload"]
            content = payload.get("content", "")
            file_path = payload.get("file_path", "Unknown")
            language = payload.get("language", "Unknown")
            symbol_name = payload.get("symbol_name", "")
            
            # Format the context chunk
            chunk_text = f"--- Context {i} ---\n"
            chunk_text += f"File: {file_path}\n"
            chunk_text += f"Language: {language}\n"
            if symbol_name:
                chunk_text += f"Symbol: {symbol_name}\n"
            chunk_text += f"Relevance Score: {chunk['score']:.3f}\n"
            chunk_text += f"Content:\n{content}\n"
            
            context_parts.append(chunk_text)
        
        return "\n".join(context_parts)
    
    async def _generate_answer_with_context(
        self,
        question: str,
        context: str,
        scan_id: str
    ) -> str:
        """Generate answer using LLM with context"""
        
        # Create prompt for the LLM
        prompt = f"""You are a helpful code analysis assistant. Answer the following question about a codebase based on the provided context.

Question: {question}

Context from the codebase:
{context}

Please provide a comprehensive answer based on the context provided. If the context doesn't contain enough information to answer the question, say so. Focus on providing accurate, helpful information about the codebase structure, patterns, and implementation details.

Answer:"""
        
        try:
            # Generate response using LLM
            response = await self.llm_service.generate(
                prompt,
                scan_id=scan_id,
                node_name="QuestionService",
                metadata={
                    "question": question,
                    "context_length": len(context),
                    "chunks_used": context.count("--- Context")
                }
            )
            
            return response
            
        except Exception as e:
            print(f"⚠️ LLM generation failed: {e}")
            return f"I apologize, but I encountered an error while generating the answer: {str(e)}"
    
    def get_available_scans(self) -> List[str]:
        """Get list of available scan IDs that can be queried"""
        try:
            if self.vector_service.use_qdrant:
                # Get collections from Qdrant
                collections = self.vector_service.client.get_collections()
                scan_ids = []
                
                for collection in collections.collections:
                    if collection.name.startswith("repo_"):
                        # Extract scan ID from collection name
                        # Format: repo_{scan_id} or repo_{scan_id}_cd
                        parts = collection.name.split("_", 2)
                        if len(parts) >= 2:
                            scan_id = parts[1]
                            if scan_id not in scan_ids:
                                scan_ids.append(scan_id)
                
                return scan_ids
            else:
                # Get collections from in-memory storage
                scan_ids = []
                for collection_name in self.vector_service.collections.keys():
                    if collection_name.startswith("repo_"):
                        parts = collection_name.split("_", 2)
                        if len(parts) >= 2:
                            scan_id = parts[1]
                            if scan_id not in scan_ids:
                                scan_ids.append(scan_id)
                
                return scan_ids
                
        except Exception as e:
            print(f"⚠️ Failed to get available scans: {e}")
            return []
    
    def get_scan_info(self, scan_id: str) -> Dict[str, Any]:
        """Get information about a specific scan"""
        try:
            main_collection = f"repo_{scan_id}"
            cd_collection = f"repo_{scan_id}_cd"
            
            info = {
                "scan_id": scan_id,
                "main_collection": {
                    "exists": False,
                    "points_count": 0
                },
                "cd_collection": {
                    "exists": False,
                    "points_count": 0
                }
            }
            
            # Check main collection
            try:
                if self.vector_service.use_qdrant:
                    main_info = self.vector_service.client.get_collection(main_collection)
                    info["main_collection"]["exists"] = True
                    info["main_collection"]["points_count"] = main_info.points_count
                else:
                    if main_collection in self.vector_service.collections:
                        info["main_collection"]["exists"] = True
                        info["main_collection"]["points_count"] = self.vector_service.collections[main_collection]["count"]
            except:
                pass
            
            # Check CD collection
            try:
                if self.vector_service.use_qdrant:
                    cd_info = self.vector_service.client.get_collection(cd_collection)
                    info["cd_collection"]["exists"] = True
                    info["cd_collection"]["points_count"] = cd_info.points_count
                else:
                    if cd_collection in self.vector_service.collections:
                        info["cd_collection"]["exists"] = True
                        info["cd_collection"]["points_count"] = self.vector_service.collections[cd_collection]["count"]
            except:
                pass
            
            return info
            
        except Exception as e:
            print(f"⚠️ Failed to get scan info: {e}")
            return {"scan_id": scan_id, "error": str(e)}
