import os
import ollama
from typing import List, Optional
from .schemas import UsedMemory

def get_available_models():
    """List available Ollama chat models (excludes embedding models)"""
    try:
        models = ollama.list()
        chat_models = []
        for model in models.models:
            model_name = getattr(model, 'model', '')
            # Filter out embedding models (common patterns)
            if model_name and not any(keyword in model_name.lower() for keyword in [
                'embed', 'embedding', 'nomic-embed', 'bge-', 'e5-', 
                'sentence-transformers', 'text-embedding'
            ]):
                chat_models.append(model_name)
        return chat_models
    except Exception:
        return []

def generate_response(user_message: str, memory_hits: List[UsedMemory], model: Optional[str] = None) -> str:
    """Generate response using specified Ollama model"""
    if not model:
        # Get first available chat model as default
        available_models = get_available_models()
        if available_models:
            model = available_models[0]
        else:
            model = os.environ.get("OLLAMA_DEFAULT_MODEL", "qwen3:30b")
    
    # Validate model exists
    available_models = get_available_models()
    if model not in available_models:
        raise Exception(f"Model {model} not available. Available: {available_models}")
    
    # Format memory context
    memory_context = ""
    if memory_hits:
        memory_context = "\n".join([f"- {hit.title} (relevance: {hit.score:.2f})" for hit in memory_hits])
    
    prompt = f"""You are a helpful assistant. Use the following memory context if relevant to answer the user's question.

Memory Context:
{memory_context}

User: {user_message}
Assistant:"""
    
    try:
        response = ollama.generate(
            model=str(model),
            prompt=prompt,
            options={"temperature": 0.2, "num_predict": 512}
        )
        return response["response"]
    except Exception as e:
        raise Exception(f"Failed to generate response with model {model}: {str(e)}")
