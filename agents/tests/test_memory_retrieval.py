import os
import sys

# Get the path to the project root (zenlearn)
current_dir = os.path.dirname(os.path.abspath(__file__))
# current_dir = .../agents/tests
project_root = os.path.dirname(os.path.dirname(current_dir))  # .../zenlearn

sys.path.insert(0, project_root)
agents_path = os.path.join(project_root, "agents")
sys.path.insert(0, agents_path)

print(f"Project Root: {project_root}")
print(f"Agents Path: {agents_path}")
print(f"Sys Path: {sys.path}")

try:
    import config

    print("Successfully imported config package")
except ImportError as e:
    print(f"Failed to import config: {e}")

# Dynamic import for module with hyphen in name (chat-agent)


# Dynamic import for module with hyphen in name (chat-agent)
def import_module_from_path(module_name, file_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# Import memory.py from chat-agent
memory_path = os.path.join(project_root, "agents", "chat-agent", "memory.py")
memory_module = import_module_from_path("chat_agent.memory", memory_path)
get_chat_memory = memory_module.get_chat_memory
from utils.logger import logger


def test_memory():
    print("Initializing Memory...")
    try:
        memory = get_chat_memory()
    except Exception as e:
        print(f"Error initializing memory: {e}")
        return

    # Add a memory first
    print("\nAdding memory: 'I hate A* search because it is confusing.'")
    add_res = memory.add_memory(
        user_id="test_user",
        chat_id="test_chat",
        content=[
            {"role": "user", "content": "I hate A* search because it is confusing."}
        ],
        memory_type="conversation",
    )
    print(f"Add result: {add_res}")

    # query 1: The specific question
    q1 = "What do I hate?"
    print(f"\nSearching for: '{q1}'")
    results1 = memory.get_memories(user_id="test_user", query=q1, n_results=5)
    print("Results 1:", results1)

    # query 2: The vague retry
    q2 = "try again"
    print(f"\nSearching for: '{q2}'")
    results2 = memory.get_memories(user_id="test_user", query=q2, n_results=5)
    print("Results 2:", results2)


if __name__ == "__main__":
    test_memory()
