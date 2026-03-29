-- Create Database
CREATE DATABASE IF NOT EXISTS blood_donation;
USE blood_donation;

-- Donor Table
CREATE TABLE donor (
    Donor_id VARCHAR(20) PRIMARY KEY,
    Blood_Group VARCHAR(5) NOT NULL,
    Name VARCHAR(50) NOT NULL,
    Age INT NOT NULL,
    Gender VARCHAR(10),
    Phone VARCHAR(15),
    City VARCHAR(50),
    Last_Donation_Date DATE
);

-- Recipient Table
CREATE TABLE recipient (
    Recipient_id VARCHAR(20) PRIMARY KEY,
    Blood_Group VARCHAR(5) NOT NULL,
    Name VARCHAR(50) NOT NULL,
    Age INT NOT NULL,
    Gender VARCHAR(10),
    Phone VARCHAR(15),
    City VARCHAR(50)
);

-- Blood Request Table
CREATE TABLE blood_request (
    Request_id VARCHAR(20) PRIMARY KEY,
    Recipient_id VARCHAR(20),
    Blood_Group VARCHAR(5),
    Request_date DATE,
    City VARCHAR(50),
    Status VARCHAR(20),
    FOREIGN KEY (Recipient_id) REFERENCES recipient(Recipient_id)
);


-- Sample Donor
INSERT INTO donor VALUES
('D001', 'A+', 'Rahul Sharma', 25, 'Male', '9876543210', 'Mumbai', '2025-12-01');

-- Sample Recipient
INSERT INTO recipient VALUES
('R001', 'A+', 'Amit Kumar', 30, 'Male', '9123456789', 'Delhi');

-- Sample Request
INSERT INTO blood_request VALUES
('REQ001', 'R001', 'A+', '2026-03-20', 'Delhi', 'Pending');