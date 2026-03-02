import os
import sqlite3
import re
import sys
import io
from pathlib import Path

# FORCES UTF-8 TO HANDLE ASCII ART AND SPECIAL CHARS
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ----------------------------
# DATABASE SETUP
# ----------------------------
conn = sqlite3.connect("inventory.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_number TEXT UNIQUE,
    description TEXT,
    price REAL,
    quantity INTEGER
)
""")
conn.commit()

# ----------------------------
# RETRO SCREEN HELPERS
# ----------------------------
def clear():
    os.system("cls" if os.name == "nt" else "clear")

def green(text):
    return f"\033[92m{text}\033[0m"

def draw_header():
    # The 'r' before the triple quotes is the secret sauce for ASCII art
    logo = r"""
  _________ __               .____    .__       .__     __   
 /   _____//  |______ _______|    |   |__| ____ |  |___/  |_ 
 \_____  \\   __\__  \\_  __ \    |   |  |/ ___\|  |  \   __\
 /        \|  |  / __ \|  | \/    |___|  / /_/  >   Y  \  |  
/_______  /|__| (____  /__|  |_______ \__\___  /|___|  /__|  TM
        \/           \/              \/ /_____/      \/      
    """
    print(green(logo))
    print(green("             INVENTORY & POINT-OF-SALE SYSTEM v0.9"))
    print(green("             -------------------------------------"))

# ----------------------------
# INVENTORY FUNCTIONS
# ----------------------------
def edit_stock():
    clear()
    draw_header()
    print("ADJUST STOCK LEVELS\n")
    sku = input("ENTER SKU TO ADJUST (or 'S' to search): ").strip().upper()

    if sku == "S":
        keyword = input("Search keyword: ").strip()
        cursor.execute("SELECT * FROM inventory WHERE description LIKE ?", (f"%{keyword}%",))
        results = cursor.fetchall()
        if not results:
            print("No matches found."); input("\nPress ENTER..."); return
        for idx, item in enumerate(results, 1):
            print(f"{idx}: {item[1]} - {item[2]} (Current: {item[4]})")
        try:
            sel = int(input("\nSelect number: "))
            selected_item = results[sel-1]
        except:
            print("Invalid selection."); input("\nPress ENTER..."); return
    else:
        cursor.execute("SELECT * FROM inventory WHERE item_number=?", (sku,))
        selected_item = cursor.fetchone()

    if not selected_item:
        print("SKU not found."); input("\nPress ENTER..."); return

    print(f"\nITEM: {selected_item[2]} | STOCK: {selected_item[4]}")
    try:
        adj = int(input("QTY TO ADD (ex: 10) or REMOVE (ex: -5): "))
        new_qty = selected_item[4] + adj
        cursor.execute("UPDATE inventory SET quantity=? WHERE item_number=?", (new_qty, selected_item[1]))
        conn.commit()
        print(green(f"SUCCESS. NEW TOTAL: {new_qty}"))
    except ValueError:
        print("Error: Whole numbers only.")
    input("\nPress ENTER...")

def list_inventory():
    clear()
    draw_header()
    cursor.execute("SELECT * FROM inventory")
    items = cursor.fetchall()
    print(f"{'SKU':<12} {'DESCRIPTION':<30} {'PRICE':<10} {'QTY':<5}")
    print("-" * 60)
    for i in items: 
        print(f"{i[1]:<12} {i[2]:<30} ${i[3]:<9.2f} {i[4]:<5}")
    input("\nPress ENTER...")

# ----------------------------
# ORDER MODE
# ----------------------------
def format_line(sku, desc, qty, price, subtotal, show_prices=True):
    SKU_W, DESC_W, QTY_W, PRI_W, SUB_W = 12, 35, 6, 10, 10
    if len(desc) > DESC_W: desc = desc[:DESC_W-3] + "..."
    p_str = f"{price:.2f}" if show_prices else "0.00"
    s_str = f"{subtotal:.2f}" if show_prices else "0.00"
    return f"{sku:<{SKU_W}}{desc:<{DESC_W}}{qty:>{QTY_W}}{p_str:>{PRI_W}}{s_str:>{SUB_W}}"

def order_mode():
    try:
        clear()
        draw_header()
        acc_name = input("ENTER ACCOUNT NAME: ").strip() or "CASH_SALE"
        folder_name = re.sub(r'[^\w\s-]', '', acc_name).replace(' ', '_').upper()
        Path(folder_name).mkdir(parents=True, exist_ok=True)
        
        po_name = input("ENTER PO NUMBER: ").strip() or "NO_PO"
        po_safe = re.sub(r'[^\w\s-]', '', po_name).replace(' ', '_')
        
        order_items = []
        while True:
            print(f"\nCart: {len(order_items)} items")
            sku_in = input("SKU (S=Search, F=Finish, X=Cancel): ").strip().upper()
            if sku_in == "F": break
            if sku_in == "X": return

            if sku_in == "S":
                kw = input("Search: ").strip()
                cursor.execute("SELECT * FROM inventory WHERE description LIKE ?", (f"%{kw}%",))
                res = cursor.fetchall()
                if not res: print("No matches."); continue
                for i, r in enumerate(res, 1):
                    print(f"{i}: {r[1]} - {r[2]} [Stock: {r[4]}]")
                try:
                    sel = int(input("Select: "))
                    selected = res[sel-1]
                except: continue
            else:
                cursor.execute("SELECT * FROM inventory WHERE item_number=?", (sku_in,))
                selected = cursor.fetchone()
            
            if not selected:
                print("SKU not found."); continue

            try:
                q = int(input(f"QTY ({selected[4]} available): "))
                if q <= 0 or q > selected[4]:
                    print("Invalid qty."); continue
            except: continue

            sub = q * selected[3]
            order_items.append((selected[1], selected[2], q, selected[3], sub))
            cursor.execute("UPDATE inventory SET quantity=? WHERE item_number=?", (selected[4]-q, selected[1]))
            conn.commit()
            print(green(f"Added {selected[2]}"))

        if not order_items: return
        inc_p = input("\nInclude prices? (y/n): ").lower() == 'y'
        total = sum(i[4] for i in order_items)
        
        lines = [
            "REDLON SUPPLY CO.", "172 St John St, Portland, Maine", "(207) 775-6053",
            "-" * 77, f"ACCOUNT: {acc_name}", f"PO NUMBER: {po_name}", "-" * 77,
            f"{'SKU':<12}{'DESCRIPTION':<35}{'QTY':>6}{'PRICE':>10}{'TOTAL':>10}", "-" * 77
        ]
        for i in order_items:
            lines.append(format_line(i[0], i[1], i[2], i[3], i[4], inc_p))
        lines.append("-" * 77)
        lines.append(f"{'TOTAL DUE:':>63} ${total:>10.2f}")
        
        invoice_text = "\n".join(lines)
        clear()
        print(green(invoice_text))

        with open(f"{folder_name}/order_{po_safe}.txt", "w", encoding="utf-8") as f:
            f.write(invoice_text)
            f.flush()
        
        input("\nSUCCESS. Press ENTER to return to menu...")
    except Exception as e:
        print(f"ERROR: {e}"); input("ENTER...")

# ----------------------------
# MAIN MENU
# ----------------------------
def main():
    while True:
        clear()
        draw_header()
        print("""
1 - New Order
2 - Manage Stock (Restock)
3 - View Inventory
4 - Add New SKU
5 - Exit
        """)
        cmd = input("OPTION: ").strip()
        if cmd == "1": order_mode()
        elif cmd == "2": edit_stock()
        elif cmd == "3": list_inventory()
        elif cmd == "4":
            clear(); draw_header()
            num = input("SKU: ").strip().upper()
            des = input("Description: ").strip()
            try:
                prc = float(input("Price: "))
                qty = int(input("Initial Qty: "))
                cursor.execute("INSERT INTO inventory (item_number, description, price, quantity) VALUES (?, ?, ?, ?)", (num, des, prc, qty))
                conn.commit(); print(green("Added!"))
            except Exception as e: print(f"Error: {e}")
            input("\nENTER...")
        elif cmd == "5": break

if __name__ == "__main__":
    main()