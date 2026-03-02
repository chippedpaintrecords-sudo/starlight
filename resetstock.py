import sqlite3

def reset_all_stock():
    db_path = r"C:\Users\bs\Desktop\Tools\Starlight\inventory.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print(f"Connecting to {db_path}...")
        
        # This one line updates EVERY row in the table
        cursor.execute("UPDATE inventory SET quantity = 100")
        
        # Get the count to confirm
        count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"\nSUCCESS: All {count} items have been reset to Qty: 100.")
        print("Your inventory is now fully 'Stocked' on paper.")

    except Exception as e:
        print(f"DATABASE ERROR: {e}")

if __name__ == "__main__":
    reset_all_stock()
    input("\nInventory is MINT. Press Enter to close...")