# This file is used to connect to the PostgreSQL database and fetch schema details, including tables, columns, data types, and sample data.

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# this class is responsible for connecting to the PostgreSQL database and fetching schema details
class Database:


	# Initialize the Database class with the provided database configuration
	def __init__(self, db_config):
		self.db_config = db_config

		try: 
			self.connection = psycopg2.connect(**db_config) 

		except Exception as e:
			print(f"Error connecting to the database: {e}")
			self.connection = None


	# Fetches the schema details for the given schema name, including tables, columns, data types, and sample data
	def schema_details(self,schema_name):
		
		# this will hold the schema information context that will be returned at the end of the function
		schema_info_context = ""
		cursor = None
		connection = self.connection
		if connection is None:
			return "Error fetching schema details: database connection is unavailable"

		cursor = connection.cursor() # Creating a cursor object to interact with the database

		# adding the schema name to the schema_info_context string
		schema_info_context = f"Database Schema: {schema_name}\n"

		# Fetching Tables
		try: 

			cursor.execute("SELECT table_name from information_schema.tables where table_schema = %s;", (schema_name,))
			tables_list = cursor.fetchall()

			# Adding Tables to the schema_info_context
			for table in tables_list:
				table_name = table[0]
				schema_info_context = f"{schema_info_context}\nTable: {table_name}\n"

				# Adding Columns & Data Types
				cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s;", (table_name,))
				columns_list = cursor.fetchall()

				# Adding Columns and Data Types to the schema_info_context
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

		# Handling any exceptions that occur during the fetching of schema details
		except Exception as e:
			print(f"Error fetching schema details: {e}")
			schema_info_context = f"Error fetching schema details: {e}"

		# Closing the cursor and connection to ensure resources are released
		finally:
			if cursor:
				cursor.close()
			if connection:
				connection.close()
        
		return schema_info_context


	# Executes the provided SQL query and returns the result as a string
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
			if connection:
				connection.close()

# obj is an instance of the Database class, initialized with the provided database configuration
if __name__ == "__main__":
	obj = Database({
		"host": os.getenv("DB_HOST"),
		"port": int(os.getenv("DB_PORT", "5432")),
		"user": os.getenv("DB_USER"),
		"password": os.getenv("DB_PASSWORD"),
		"dbname": os.getenv("DB_NAME")
	})

	result = obj.schema_details("public")

	with open("test_schema_details.txt", "w") as f:
		f.write(result)
