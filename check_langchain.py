import langchain
import pkgutil

print(f"LangChain path: {langchain.__path__}")

try:
    import langchain.memory
    print("Imported langchain.memory")
    print(dir(langchain.memory))
except ImportError as e:
    print(f"Failed to import langchain.memory: {e}")

try:
    from langchain.chains import ConversationChain
    print("Imported ConversationChain")
except ImportError as e:
    print(f"Failed to import ConversationChain: {e}")
