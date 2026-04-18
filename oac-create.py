import os
import logging
import mysql.connector
import argparse
from mysql.connector import Error

# ==========================================
# 1. LOGGING CONFIGURATION
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ==========================================
# 2. MAIN CLASS: STUDY GROUP PROVISIONER
# ==========================================
class StudyGroupProvisioner:
    def __init__(self, db_config, base_storage_path="./belajarbareng_storage"):
        self.db_config = db_config
        self.base_storage_path = base_storage_path

    def execute_query(self, query, params=None, fetch_last_id=False):
        """Helper method to execute queries safely."""
        try:
            conn = mysql.connector.connect(**self.db_config)
            if conn.is_connected():
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                if fetch_last_id:
                    return cursor.lastrowid
                return True
        except Error as e:
            logging.error(f"[DB ERROR] Query execution failed: {e}")
            return None
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    def create_database_schema(self, schema_name):
        """Creates a dedicated database schema for the study group."""
        try:
            # Connect without specifying a database to run CREATE DATABASE
            admin_config = self.db_config.copy()
            if 'database' in admin_config:
                del admin_config['database']
                
            conn = mysql.connector.connect(**admin_config)
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {schema_name};")
            logging.info(f"[PROVISIONING] Database schema '{schema_name}' created successfully.")
            return True
        except Error as e:
            logging.error(f"[DB ERROR] Failed to create schema '{schema_name}': {e}")
            return False
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    def create_storage_folder(self, folder_path):
        """Creates the physical directory for group resources."""
        try:
            os.makedirs(folder_path, exist_ok=True)
            logging.info(f"[PROVISIONING] Storage folder created at '{folder_path}'.")
            return True
        except OSError as e:
            logging.error(f"[OS ERROR] Failed to create folder at '{folder_path}': {e}")
            return False

    def provision_new_group(self, creator_id, name, description):
        """Main workflow to provision a new Wadah Belajar."""
        logging.info(f"--- Starting provisioning for group: '{name}' ---")
        
        # Insert initial record to get the Auto-Increment ID
        insert_query = """
            INSERT INTO study_groups (creator_id, name, description)
            VALUES (%s, %s, %s)
        """
        group_id = self.execute_query(insert_query, (creator_id, name, description), fetch_last_id=True)
        
        if not group_id:
            logging.error("[FAILED] Could not insert group metadata. Aborting.")
            return

        # Define dynamic schema name and storage path based on the ID
        db_schema_name = f"group_{group_id}_db"
        storage_path = os.path.join(self.base_storage_path, f"group_{group_id}")

        # Update the record with the generated infrastructure paths
        update_query = """
            UPDATE study_groups 
            SET storage_path = %s, db_schema_name = %s 
            WHERE id = %s
        """
        self.execute_query(update_query, (storage_path, db_schema_name, group_id))

        # Add creator as an 'admin' member
        member_query = """
            INSERT INTO group_members (group_id, user_id, role)
            VALUES (%s, %s, 'admin')
        """
        self.execute_query(member_query, (group_id, creator_id))

        # Execute Infrastructure Provisioning
        schema_status = self.create_database_schema(db_schema_name)
        folder_status = self.create_storage_folder(storage_path)

        if schema_status and folder_status:
            logging.info(f"[SUCCESS] Wadah Belajar '{name}' (ID: {group_id}) fully provisioned.\n")
        else:
            logging.warning(f"[PARTIAL SUCCESS] Group metadata created for ID: {group_id}, but infrastructure provisioning encountered errors.\n")

# ==========================================
# 3. PRODUCTION EXECUTION BLOCK
# ==========================================
if __name__ == "__main__":
    # Setup argument parser to accept dynamic inputs from the terminal or backend
    parser = argparse.ArgumentParser(description="OaC: Provision a new Wadah Belajar.")
    parser.add_argument("--user_id", type=int, required=True, help="The ID of the user creating the group.")
    parser.add_argument("--name", type=str, required=True, help="The name of the Wadah Belajar.")
    parser.add_argument("--desc", type=str, required=True, help="The description of the Wadah Belajar.")
    
    args = parser.parse_args()

    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'root', # Update if necessary
        'database': 'db_belajar_bareng'
    }

    try:
        # Initialize the provisioner
        provisioner = StudyGroupProvisioner(db_config=db_config)

        # Pass the dynamic arguments directly into the provisioning function
        provisioner.provision_new_group(
            creator_id=args.user_id,
            name=args.name,
            description=args.desc
        )

    except Error as e:
        print(f"\n[EXECUTION FAILED] System Error: {e}")

