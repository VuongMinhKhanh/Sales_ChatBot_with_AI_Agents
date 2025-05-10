import pkgutil
import importlib

agent_registry = {}

def register_agent(name=None):
    """
    Decorator to register an agent function under `name`.
    If `name` is None, use the function’s own name.
    """
    def decorator(fn):
        agent_name = name or fn.__name__
        agent_registry[agent_name] = fn
        return fn
    return decorator

def load_all_agents():
    """
    Dynamically import every module in chatbot.agents so that
    each @register_agent(...) decorator runs at import time.
    """
    import chatbot.agents as agents_pkg
    for finder, module_name, is_pkg in pkgutil.iter_modules(agents_pkg.__path__):
        importlib.import_module(f"{agents_pkg.__name__}.{module_name}")

# Eagerly load them on import of this module
load_all_agents()
