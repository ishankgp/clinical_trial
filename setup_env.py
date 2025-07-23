import os

def main():
    env_path = ".env"
    if os.path.exists(env_path):
        print(f"{env_path} already exists.")
        return
    api_key = input("Enter your OpenAI API key: ")
    with open(env_path, "w") as f:
        f.write(f"OPENAI_API_KEY={api_key}\n")
    print(f"{env_path} created successfully.")

if __name__ == "__main__":
    main() 