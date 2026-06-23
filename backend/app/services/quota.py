from backend.app.core.config import settings
from backend.app.db.session import get_db_user, add_db_quota_spent

def estimate_request_cost(prompt: str, model: str) -> float:
    """
    Estimates the cost of a request based on input prompt size and typical output size.
    """
    price_info = settings.MODEL_PRICING.get(model, {"input": 0.00015, "output": 0.0006})
    
    # Average Portuguese token conversion: ~1.5 tokens per word
    word_count = len(prompt.split())
    estimated_input_tokens = word_count * 1.5
    
    # Average output size estimate for responses
    estimated_output_tokens = 750.0
    
    input_cost = (estimated_input_tokens / 1000.0) * price_info["input"]
    output_cost = (estimated_output_tokens / 1000.0) * price_info["output"]
    
    return input_cost + output_cost

def verify_and_update_quota(user_email: str, estimated_cost: float) -> dict:
    """
    Checks if user is within their quota. Returns decision dict.
    """
    user = get_db_user(user_email)
    if not user:
        return {"allowed": False, "message": "Usuário não encontrado.", "status": "error"}
        
    # 1. Global Budget Check (Fundo de Caixa Global)
    from backend.app.db.session import get_all_db_users, get_db_system_settings
    sys_settings = get_db_system_settings()
    enable_global_budget = sys_settings.get("enable_global_budget", "true").lower() == "true"
    
    if enable_global_budget:
        global_budget = float(sys_settings.get("global_budget", "15.0"))
        
        # Calculate sum of all spent quotas
        all_users = get_all_db_users()
        total_spent = sum(u["quota_spent"] for u in all_users)
        
        if total_spent + estimated_cost > global_budget:
            return {
                "allowed": False,
                "message": f"Bloqueio de Saldo Global: O custo estimado de ${estimated_cost:.4f} excede o caixa total disponível do escritório (${global_budget - total_spent:.4f}). Contate o Sócio.",
                "status": "locked"
            }
        
    limit = user["quota_limit"]
    spent = user["quota_spent"]
    
    # Check if request exceeds limit
    if spent + estimated_cost > limit:
        return {
            "allowed": False, 
            "message": f"Bloqueio de Cota: O custo estimado de ${estimated_cost:.4f} ultrapassa o saldo restante de sua cota (${limit - spent:.4f}).", 
            "status": "locked"
        }
    
    # Check if 80% alert threshold reached
    warning = False
    if (spent + estimated_cost) / limit >= 0.8:
        warning = True
        
    return {
        "allowed": True,
        "warning": warning,
        "message": f"Cota autorizada. Saldo restante: ${limit - spent - estimated_cost:.4f}",
        "status": "ok"
    }

def commit_quota_usage(user_email: str, actual_cost: float) -> None:
    """
    Updates the database with actual spent cost after request completion.
    """
    add_db_quota_spent(user_email, actual_cost)
