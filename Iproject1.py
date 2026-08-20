"""
Velvet Hotel Management System
---------------------------------------
Handles: room management, date-based availability, reservations,
cancellations, and billing. Uses transactional row-locking to
prevent double bookings when two staff members book at the same time.
"""

import mysql.connector as a
from datetime import datetime, date

con = a.connect(host="localhost", user="root", passwd="sonabms", database="hotel")
if con.is_connected():
    print("Connection successful")
con.autocommit = True
cr1 = con.cursor()


# ---------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------
def init_db():
    """Create all required tables if they don't already exist."""
    cr1.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            roomno INT PRIMARY KEY,
            room_type VARCHAR(50),
            location VARCHAR(50),
            capacity INT,
            rent DECIMAL(10,2),
            status VARCHAR(20) DEFAULT 'Available'
        )
    """)
    cr1.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            cust_id INT PRIMARY KEY,
            cust_name VARCHAR(100),
            phone VARCHAR(20)
        )
    """)
    cr1.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            reservation_id INT AUTO_INCREMENT PRIMARY KEY,
            room_no INT,
            cust_id INT,
            cust_name VARCHAR(100),
            phone VARCHAR(20),
            meal_type VARCHAR(50),
            checkin_date DATE,
            checkout_date DATE,
            status VARCHAR(20) DEFAULT 'Booked',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_no) REFERENCES rooms(roomno)
        )
    """)
    cr1.execute("""
        CREATE TABLE IF NOT EXISTS billing (
            bill_id INT AUTO_INCREMENT PRIMARY KEY,
            reservation_id INT,
            room_charge DECIMAL(10,2),
            meal_charge DECIMAL(10,2),
            tax DECIMAL(10,2),
            total DECIMAL(10,2),
            payment_status VARCHAR(20) DEFAULT 'Unpaid',
            bill_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id)
        )
    """)
    cr1.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            cuisine VARCHAR(50),
            dish VARCHAR(50),
            type VARCHAR(20),
            price DECIMAL(10,2)
        )
    """)
    con.commit()


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def get_int(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Please enter a valid number.")


def get_float(prompt):
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Please enter a valid number.")


def get_date(prompt):
    """Read a date as YYYY-MM-DD."""
    while True:
        raw = input(prompt + " (YYYY-MM-DD): ")
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            print("Please enter a valid date in YYYY-MM-DD format.")


# ---------------------------------------------------------------------
# Room management
# ---------------------------------------------------------------------
def add_room():
    ch = "y"
    while ch.lower() == "y":
        rno = get_int("Enter room no.: ")
        rtype = input("Enter room type: ")
        location = input("Enter location: ")
        guest = get_int("Enter no. of guests: ")
        rent = get_float("Enter room rent: ")

        try:
            cr1.execute(
                "insert into rooms (roomno, room_type, location, capacity, rent, status) "
                "values (%s, %s, %s, %s, %s, 'Available')",
                (rno, rtype, location, guest, rent)
            )
            con.commit()
            print("Room added.")
        except a.Error as e:
            print("Database error:", e)
            con.rollback()
        ch = input("Enter y to add another room: ")


def view_rooms():
    cr1.execute("select roomno, room_type, location, capacity, rent, status from rooms order by roomno")
    rows = cr1.fetchall()
    if not rows:
        print("No rooms found.")
        return
    print(f"{'Room':<6}{'Type':<12}{'Location':<12}{'Cap':<5}{'Rent':<10}{'Status':<10}")
    for r in rows:
        print(f"{r[0]:<6}{r[1]:<12}{r[2]:<12}{r[3]:<5}{r[4]:<10}{r[5]:<10}")


# ---------------------------------------------------------------------
# Availability (date-range aware)
# ---------------------------------------------------------------------
def check_availability(checkin, checkout, room_type=None):
    """
    Return list of rooms with NO overlapping active reservation
    for the given date range. Two ranges overlap unless one ends
    before the other starts.
    """
    query = """
        SELECT r.roomno, r.room_type, r.location, r.capacity, r.rent
        FROM rooms r
        WHERE r.roomno NOT IN (
            SELECT res.room_no FROM reservations res
            WHERE res.status IN ('Booked', 'CheckedIn')
              AND NOT (res.checkout_date <= %s OR res.checkin_date >= %s)
        )
    """
    params = [checkin, checkout]
    if room_type:
        query += " AND r.room_type = %s"
        params.append(room_type)
    query += " ORDER BY r.roomno"

    cr1.execute(query, tuple(params))
    return cr1.fetchall()


def view_availability():
    checkin = get_date("Enter check-in date")
    checkout = get_date("Enter check-out date")
    if checkout <= checkin:
        print("Check-out date must be after check-in date.")
        return
    rooms = check_availability(checkin, checkout)
    if not rooms:
        print("No rooms available for those dates.")
        return
    print(f"\nAvailable rooms from {checkin} to {checkout}:")
    print(f"{'Room':<6}{'Type':<12}{'Location':<12}{'Cap':<5}{'Rent':<10}")
    for r in rooms:
        print(f"{r[0]:<6}{r[1]:<12}{r[2]:<12}{r[3]:<5}{r[4]:<10}")


# ---------------------------------------------------------------------
# Reservations (double-booking safe)
# ---------------------------------------------------------------------
def make_reservation():
    print("\nNEW RESERVATION")
    cust_id = get_int("Enter customer ID: ")
    cust_name = input("Enter customer name: ")
    phone = input("Enter phone no.: ")
    meal_type = input("Enter meal type: ")
    rno = get_int("Enter room no.: ")
    checkin = get_date("Enter check-in date")
    checkout = get_date("Enter check-out date")

    if checkout <= checkin:
        print("Check-out date must be after check-in date.")
        return

    try:
        # Transaction + row lock: prevents two staff members from
        # booking the same room for overlapping dates at the same time.
        con.start_transaction()

        cr1.execute("SELECT roomno FROM rooms WHERE roomno = %s FOR UPDATE", (rno,))
        if cr1.fetchone() is None:
            print("Room does not exist.")
            con.rollback()
            return

        cr1.execute("""
            SELECT reservation_id FROM reservations
            WHERE room_no = %s
              AND status IN ('Booked', 'CheckedIn')
              AND NOT (checkout_date <= %s OR checkin_date >= %s)
        """, (rno, checkin, checkout))

        if cr1.fetchone() is not None:
            print(f"Room {rno} is already booked for an overlapping date range. Choose another room or dates.")
            con.rollback()
            return

        # Upsert customer record
        cr1.execute(
            "INSERT INTO customers (cust_id, cust_name, phone) VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE cust_name = VALUES(cust_name), phone = VALUES(phone)",
            (cust_id, cust_name, phone)
        )

        cr1.execute("""
            INSERT INTO reservations (room_no, cust_id, cust_name, phone, meal_type,
                                       checkin_date, checkout_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Booked')
        """, (rno, cust_id, cust_name, phone, meal_type, checkin, checkout))

        # If the stay includes today, mark room Occupied for quick-glance status
        if checkin <= date.today() < checkout:
            cr1.execute("UPDATE rooms SET status = 'Occupied' WHERE roomno = %s", (rno,))

        con.commit()
        print(f"Reservation confirmed. Reservation ID: {cr1.lastrowid}")

    except a.Error as e:
        print("Database error:", e)
        con.rollback()


def view_reservations():
    cr1.execute("""
        SELECT reservation_id, room_no, cust_name, phone, checkin_date, checkout_date, status
        FROM reservations ORDER BY checkin_date
    """)
    rows = cr1.fetchall()
    if not rows:
        print("No reservations found.")
        return
    print(f"{'ID':<5}{'Room':<6}{'Name':<15}{'Phone':<15}{'Check-in':<12}{'Check-out':<12}{'Status':<10}")
    for r in rows:
        print(f"{r[0]:<5}{r[1]:<6}{r[2]:<15}{r[3]:<15}{str(r[4]):<12}{str(r[5]):<12}{r[6]:<10}")


# ---------------------------------------------------------------------
# Cancellation
# ---------------------------------------------------------------------
def cancel_reservation():
    res_id = get_int("Enter reservation ID to cancel: ")
    try:
        con.start_transaction()
        cr1.execute("SELECT room_no, status FROM reservations WHERE reservation_id = %s FOR UPDATE", (res_id,))
        row = cr1.fetchone()
        if row is None:
            print("Reservation not found.")
            con.rollback()
            return
        room_no, status = row
        if status == 'Cancelled':
            print("Reservation is already cancelled.")
            con.rollback()
            return
        if status == 'CheckedOut':
            print("Cannot cancel a reservation that has already checked out.")
            con.rollback()
            return

        cr1.execute("UPDATE reservations SET status = 'Cancelled' WHERE reservation_id = %s", (res_id,))

        # If no other active reservation covers today for this room, free it up
        cr1.execute("""
            SELECT reservation_id FROM reservations
            WHERE room_no = %s AND status IN ('Booked','CheckedIn')
              AND checkin_date <= %s AND checkout_date > %s
        """, (room_no, date.today(), date.today()))
        if cr1.fetchone() is None:
            cr1.execute("UPDATE rooms SET status = 'Available' WHERE roomno = %s", (room_no,))

        con.commit()
        print("Reservation cancelled.")
    except a.Error as e:
        print("Database error:", e)
        con.rollback()


# ---------------------------------------------------------------------
# Checkout & Billing
# ---------------------------------------------------------------------
TAX_RATE = 0.12  # 12%


def checkout_and_bill():
    res_id = get_int("Enter reservation ID to check out: ")
    try:
        con.start_transaction()
        cr1.execute("""
            SELECT res.room_no, res.checkin_date, res.checkout_date, res.meal_type,
                   res.status, r.rent
            FROM reservations res JOIN rooms r ON res.room_no = r.roomno
            WHERE res.reservation_id = %s FOR UPDATE
        """, (res_id,))
        row = cr1.fetchone()
        if row is None:
            print("Reservation not found.")
            con.rollback()
            return
        room_no, checkin, checkout, meal_type, status, rent = row
        if status == 'Cancelled':
            print("Cannot bill a cancelled reservation.")
            con.rollback()
            return
        if status == 'CheckedOut':
            print("This reservation has already been checked out and billed.")
            con.rollback()
            return

        nights = (checkout - checkin).days
        room_charge = float(rent) * nights

        # Simple per-night meal charge lookup: average dish price for veg/non-veg not tracked
        # per stay, so charge a flat meal rate based on meal_type keyword, defaulting to 0.
        meal_rate = 0.0
        if meal_type:
            lowered = meal_type.lower()
            if "all" in lowered or "full" in lowered:
                meal_rate = 1200.0
            elif "breakfast" in lowered:
                meal_rate = 400.0
            elif "half" in lowered:
                meal_rate = 800.0
        meal_charge = meal_rate * nights

        subtotal = room_charge + meal_charge
        tax = subtotal * TAX_RATE
        total = subtotal + tax

        cr1.execute("""
            INSERT INTO billing (reservation_id, room_charge, meal_charge, tax, total, payment_status)
            VALUES (%s, %s, %s, %s, %s, 'Unpaid')
        """, (res_id, room_charge, meal_charge, tax, total))

        cr1.execute("UPDATE reservations SET status = 'CheckedOut' WHERE reservation_id = %s", (res_id,))
        cr1.execute("UPDATE rooms SET status = 'Available' WHERE roomno = %s", (room_no,))

        con.commit()

        print("\n----- BILL -----")
        print(f"Reservation ID : {res_id}")
        print(f"Room No        : {room_no}")
        print(f"Nights         : {nights}")
        print(f"Room charge    : {room_charge:.2f}")
        print(f"Meal charge    : {meal_charge:.2f}")
        print(f"Tax ({int(TAX_RATE*100)}%)     : {tax:.2f}")
        print(f"TOTAL          : {total:.2f}")
        print("-----------------\n")

    except a.Error as e:
        print("Database error:", e)
        con.rollback()


def mark_bill_paid():
    bill_id = get_int("Enter bill ID to mark as paid: ")
    try:
        cr1.execute("UPDATE billing SET payment_status = 'Paid' WHERE bill_id = %s", (bill_id,))
        con.commit()
        if cr1.rowcount:
            print("Bill marked as paid.")
        else:
            print("Bill ID not found.")
    except a.Error as e:
        print("Database error:", e)
        con.rollback()


def view_bills():
    cr1.execute("""
        SELECT bill_id, reservation_id, room_charge, meal_charge, tax, total, payment_status, bill_date
        FROM billing ORDER BY bill_date DESC
    """)
    rows = cr1.fetchall()
    if not rows:
        print("No bills found.")
        return
    for r in rows:
        print(f"Bill #{r[0]} | Res #{r[1]} | Room: {r[2]:.2f} Meal: {r[3]:.2f} "
              f"Tax: {r[4]:.2f} Total: {r[5]:.2f} | {r[6]} | {r[7]}")


# ---------------------------------------------------------------------
# Menu management
# ---------------------------------------------------------------------
def menu():
    ch = "y"
    while ch.lower() == "y":
        cusname = input("Enter cuisine name: ")
        dishname = input("Enter dish name: ")
        tp = input("Enter veg or non-veg: ")
        price = get_float("Enter price: ")
        try:
            cr1.execute(
                "insert into menu (cuisine, dish, type, price) values (%s, %s, %s, %s)",
                (cusname, dishname, tp, price)
            )
            con.commit()
        except a.Error as e:
            print("Database error:", e)
            con.rollback()
        ch = input("Enter y to continue: ")


def view_menu():
    cr1.execute("select cuisine, dish, type, price from menu")
    rows = cr1.fetchall()
    if not rows:
        print("Menu is empty.")
        return
    for r in rows:
        print(f"{r[0]:<15}{r[1]:<20}{r[2]:<10}{r[3]:<8}")


# ---------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------
def main():
    init_db()
    print("Welcome to the Velvet Vistara Hotel Management System")
    menu_text = """
 1. Add room
 2. View rooms
 3. Check availability for dates
 4. Make a reservation
 5. View reservations
 6. Cancel a reservation
 7. Check out & generate bill
 8. Mark bill as paid
 9. View bills
10. Add menu item
11. View menu
 0. Exit
"""
    while True:
        print(menu_text)
        choice = get_int("Enter choice: ")
        if choice == 1:
            add_room()
        elif choice == 2:
            view_rooms()
        elif choice == 3:
            view_availability()
        elif choice == 4:
            make_reservation()
        elif choice == 5:
            view_reservations()
        elif choice == 6:
            cancel_reservation()
        elif choice == 7:
            checkout_and_bill()
        elif choice == 8:
            mark_bill_paid()
        elif choice == 9:
            view_bills()
        elif choice == 10:
            menu()
        elif choice == 11:
            view_menu()
        elif choice == 0:
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")

    cr1.close()
    con.close()


if __name__ == "__main__":
    main()
