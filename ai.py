import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain

# Load environment variables from .env file
load_dotenv()

# Initialize the Anthropic LLM
llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    temperature=0,  # Lower temperature for more accurate SQL
    max_tokens=1000
)

# Connect to SQLite database
db_path = "./database/database.db"
db = SQLDatabase.from_uri(f"sqlite:///{db_path}")

db._sample_rows_in_table_info = 0

# Create SQL database chain - this handles SQL generation and execution automatically
db_chain = SQLDatabaseChain.from_llm(
    llm=llm, 
    db=db, 
    verbose=True,  # Shows the SQL queries being generated
    return_intermediate_steps=True,  # Returns both query and result
    use_query_checker=True,  # Validates SQL before execution
    return_direct=False,  # Returns natural language answer, not just SQL results
    #return_only_outputs=True  # Only return the final answer, not the dictionary
)

def query_database(question):
    """Query the database with a natural language question"""
    try:
        result = db_chain.invoke(question)
        return result
    except Exception as e:
        return f"Error: {e}"

# Example usage
if __name__ == "__main__":
    # First, let's see what's in the database
    #print("=== Database Schema ===")
    #print(db.get_table_info())
    
    # Example queries
    questions = [
        'what city is the oldest user from',
        #"What tables are in this database?",
        #"How many records are in each table?",
        #"Show me all users from New York",
        #"What's the average age of users?",
        #"List all unique cities in the database",
        # Add your specific questions here
    ]
    
    for question in questions:
        print(f"\n=== Question: {question} ===")
        answer = query_database(question)
        #print('the answer follows')
        #print(f"Answer: {answer}")
        print("-" * 50)
    
    # Interactive mode
    print("\n=== Interactive Mode ===")
    while True:
        user_question = input("\nEnter your question (or 'quit' to exit): ")
        if user_question.lower() == 'quit':
            break
        answer = query_database(user_question)
        #print(f"Answer: {answer}")