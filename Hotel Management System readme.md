Hotel Management System

Executive Summary
This Hotel Management System is a Python-based application backed by a MySQL database, designed to handle all core hotel operations such as room inventory, bookings, availability checks, cancellations, and billing. It ensures consistent state of operation and avoids issues like double-booking by using transactional database operations and constraints. This self-contained system is meant for small to mid-sized hotels, streamlining reservation workflows and automating billing tasks.

Problem Statement

Hotel operations primarily include tracking room availability, managing reservations, generating bills and processing cancellations. A key problem is preventing double booking so that no two guests can hold the same room for the same dates. This system addresses this issues by integrating booking logic with transactional MySQL database, providing automation and improving efficiency in management.


Objective

The objective of this project is to build a reliable hotel management system which :
Maintains an up-to-date inventory of available rooms 
Allows staff to create, view and cancel reservations.
Processes billings and payments for confirmed bookings.
Guarantees no double – booking by enforcing checks at the database level or application level.
Provides a clear codebase that can be run on common platforms.

Features

Managing Rooms : The programs enables the ability to add, update or remove rooms with corresponding details.
Check for Availability : Users can check for available rooms within specified parameters.
Prevention of Double – Booking : This system ensures that two reservations do not overlap in the same room.
Billing : It can calculate or record charges for each reservation in the database, and also flag the charges paid or pending.
Handling Reservations : It allows for creating and cancelling reservations tied to specified rooms and guests.
User Friendly Interface : allowing users to operate the system with minimal prior training.

Technologies Used

Programming Language used : Python 3.x
Database : MySQL 8.x with InnoDB engine for transactions and foreign keys.
Libraries:
mysql-connector-python or PyMySQL for database connectivity
configparser for configuration management (if using config.ini)
pytest for testing
Tools : 
venv for virtual environments
pip for package management
mysql CLI for database setup


Installation / Setup Instructions 

Following are the steps required to install and run the Hotel Management System on the computer.
Download and install Python 3.x on the computer.
During installation on Windows, make sure to enable "Add Python to PATH".
Install MySQL Server on the computer.
Make sure the MySQL server is running before starting the Hotel Management System.
To create the Hotel Database, open MySQL Command Line Client or MySQL Workbench and create the database used by the application:
CREATE DATABASE hotel;
The application is configured to connect to a MySQL database named hotel.
Note: The program automatically creates the required tables when it is started, so the tables do not need to be created manually.
Open Command Prompt/Terminal in the project folder and install the MySQL connector:
pip install mysql-connector-python
This package allows the Python application to communicate with the MySQL database.

The current program contains the MySQL connection details directly in the Python file:
con = a.connect(
host="localhost",
user="root",
passwd="xxx",
database="hotel"
)
Therefore, the MySQL installation must have a user with the appropriate credentials, or these values must be changed in the Python file to match the MySQL account on the computer.
Important: If the MySQL username or password is different, update the connection details before running the application.
Copy/download the project files into a folder on the computer.
For example:
HotelManagementSystem/
└── Iproject1(1).py
Open Command Prompt/Terminal in this folder.
Run the Python program using:
python "Iproject1(1).py"
If the database connection is successful, the program will display:
Connection successful
The required database tables are then created automatically if they do not already exist.
The system is now ready to use.


Guide to Run the Project

Activate the Python virtual environment (venv) as described above.
Ensure MySQL server is running and the hotel_db schema is in place.
Run the application
The application will connect to the database using the provided credentials and begin accepting user input or requests.
Run tests using pytest or unittest to run unit and integration tests.

Project Structure
| Sl. No. | Path | Description |
| 1 | app.py | Consists of the main application script |
| 2 | config.ini | It is the configuration file for DB credentials |
| 3 | requirements.txt | Python dependencies list in pip format |
| 4 | schema.sql | SQL file containing DB schema and sample data |
| 5 | modules/ | It consists Python modules (e.g., db.py, reservation.py, billing.py) |
| 6 | tests/ | Test suite  |
| 7 | README.md | Documentation of the Project  |




Testing

Unit Tests: Write tests for individual components (e.g., room listing, booking logic, billing calculation). Use a testing framework like pytest or unittest
Integration Tests: Test end-to-end scenarios using a test database. For example, attempt to create a reservation through the full stack and verify the database entries.


Manual Tests: Verify key workflows manually:
Try booking a room for given dates. Then try booking the same room and dates again; the second attempt should fail or be rejected, confirming no double-booking.
Use a SQL query to check for overlapping reservations
Check available rooms in a date range
After cancelling a reservation, verify the room becomes available for those dates again.

Limitations

Currently, the system assumes trusted users and requires no login or authorisation. In production, user management and permissions would be needed.
While the system checks for overlapping bookings, simultaneous transactions may still require careful locking. 
Invoice generation and payment processing allow for basic amount tracking. Taxes, discounts, or payment gateway integration are not currently included.
The prototype is designed for one currency only. As such, multi-currency or internationalization is not implemented.
Test coverage may be limited. Comprehensive tests such as UI tests or stress tests are not provided.
Security: Configuration stores DB credentials in plain text. No encryption or secure storage of secrets is implemented.

Future Improvements

Web/Mobile Interface: A web page or mobile app can be developed to make the system more accessible and user friendly.
User Accounts & Roles: Adding authentication with roles such as admin, receptionist or guest, and secure login to protect data and functions.
Advanced Concurrency Controls: Implement database transactions (e.g., row locking, optimistic locks) or queuing to handle simultaneous bookings safely, as suggested by industry practice.
Payment Integration: Integration a payment gateway for real transactions and automated invoice emailing.
Reporting & Analytics: Addition of modules for occupancy reports, revenue analytics, and export (CSV/Excel) of booking data.
Configuration Management: Move sensitive configurations to environment variables or a secrets manager (12-factor apps), rather than flat files.
Internationalization: Support multiple currencies, languages, and regional date/time formats.

