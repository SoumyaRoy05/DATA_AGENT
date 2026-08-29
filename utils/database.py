import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Database class to handle database operations
class Database:

    def __init__(self, db_config):
        self.db_config = db_config

        try: 
            self.connection = psycopg2.connect(**db_config) 

        except Exception as e:
            print(f"Error connecting to the database: {e}")
            self.connection = None

    def __del__(self):
        """Destructor to close the connection when the object is destroyed."""
        if self.connection:
            try:
                self.connection.close()
            except Exception as e:
                print(f"Error closing database connection: {e}")

    def schema_details(self,schema_name):

        schema_info_context = ""
        
        connection = self.connection
        if connection is None:
            return "Error: No database connection"
        
        cursor = None
        
        try:
            cursor = connection.cursor()
        except Exception as e:
            print(f"Error creating cursor: {e}")
            return None

        schema_info_context = f"Database Schema: {schema_name}\n"

        try: 

            cursor.execute("SELECT table_name from information_schema.tables where table_schema = %s;", (schema_name,))
            tables_list = cursor.fetchall()

            for table in tables_list:
                table_name = table[0]
                schema_info_context = f"{schema_info_context}\nTable: {table_name}\n"

                # Adding Columns & Data Types
                cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s;", (table_name,))
                columns_list = cursor.fetchall()

                for column in columns_list:
                    column_name = column[0]
                    data_type = column[1]
                    schema_info_context = f"{schema_info_context}  Column: {column_name}, Data Type: {data_type}\n"

                # Adding Sample Data
                cursor.execute(f"SELECT * FROM {schema_name}.{table_name} LIMIT 5;")
                sample_data = cursor.fetchall()
                schema_info_context = f"{schema_info_context}  Sample Data:\n"
                for row in sample_data:
                    schema_info_context = f"{schema_info_context}    {row}\n"

        except Exception as e:
            print(f"Error fetching schema details: {e}")
            schema_info_context = f"Error fetching schema details: {e}"

        finally:
            if cursor:
                cursor.close()
        
        return schema_info_context

    def execute_sql(self, query):
        connection = self.connection
        cursor = None
        if connection is None:
            return None
        
        try:
            cursor = connection.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            connection.commit()
            return str(result)
        except Exception as e:
            print(f"Error executing query: {e}")
            return None
        finally:
            if cursor:
                cursor.close()


if __name__ == "__main__":
    obj = Database({
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD"),
        "dbname": os.getenv("DB_NAME", "data_agent").lower()
    })

    result = obj.schema_details("public")

    if result:
        with open("test_schema_details.txt", "w") as f:
            f.write(result)